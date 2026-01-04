from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.request import HTTPXRequest

from datetime import timedelta
from app.config.settings import get_settings
from app.services.ai_service import ai_service
from app.config.database import supabase_client

settings = get_settings()

class TelegramBot:
    def __init__(self):
        request = HTTPXRequest(
            connection_pool_size=8,
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=30.0  # 연결 풀에서 연결을 기다리는 최대 시간(초)
        )
        self.application = Application.builder().token(settings.telegram_bot_token).request(request).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """핸들러 등록"""
        # 명령어 핸들러
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("record", self.record_command))

        # 메시지 핸들러
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시작 명령어 처리"""
        user = update.effective_user
        welcome_message = f"""
안녕하세요 {user.first_name}님!
러닝 코치 봇입니다.

저는 당신의 러닝을 도와드립니다:
- 러닝 기록 관리
- 개인화된 조언 제공
- 동기부여 메시지

/help 를 입력하면 사용 가능한 명령어를 볼 수 있습니다.
"""
        await update.message.reply_text(welcome_message)

        # 사용자 정보 Supabase에 저장
        try:
            supabase_client.table('users').upsert({
                'id': user.id,
                'username': user.full_name,
            }).execute()
        except Exception as e:
            print(f"사용자 저장 오류: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어 처리"""
        help_text = """
사용 가능한 명령어:

/start - 봇 시작
/help - 도움말 보기
/record - 러닝 기록하기 (예: /record 5.0 00:30:21 - 5km를 30분 21초)

일반 메시지를 보내면 AI 코치와 대화할 수 있습니다!
"""
        await update.message.reply_text(help_text)

    async def record_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """러닝 기록 명령어 처리"""
        if len(context.args) != 2:
            await update.message.reply_text(
                "사용법: /record [거리(km)] [시간(hh:mm:ss)]\n예시: /record 5.0 00:25:47"
            )
            return

        try:
            distance = float(context.args[0])
            duration = self._parse_duration(context.args[1])
            pace_per_km = timedelta(seconds=int((duration / distance).total_seconds()))

            # Supabase에 기록 저장
            user = update.effective_user
            supabase_client.table('workouts').insert({
                'user_id': user.id,
                'distance_km': distance,
                'duration': str(duration),
                'pace_per_km': str(pace_per_km)
            }).execute()

            # AI 피드백 생성
            feedback = await ai_service.analyze_running_record(distance, duration, pace_per_km)
            await update.message.reply_text(f"기록이 저장되었습니다!\n\n{feedback}")

        except ValueError as e:
            await update.message.reply_text(
                "입력 형식이 올바르지 않습니다.\n"
                "거리: 숫자 (예: 5.0)\n"
                "시간: hh:mm:ss 형식 (예: 00:25:47)"
            )
        except Exception as e:
            await update.message.reply_text(f"기록 저장 중 오류가 발생했습니다: {str(e)}")

    def _parse_duration(self, time_str: str) -> timedelta:
        """시간 문자열을 timedelta로 파싱"""
        hours, minutes, seconds = map(int, time_str.split(":"))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일반 메시지 처리"""
        user_message = update.message.text

        # AI 응답 생성
        ai_response = await ai_service.generate_response(user_message)

        # 대화 내용 Supabase에 저장 (선택사항)
        try:
            user = update.effective_user
            supabase_client.table('conversations').insert({
                'telegram_id': user.id,
                'user_message': user_message,
                'bot_response': ai_response
            }).execute()
        except Exception as e:
            print(f"대화 저장 오류: {e}")

        await update.message.reply_text(ai_response)

    async def run(self):
        """봇 실행 (환경에 따라 webhook 또는 polling 모드)"""
        await self.application.initialize()
        await self.application.start()

        if settings.environment == "prod":
            # Webhook 설정 (운영 환경)
            print(f"Setting webhook to: {settings.webhook_url}")
            await self.application.bot.set_webhook(
                url=settings.webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            print("Telegram Bot webhook set successfully!")
        else:
            # Polling 설정 (개발 환경)
            print("Starting polling mode...")
            await self.application.updater.start_polling(allowed_updates=["message", "callback_query"])
            print("Telegram Bot polling started successfully!")

    async def stop(self):
        """봇 중지 (환경에 따라 webhook 또는 polling 정리)"""
        if settings.environment == "prod":
            # Webhook 삭제
            await self.application.bot.delete_webhook()
        else:
            # Polling 중지
            await self.application.updater.stop()

        await self.application.stop()
        await self.application.shutdown()

    async def process_update(self, update_data: dict):
        """Webhook으로 받은 업데이트 처리"""
        update = Update.de_json(update_data, self.application.bot)
        await self.application.process_update(update)

    async def check_webhook_loop(self):
        """1분마다 웹훅 상태를 점검하고 복구하는 루프"""
        import asyncio

        # 개발 환경에서는 루프를 실행하지 않음
        if settings.environment != "prod":
            print("개발 환경이므로 webhook 체크를 건너뜁니다.")
            return

        while True:
            try:
                # 1. 텔레그램에 현재 웹훅 정보 요청
                webhook_info = await self.application.bot.get_webhook_info()

                # 2. URL이 비어있거나 다르면 다시 설정
                if webhook_info.url != settings.webhook_url:
                    print(f"웹훅이 해제됨을 감지! 재등록 중... (현재: '{webhook_info.url}')")
                    await self.application.bot.set_webhook(
                        url=settings.webhook_url,
                        allowed_updates=["message", "callback_query"]
                    )
                    print("웹훅 재등록 완료.")
                else:
                    print("웹훅 연결 상태 정상.")

            except Exception as e:
                print(f"웹훅 점검 중 에러 발생: {e}")

            # 60초 대기
            await asyncio.sleep(60)


# 봇 인스턴스
telegram_bot = TelegramBot()
