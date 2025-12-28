from supabase import create_client, Client
from app.config.settings import get_settings

settings = get_settings()


def get_supabase_client() -> Client:
    """Supabase 클라이언트 연결"""
    supabase: Client = create_client(
        settings.supabase_url,
        settings.supabase_key
    )
    return supabase


# 싱글톤 패턴으로 클라이언트 관리
supabase_client = get_supabase_client()
