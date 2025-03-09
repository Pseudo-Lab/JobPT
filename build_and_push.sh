#!/bin/bash

# Docker Buildx 설정
echo "Docker Buildx 설정 중..."
docker buildx create --name jobpt-builder --use || true
docker buildx inspect --bootstrap

# OpenAI API 키 확인
if [ -z "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY가 설정되지 않았습니다. 설정해주세요."
  echo "예: export OPENAI_API_KEY=your-openai-api-key"
  exit 1
fi

# 멀티 아키텍처 이미지 빌드 및 푸시
echo "멀티 아키텍처 이미지 빌드 및 푸시 중..."
docker buildx bake -f docker-compose.yml --push

echo "빌드 및 푸시 완료!"
echo "API 이미지: jaeghangchoi/jobpt:api"
echo "웹 이미지: jaeghangchoi/jobpt:web"
