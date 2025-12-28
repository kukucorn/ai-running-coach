from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config.settings import get_settings
from app.services.telegram_bot import telegram_bot

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작 및 종료 이벤트"""
    # 시작 시
    print("Starting Telegram Bot...")
    await telegram_bot.run()
    print("Telegram Bot started successfully!")

    yield

    # 종료 시
    print("Stopping Telegram Bot...")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
