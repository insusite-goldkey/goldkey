FROM python:3.10-slim

# ── 1. 시스템 패키지 + 한국어 locale ──────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all \
    curl \
    nginx \
    gettext-base \
    supervisor \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# ── 2. 환경변수 설정 ────────────────────────────────────────────────────────────
ENV LANG=ko_KR.UTF-8 \
    LC_ALL=ko_KR.UTF-8 \
    LANGUAGE=ko_KR.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50 \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_LOGGER_LEVEL=info \
    PORT=8080 \
    HOME=/home/user

# ── 3. 유저 설정 및 PATH (가장 안전한 방식) ───────────────────────────────────
# 유저가 이미 있는지 확인하고 없으면 생성합니다.
RUN id -u user >/dev/null 2>&1 || useradd -m -u 1000 user
ENV PATH="/usr/local/bin:/home/user/.local/bin:${PATH}"

WORKDIR /home/user/app

# ── 4. Python 패키지 설치 ──────────────────────────────────────────────────────
# 패키지 설치는 root 권한으로 수행하여 /usr/local/bin에 실행파일이 생기게 합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── 5. 실행 스크립트/슈퍼바이저 설정 선복사 (경로 누락 방지) ──────────────────
COPY docker/init-hq.sh ./docker/init-hq.sh
COPY docker/supervisord-hq.conf ./supervisord.conf

# ── 6. [중요!] 앱 소스 코드 전체 복사 ──────────────────────────────────────────
# 이 과정이 빠져있어서 실행 파일(init-hq.sh 등)을 찾지 못했던 것입니다.
COPY . .

# ── 7. 권한 설정 및 마무리 ─────────────────────────────────────────────────────
USER root
# 실행 권한 부여 및 소유권 변경
RUN chmod +x /home/user/app/docker/init-hq.sh && \
    chown -R user:user /home/user/app

# 마지막으로 user로 전환
USER user

# Cloud Run은 8080 포트를 수신합니다.
EXPOSE 8080

# 최종 실행 (init-hq.sh가 nginx, streamlit, uvicorn을 모두 깨웁니다)
CMD ["/home/user/app/docker/init-hq.sh"]