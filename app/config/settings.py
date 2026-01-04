from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram Bot
    telegram_bot_token: str
    webhook_url: str = ""

    # Google AI Studio
    gemini_api_key: str
    gemini_model_name: str

    # Supabase
    supabase_url: str
    supabase_key: str

    # App
    app_name: str = "Running Bot"
    debug: bool = True
    environment: str = "dev"  # dev or prod

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
