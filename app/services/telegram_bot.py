from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from datetime import timedelta
from app.config.settings import get_settings
from app.services.ai_service import ai_service
from app.config.database import supabase_client

settings = get_settings()


class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(settings.telegram_bot_token).build()
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
/record - 러닝 기록하기 (예: /record 5 30 - 5km를 30분)

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
            pace_per_km = duration / distance

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


# 봇 인스턴스
telegram_bot = TelegramBot()
