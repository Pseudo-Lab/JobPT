# syntax=docker/dockerfile:1.4
# Python 3.11 이미지 기반
FROM python:3.11-slim

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치 (캐시 활용)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libgl1-mesa-dev \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl

# uv 설치 (pip보다 10-100배 빠름)
RUN pip install uv

# 의존성 파일 복사 및 설치 (uv 캐시 마운트로 빠른 설치)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# NLTK 데이터 다운로드
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# 백엔드 코드 복사
RUN mkdir -p /app
COPY ./ /app

# 업로드 디렉토리 생성
RUN mkdir -p /app/uploaded_resumes

# 포트 노출
EXPOSE 8000

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 서버 실행 (개발 모드에서는 --reload 옵션 사용)
CMD ["sh", "-c", "if [ \"$ENVIRONMENT\" = \"development\" ] || [ -z \"$ENVIRONMENT\" ]; then uvicorn main:app --host 0.0.0.0 --port 8000 --reload; else uvicorn main:app --host 0.0.0.0 --port 8000; fi"]
