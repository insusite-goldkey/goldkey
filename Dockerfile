FROM python:3.11-slim

# 한국어 locale + 필수 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all \
    curl \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Python 인코딩 환경변수
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LANGUAGE=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1
# Cloud Run 타임아웃 방지: 요청 대기 시간 연장
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# requirements 먼저 복사 (레이어 캐시 활용 — 코드 변경 시 pip 재설치 방지)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# 헬스체크: Cloud Run이 컨테이너 상태를 주기적으로 확인
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

EXPOSE 8080
CMD ["streamlit", "run", "app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.maxUploadSize=50", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
