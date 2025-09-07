#!/bin/bash

# 오류 발생 시 스크립트 종료
set -e

# nvm 설치
echo "Installing nvm..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# nvm 로드 (스크립트 안에서는 수동으로 source 해야 함)
export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 원하는 Node.js 버전 설치
NODE_VERSION="lts/*"  # 최신 LTS 버전 설치
echo "Installing Node.js ($NODE_VERSION)..."
nvm install "$NODE_VERSION"

# 기본 node 버전 설정
nvm alias default "$NODE_VERSION"

# PATH에 npm과 node 경로 추가
export PATH="$NVM_DIR/versions/node/$(node -v)/bin:$PATH"

# 현재 셸에 대한 환경 변수 업데이트
hash -r

# 설치 완료 확인
echo "Node.js version:"
node -v
echo "npm version:"
npm -v

echo "Node.js installation completed successfully."

# npx 사용 가능 여부 확인
echo "Checking npx availability:"
which npx || echo "npx not found in PATH"
