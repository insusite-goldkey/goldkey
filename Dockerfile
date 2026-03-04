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
# HuggingFace Space app_port=7860 (README.md 기준)
ENV PORT=7860

# ── HF Space 필수: non-root 유저 설정 (권한 문제 방지) ─────────────────────
RUN useradd -m -u 1000 user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# ── Python 패키지 설치 (레이어 캐시 활용) ──────────────────────────────────
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── 앱 소스 복사 ────────────────────────────────────────────────────────────
COPY --chown=user . .

# ── non-root 유저로 전환 ────────────────────────────────────────────────────
USER user

# HuggingFace Space 포트 노출
EXPOSE 7860

# HF Space: PORT=7860 고정
CMD streamlit run app.py \
    --server.port=${PORT:-7860} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.maxUploadSize=50 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
