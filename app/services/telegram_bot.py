from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
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
                'telegram_id': user.id,
                'username': user.username,
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
        try:
            if len(context.args) != 2:
                await update.message.reply_text(
                    "사용법: /record [거리(km)] [시간(분)]\n예시: /record 5 30"
                )
                return

            distance = float(context.args[0])
            time_minutes = float(context.args[1])

            # Supabase에 기록 저장
            user = update.effective_user
            supabase_client.table('running_records').insert({
                'telegram_id': user.id,
                'distance_km': distance,
                'time_minutes': time_minutes,
                'pace_min_per_km': time_minutes / distance if distance > 0 else 0
            }).execute()

            # AI 피드백 생성
            feedback = await ai_service.analyze_running_record(distance, time_minutes)
            await update.message.reply_text(f"기록이 저장되었습니다!\n\n{feedback}")

        except ValueError:
            await update.message.reply_text("거리와 시간은 숫자로 입력해주세요.")
        except Exception as e:
            await update.message.reply_text(f"기록 저장 중 오류가 발생했습니다: {str(e)}")

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
        """봇 실행"""
        await self.application.initialize()
        await self.application.start()

    async def stop(self):
        """봇 중지"""
        await self.application.stop()
        await self.application.shutdown()

    async def process_update(self, update_data: dict):
        """Webhook으로 받은 업데이트 처리"""
        update = Update.de_json(update_data, self.application.bot)
        await self.application.process_update(update)


# 봇 인스턴스
telegram_bot = TelegramBot()
