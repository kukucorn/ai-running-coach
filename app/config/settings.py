from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram Bot
    telegram_bot_token: str

    # Google AI Studio
    google_api_key: str

    # Supabase
    supabase_url: str
    supabase_key: str

    # App
    app_name: str = "Running Bot"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
