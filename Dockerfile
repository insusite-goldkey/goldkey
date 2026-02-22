FROM python:3.11-slim

# 한국어 locale 설치 — surrogate 오류 근본 차단
RUN apt-get update && apt-get install -y \
    locales \
    locales-all \
    language-pack-ko \
    && locale-gen ko_KR.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Python 인코딩 환경변수 강제 설정
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LANGUAGE=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["streamlit", "run", "app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
