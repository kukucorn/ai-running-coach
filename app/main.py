from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from app.config.settings import get_settings
from app.services.telegram_bot import telegram_bot

settings = get_settings()

# Webhook 설정
WEBHOOK_HOST = "https://scrawny-rosemary-kukucorn-b44b6d4a.koyeb.app"
WEBHOOK_PATH = f"/webhook/{settings.telegram_bot_token}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작 및 종료 이벤트"""
    # 시작 시
    print("Starting Telegram Bot...")
    await telegram_bot.run()

    # Webhook 설정
    print(f"Setting webhook to: {WEBHOOK_URL}")
    await telegram_bot.application.bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )
    print("Telegram Bot webhook set successfully!")

    yield

    # 종료 시
    print("Stopping Telegram Bot...")
    # Webhook 삭제
    await telegram_bot.application.bot.delete_webhook()
    await telegram_bot.stop()
    print("Telegram Bot stopped.")


app = FastAPI(
    title=settings.app_name,
    description="러닝 코치 텔레그램 봇 백엔드",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "message": "러닝 코치 봇이 실행 중입니다."
    }


@app.get("/health")
async def health():
    """상태 확인"""
    return {"status": "healthy"}


@app.post("/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    """텔레그램 Webhook 엔드포인트"""
    # 토큰 검증 (보안)
    if token != settings.telegram_bot_token:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        update_data = await request.json()
        await telegram_bot.process_update(update_data)
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
