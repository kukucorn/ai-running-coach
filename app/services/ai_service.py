from google import genai
from app.config.settings import get_settings
import os
from datetime import timedelta

settings = get_settings()

GEMINI_MODEL_NAME = 'gemini-2.5-flash-lite'

# Google AI Studio 설정 - 환경 변수로 API 키 설정
os.environ['GEMINI_API_KEY'] = settings.google_api_key


class AIService:
    def __init__(self):
        # Google Genai Client 초기화
        self.client = genai.Client()

        # 러닝 코칭 봇을 위한 시스템 프롬프트
        self.system_prompt = """
당신은 친절한 러닝 코치입니다.
사용자의 러닝 기록을 관리하고, 동기부여를 하며, 러닝에 대한 조언을 제공합니다.
항상 긍정적이고 격려하는 톤으로 대화하세요.
거리, 시간, 페이스 등의 러닝 데이터를 기록하고 분석할 수 있습니다.
"""

    async def generate_response(self, user_message: str, conversation_history: list = None) -> str:
        """
        사용자 메시지를 받아 AI 응답을 생성합니다.

        Args:
            user_message: 사용자 메시지
            conversation_history: 이전 대화 기록 (선택)

        Returns:
            AI 생성 응답
        """
        try:
            # 프롬프트 구성
            full_prompt = f"{self.system_prompt}\n\n사용자: {user_message}"

            # 대화 기록이 있으면 추가
            if conversation_history:
                history_text = "\n".join([
                    f"{'사용자' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
                    for msg in conversation_history[-5:]  # 최근 5개만 사용
                ])
                full_prompt = f"{self.system_prompt}\n\n이전 대화:\n{history_text}\n\n사용자: {user_message}"

            # AI 응답 생성 (google-genai 1.56.0 API 사용)
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=full_prompt
            )
            return response.text

        except Exception as e:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

    async def analyze_running_record(self, distance: float, duration: timedelta, pace_per_km: timedelta) -> str:
        prompt = f"""
{self.system_prompt}

사용자가 다음과 같은 러닝 기록을 남겼습니다:
- 거리: {distance}km
- 시간: {duration}
- 페이스: {pace_per_km}

이 기록을 분석하고 격려의 메시지와 함께 다음 러닝을 위한 조언을 해주세요.
"""

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"기록 분석 중 오류가 발생했습니다: {str(e)}"


# 싱글톤 인스턴스
ai_service = AIService()
