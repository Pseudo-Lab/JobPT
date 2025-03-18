#!/bin/bash

# 스크립트 실패 시 즉시 중단
set -e

# 기본 설정
PUSH_IMAGES=false  # 기본값: 이미지 푸시하지 않음
NO_CACHE=false     # 기본값: 캐시 사용
BUILD_API=true     # 기본값: API 이미지 빌드
BUILD_WEB=true     # 기본값: 웹 이미지 빌드

# 명령줄 인자 처리
while [[ $# -gt 0 ]]; do
  case $1 in
    --push)
      PUSH_IMAGES=true
      shift
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    --api-only)
      BUILD_API=true
      BUILD_WEB=false
      shift
      ;;
    --web-only)
      BUILD_API=false
      BUILD_WEB=true
      shift
      ;;
    *)
      echo "알 수 없는 옵션: $1"
      echo "사용법: $0 [--push] [--no-cache] [--api-only] [--web-only]"
      exit 1
      ;;
  esac
done

# 환경변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY가 설정되지 않았습니다. 설정해주세요."
    echo "예: export OPENAI_API_KEY=your-openai-api-key"
    exit 1
fi

if [ -z "$DOCKER_USERNAME" ]; then
    echo "DOCKER_USERNAME이 설정되지 않았습니다. 설정해주세요."
    echo "예: export DOCKER_USERNAME=your-docker-username"
    exit 1
fi

# 이미지 푸시 여부에 따른 설정
if [ "$PUSH_IMAGES" = true ]; then
    # Docker Hub 로그인 확인
    echo "Docker Hub 로그인 상태 확인 중..."
    if ! docker info | grep -q "Username: $DOCKER_USERNAME"; then
        echo "Docker Hub에 로그인되어 있지 않습니다. 로그인해주세요."
        docker login
    fi
    
    PUSH_FLAG="--push"
    BUILD_PLATFORM="linux/amd64,linux/arm64"
    echo "이미지를 빌드하고 Docker Hub에 푸시합니다."
else
    PUSH_FLAG="--load"
    # 현재 시스템 아키텍처만 빌드
    BUILD_PLATFORM="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/arm64/arm64/')"
    echo "이미지를 로컬에만 빌드합니다 (푸시하지 않음)."
fi

echo "빌드 플랫폼: $BUILD_PLATFORM"

# 캐시 사용 여부에 따른 설정
if [ "$NO_CACHE" = true ]; then
    CACHE_FLAG="--no-cache"
    echo "캐시를 사용하지 않고 처음부터 빌드합니다."
else
    CACHE_FLAG=""
    echo "캐시를 사용하여 빌드합니다."
fi

# Docker 시스템 정리
echo "Docker 시스템 정리 중..."
docker system prune -f

# Docker Buildx 설정
echo "Docker Buildx 설정 중..."
docker buildx create --name jobpt-builder --use || true
docker buildx inspect --bootstrap

# 캐시 디렉토리 생성
if [ "$NO_CACHE" = false ]; then
    if [ "$BUILD_API" = true ]; then
        mkdir -p ~/.docker/buildx-cache/api
    fi
    if [ "$BUILD_WEB" = true ]; then
        mkdir -p ~/.docker/buildx-cache/web
    fi
fi

# 빌드 메모리 최적화를 위한 환경변수 설정
export DOCKER_BUILDKIT=1
export DOCKER_CLI_EXPERIMENTAL=enabled
export DOCKER_BUILDX_CACHE_ENABLED=true

# API 이미지 빌드
if [ "$BUILD_API" = true ]; then
    echo "API 이미지 빌드 중..."
    if [ "$NO_CACHE" = true ]; then
        # 캐시 없이 빌드
        docker buildx build \
            --platform ${BUILD_PLATFORM} \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            -t ${DOCKER_USERNAME}/jobpt:api \
            -f Dockerfile.api \
            ${CACHE_FLAG} \
            ${PUSH_FLAG} \
            .
    else
        # 캐시 사용하여 빌드
        docker buildx build \
            --platform ${BUILD_PLATFORM} \
            --cache-from type=local,src=~/.docker/buildx-cache/api \
            --cache-to type=local,dest=~/.docker/buildx-cache/api \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            -t ${DOCKER_USERNAME}/jobpt:api \
            -f Dockerfile.api \
            ${PUSH_FLAG} \
            .
    fi
    echo "API 이미지 빌드 완료: ${DOCKER_USERNAME}/jobpt:api"
fi

# 웹 이미지 빌드
if [ "$BUILD_WEB" = true ]; then
    echo "웹 이미지 빌드 중..."
    if [ "$NO_CACHE" = true ]; then
        # 캐시 없이 빌드
        docker buildx build \
            --platform ${BUILD_PLATFORM} \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            -t ${DOCKER_USERNAME}/jobpt:web \
            -f Dockerfile.web \
            ${CACHE_FLAG} \
            ${PUSH_FLAG} \
            .
    else
        # 캐시 사용하여 빌드
        docker buildx build \
            --platform ${BUILD_PLATFORM} \
            --cache-from type=local,src=~/.docker/buildx-cache/web \
            --cache-to type=local,dest=~/.docker/buildx-cache/web \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            -t ${DOCKER_USERNAME}/jobpt:web \
            -f Dockerfile.web \
            ${PUSH_FLAG} \
            .
    fi
    echo "웹 이미지 빌드 완료: ${DOCKER_USERNAME}/jobpt:web"
fi

echo "빌드 완료!"
if [ "$PUSH_IMAGES" = true ]; then
    echo "이미지가 Docker Hub에 푸시되었습니다."
else
    echo "이미지가 로컬에만 빌드되었습니다."
fi

# 빌드된 이미지 정보 출력
if [ "$BUILD_API" = true ]; then
    echo "API 이미지: ${DOCKER_USERNAME}/jobpt:api"
fi
if [ "$BUILD_WEB" = true ]; then
    echo "웹 이미지: ${DOCKER_USERNAME}/jobpt:web"
fi

echo ""
echo "사용법:"
if [ "$BUILD_API" = true ]; then
    echo "  docker run -e OPENAI_API_KEY=your-key -p 8000:8000 ${DOCKER_USERNAME}/jobpt:api"
fi
if [ "$BUILD_WEB" = true ]; then
    echo "  docker run -e OPENAI_API_KEY=your-key -p 7860:7860 ${DOCKER_USERNAME}/jobpt:web"
fi

echo ""
echo "스크립트 옵션:"
echo "  --push: 이미지를 Docker Hub에 푸시합니다"
echo "  --no-cache: 캐시를 사용하지 않고 처음부터 빌드합니다"
echo "  --api-only: API 이미지만 빌드합니다"
echo "  --web-only: 웹 이미지만 빌드합니다"
