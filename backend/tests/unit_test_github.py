import pytest

import asyncio
import os
import sys
from pathlib import Path

# backend 디렉토리를 Python path에 추가
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from multi_agents.agent.github_tools import (
    get_github_user_info,
    get_github_repo_details,
)

def test_get_user_info():
    print("\n" + "="*60)
    print("테스트 1: GitHub 사용자 정보 조회")
    print("="*60)
    result = get_github_user_info.invoke({"username": "Pseudo-Lab"})
    print(f"✓ 사용자명: {result['login']}")
    print(f"✓ 이름: {result['name']}")
    print(f"✓ Bio: {result['bio']}")
    print(f"✓ 팔로워: {result['followers']}")
    print(f"✓ 공개 레포: {result['public_repos']}")
    assert result["login"] == "Pseudo-Lab"
    assert result["public_repos"] > 0
    print("✅ 테스트 통과!")
    return result

def test_get_repo_details():
    print("\n" + "="*60)
    print("테스트 2: 레포지토리 상세 정보 조회")
    print("="*60)
    result = get_github_repo_details.invoke({
        "owner": "Pseudo-Lab",
        "repo": "JobPT"
    })
    print(f"✓ 레포명: {result['name']}")
    print(f"✓ 설명: {result['description']}")
    print(f"✓ 언어: {result['language']}")
    print(f"✓ 스타: {result['stargazers_count']}")
    print(f"✓ 포크: {result['forks_count']}")
    print(f"✓ 생성일: {result['created_at']}")
    print(f"✓ 업데이트: {result['updated_at']}")
    assert result["name"] == "JobPT"
    assert "language" in result
    print("✅ 테스트 통과!")
    return result

if __name__ == "__main__":
    print("\n" + "🚀 GitHub Tools 테스트 시작" + "\n")
    
    try:
        # 테스트 1: 사용자 정보
        test_get_user_info()
        
        # 테스트 2: 레포지토리 정보
        test_get_repo_details()
        
        print("\n" + "="*60)
        print("🎉 모든 테스트 통과!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

