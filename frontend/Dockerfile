FROM node:22-bookworm-slim AS frontend
WORKDIR /app

# 빌드에 필요한 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-pip \
    python3-requests \
    python3-dotenv \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    libpng-dev \
    libfreetype6-dev \
    git \
 && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 (캐시 최적화)
COPY package*.json ./
RUN npm ci

# 소스 복사
COPY . .

# 환경 설정
ENV NODE_ENV=production
ENV PORT=3000

# 운영 / 개발 겸용 실행 명령
# NODE_ENV 값에 따라 자동으로 dev 또는 start 실행
CMD ["sh", "-c", "if [ \"$NODE_ENV\" = \"production\" ]; then npm run build && npm run start; else npm run dev; fi"]

EXPOSE 3000
