# Python 3.11 이미지 기반
FROM python:3.11-slim

# 작업 디렉터리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 보수적으로 requests 설치 보장
RUN pip install --no-cache-dir requests==2.31.0

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

# 서버 실행 (docker-compose에서 command로 override 가능)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
