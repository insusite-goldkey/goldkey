FROM python:3.10-slim

# ── 시스템 패키지 + 한국어 locale ──────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    locales-all \
    curl \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# ── 환경변수 ────────────────────────────────────────────────────────────────
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LANGUAGE=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ── HF Space 필수: non-root 유저 설정 (권한 문제 방지) ─────────────────────
RUN useradd -m -u 1000 user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# ── Python 패키지 설치 (레이어 캐시 활용) ──────────────────────────────────
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Playwright + Chromium 빌드타임 설치 (런타임 크래시 완전 방지) ───────────
RUN pip install --no-cache-dir playwright && \
    playwright install --with-deps chromium

# ── 앱 소스 복사 ────────────────────────────────────────────────────────────
COPY --chown=user . .

# ── non-root 유저로 전환 ────────────────────────────────────────────────────
USER user

# ── HF Space 기본 포트 7860 ─────────────────────────────────────────────────
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.maxUploadSize=50", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
