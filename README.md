# Running Coach Telegram Bot

FastAPI 백엔드와 텔레그램 봇을 활용한 러닝 코치 애플리케이션입니다.

## 기술 스택

- **Backend**: FastAPI
- **Bot**: python-telegram-bot
- **AI**: Google AI Studio (Gemini)
- **Database**: Supabase
- **Language**: Python 3.10+

## 프로젝트 구조

```
running/
├── app/
│   ├── config/          # 설정 파일
│   │   ├── settings.py  # 환경 변수 관리
│   │   └── database.py  # Supabase 연결
│   ├── services/        # 비즈니스 로직
│   │   ├── telegram_bot.py  # 텔레그램 봇 핸들러
│   │   └── ai_service.py    # Google AI 서비스
│   ├── models/          # 데이터 모델
│   ├── routers/         # API 라우터
│   └── main.py          # FastAPI 앱
├── requirements.txt
├── .env.example
└── README.md
```

## 설치 방법

1. 저장소 클론 및 가상환경 생성

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치

```bash
pip install -r requirements.txt
```

3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 필요한 값을 입력합니다:

```bash
cp .env.example .env
```

필요한 환경 변수:
- `TELEGRAM_BOT_TOKEN`: [@BotFather](https://t.me/botfather)에서 발급
- `GOOGLE_API_KEY`: [Google AI Studio](https://aistudio.google.com/)에서 발급
- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_KEY`: Supabase anon public key

## Supabase 테이블 스키마

### users 테이블
```sql
CREATE TABLE users (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### running_records 테이블
```sql
CREATE TABLE running_records (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  telegram_id BIGINT NOT NULL,
  distance_km DECIMAL(10, 2) NOT NULL,
  time_minutes DECIMAL(10, 2) NOT NULL,
  pace_min_per_km DECIMAL(10, 2),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);
```

### conversations 테이블
```sql
CREATE TABLE conversations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  telegram_id BIGINT NOT NULL,
  user_message TEXT NOT NULL,
  bot_response TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
);
```

## 실행 방법

```bash
python -m app.main
```

또는

```bash
uvicorn app.main:app --reload
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

- `GET /` - 헬스체크
- `GET /health` - 상태 확인

## 텔레그램 봇 명령어

- `/start` - 봇 시작 및 사용자 등록
- `/help` - 도움말 보기
- `/record [거리] [시간]` - 러닝 기록하기 (예: `/record 5 30`)
- 일반 메시지 - AI 코치와 대화

## 주요 기능

1. **러닝 기록 관리**: 거리, 시간, 페이스 자동 계산 및 저장
2. **AI 코칭**: Google Gemini를 활용한 개인화된 조언
3. **대화형 인터페이스**: 텔레그램을 통한 자연스러운 대화
4. **데이터 저장**: Supabase를 통한 안전한 데이터 관리

## 개발 환경

- Python 3.10 이상
- FastAPI 0.115.0
- python-telegram-bot 21.7
- google-generativeai 0.8.3
- supabase 2.9.1

## 라이선스

MIT
