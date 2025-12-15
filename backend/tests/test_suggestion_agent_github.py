"""
Suggestion Agent GitHub & Blog Tools 통합 테스트

이 스크립트는 suggestion_agent.py가 GitHub Tools와 Blog Tools를 제대로 호출하는지 테스트합니다.
GitHub URL 또는 Blog URL이 포함된 이력서를 입력하고, Agent가 자동으로 해당 정보를 조회하는지 확인합니다.
"""

import asyncio
import os
import sys
from pathlib import Path

# backend 디렉토리를 Python path에 추가
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from multi_agents.states.states import State
from multi_agents.agent.suggestion_agent import suggest_agent
from langchain_core.messages import HumanMessage

# 환경 변수 로드
load_dotenv()

# 테스트용 이력서 샘플 (GitHub URL 포함)
SAMPLE_RESUME_WITH_GITHUB = """
# 김민아 (Minah Kim)

## 경력 사항
- AI/ML 엔지니어 @ 가짜연구소 (2023 - 현재)
- 데이터 사이언티스트 @ 스타트업 (2021 - 2023)

## 프로젝트

### JobPT - AI 기반 채용 공고 매칭 시스템
- GitHub: https://github.com/Pseudo-Lab/JobPT
- LLM과 RAG를 활용한 이력서-채용공고 매칭 시스템 개발
- LangGraph 기반 Multi-Agent 시스템 구축
- Python, FastAPI, OpenAI API 사용

### 개인 포트폴리오
- GitHub: https://github.com/minglet

## 기술 스택
- Python, JavaScript, TypeScript
- LangChain, LangGraph, OpenAI
- FastAPI, React, Next.js
"""

# 직무 설명 샘플
JOB_DESCRIPTION = """
[포지션] Senior ML Engineer

[업무 내용]
- LLM 기반 AI 서비스 개발
- Multi-Agent 시스템 설계 및 구현
- 프로덕션 환경 배포 및 운영

[필수 역량]
- Python 3년 이상 경험
- LangChain/LangGraph 경험
- GitHub를 통한 협업 경험
- 오픈소스 기여 경험 우대

[기술 스택]
- Python, FastAPI
- LangChain, OpenAI API
- Docker, Kubernetes
"""

# 회사 정보 샘플
COMPANY_SUMMARY = """
AI 스타트업으로 LLM 기반 서비스를 개발하는 회사입니다.
오픈소스 활동을 적극 장려하며, GitHub 프로필을 중요하게 평가합니다.
"""

# 사용자 선택 섹션 (개선할 부분)
USER_SELECTED_SECTION = """
### JobPT - AI 기반 채용 공고 매칭 시스템
- GitHub: https://github.com/Pseudo-Lab/JobPT
- LLM과 RAG를 활용한 이력서-채용공고 매칭 시스템 개발
- LangGraph 기반 Multi-Agent 시스템 구축
- Python, FastAPI, OpenAI API 사용
"""


async def test_suggestion_agent_with_github():
    """GitHub URL이 포함된 이력서로 Suggestion Agent 테스트"""
    
    print("\n" + "="*80)
    print("🚀 Suggestion Agent + GitHub Tools 통합 테스트")
    print("="*80)
    
    # State 초기화
    state = State(
        session_id="test_github_integration",
        resume=SAMPLE_RESUME_WITH_GITHUB,
        job_description=JOB_DESCRIPTION,
        company_summary=COMPANY_SUMMARY,
        user_resume=USER_SELECTED_SECTION,
        messages=[
            HumanMessage(content="GitHub 프로젝트 정보를 참고해서 이 섹션을 개선해주세요.")
        ]
    )
    
    print("\n📄 입력 이력서:")
    print("-" * 80)
    print(USER_SELECTED_SECTION)
    
    print("\n🔍 테스트 시나리오:")
    print("1. Agent가 GitHub URL을 감지합니다")
    print("2. get_github_repo_details를 호출하여 레포지토리 정보를 조회합니다")
    print("3. get_github_repo_readme를 호출하여 README를 읽습니다")
    print("4. 실제 프로젝트 정보를 바탕으로 이력서를 개선합니다")
    
    print("\n⏳ Agent 실행 중...\n")
    print("="*80)
    
    try:
        # Suggestion Agent 실행
        result = await suggest_agent(state)
        
        print("\n" + "="*80)
        print("✅ 개선 결과:")
        print("="*80)
        
        if result.get("messages"):
            final_message = result["messages"][0]
            print(final_message.content)
        else:
            print("⚠️ 결과 메시지가 없습니다.")
        
        print("\n" + "="*80)
        print("🎉 테스트 완료!")
        print("="*80)
        
        # GitHub Tools 호출 여부 확인
        print("\n📊 테스트 평가:")
        response_text = result["messages"][0].content if result.get("messages") else ""
        
        checks = [
            ("GitHub 레포지토리 정보 확인", any(keyword in response_text for keyword in ["스타", "포크", "기여자", "커밋"])),
            ("README 내용 반영", "README" in response_text or len(response_text) > 500),
            ("개선 내용 포함", "**" in response_text or "개선" in response_text),
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "⚠️"
            print(f"{status} {check_name}: {'통과' if passed else '확인 필요'}")
        
    except Exception as e:
        print("\n❌ 테스트 실패!")
        print(f"에러: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_multiple_github_urls():
    """여러 GitHub URL이 포함된 경우 테스트"""
    
    print("\n" + "="*80)
    print("🚀 테스트 2: 여러 GitHub URL 처리")
    print("="*80)
    
    multi_github_resume = """
    ## 프로젝트
    
    1. JobPT: https://github.com/Pseudo-Lab/JobPT
    2. DevFactory: https://github.com/Pseudo-Lab/DevFactory
    """
    
    state = State(
        session_id="test_multi_github",
        resume=multi_github_resume,
        job_description=JOB_DESCRIPTION,
        company_summary=COMPANY_SUMMARY,
        user_resume=multi_github_resume,
        messages=[
            HumanMessage(content="두 프로젝트의 GitHub 정보를 조회해서 개선해주세요.")
        ]
    )
    
    print("\n📄 입력:")
    print(multi_github_resume)
    
    print("\n⏳ Agent 실행 중...\n")
    
    try:
        result = await suggest_agent(state)
        
        print("\n" + "="*80)
        print("✅ 개선 결과:")
        print("="*80)
        print(result["messages"][0].content if result.get("messages") else "결과 없음")
        
    except Exception as e:
        print(f"\n❌ 에러: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_github_user_profile():
    """GitHub 사용자 프로필 URL 테스트"""
    
    print("\n" + "="*80)
    print("🚀 테스트 3: GitHub 사용자 프로필")
    print("="*80)
    
    user_profile_resume = """
    ## 온라인 프로필
    - GitHub: https://github.com/minglet
    - 120+ 기여, 다수의 오픈소스 프로젝트 참여
    """
    
    state = State(
        session_id="test_user_profile",
        resume=user_profile_resume,
        job_description=JOB_DESCRIPTION,
        company_summary=COMPANY_SUMMARY,
        user_resume=user_profile_resume,
        messages=[
            HumanMessage(content="GitHub 프로필을 조회해서 구체적인 활동 내역을 추가해주세요.")
        ]
    )
    
    print("\n📄 입력:")
    print(user_profile_resume)
    
    print("\n⏳ Agent 실행 중...\n")
    
    try:
        result = await suggest_agent(state)
        
        print("\n" + "="*80)
        print("✅ 개선 결과:")
        print("="*80)
        print(result["messages"][0].content if result.get("messages") else "결과 없음")
        
    except Exception as e:
        print(f"\n❌ 에러: {str(e)}")
        import traceback
        traceback.print_exc()


# ============================================================================
# Blog Tools 테스트
# ============================================================================

# 블로그 URL이 포함된 이력서 샘플
SAMPLE_RESUME_WITH_BLOG = """
# 김민아 (Minah Kim)

## 경력 사항
- AI/ML 엔지니어 @ 가짜연구소 (2023 - 현재)
- 데이터 사이언티스트 @ 스타트업 (2021 - 2023)

## 온라인 활동

### 기술 블로그
- Tistory: https://day-to-day.tistory.com/
- AI, ML, LLM 관련 기술 블로그 운영
- 월 평균 1000+ 방문자

## 기술 스택
- Python, JavaScript, TypeScript
- LangChain, LangGraph, OpenAI
- FastAPI, React, Next.js
"""

# 블로그 섹션 개선 요청
USER_SELECTED_BLOG_SECTION = """
### 기술 블로그
- Tistory: https://day-to-day.tistory.com/
- AI, ML, LLM 관련 기술 블로그 운영
- 월 평균 1000+ 방문자
"""


async def test_suggestion_agent_with_blog():
    """Blog URL이 포함된 이력서로 Suggestion Agent 테스트"""
    
    print("\n" + "="*80)
    print("🚀 테스트 4: Blog Tools 통합 테스트")
    print("="*80)
    
    # State 초기화
    state = State(
        session_id="test_blog_integration",
        resume=SAMPLE_RESUME_WITH_BLOG,
        job_description=JOB_DESCRIPTION,
        company_summary=COMPANY_SUMMARY,
        user_resume=USER_SELECTED_BLOG_SECTION,
        messages=[
            HumanMessage(content="블로그 정보를 조회해서 구체적인 활동 내역과 주요 게시물을 추가해주세요.")
        ]
    )
    
    print("\n📄 입력 이력서:")
    print("-" * 80)
    print(USER_SELECTED_BLOG_SECTION)
    
    print("\n🔍 테스트 시나리오:")
    print("1. Agent가 Blog URL을 감지합니다")
    print("2. fetch_homepage_overview를 호출하여 블로그 기본 정보를 조회합니다")
    print("3. list_recent_posts를 호출하여 최근 게시물을 확인합니다")
    print("4. 블로그 활동 정보를 바탕으로 이력서를 개선합니다")
    
    print("\n⏳ Agent 실행 중...\n")
    print("="*80)
    
    try:
        # Suggestion Agent 실행
        result = await suggest_agent(state)
        
        print("\n" + "="*80)
        print("✅ 개선 결과:")
        print("="*80)
        
        if result.get("messages"):
            final_message = result["messages"][0]
            print(final_message.content)
        else:
            print("⚠️ 결과 메시지가 없습니다.")
        
        print("\n" + "="*80)
        print("🎉 테스트 완료!")
        print("="*80)
        
        # Blog Tools 호출 여부 확인
        print("\n📊 테스트 평가:")
        response_text = result["messages"][0].content if result.get("messages") else ""
        
        checks = [
            ("블로그 정보 확인", any(keyword in response_text for keyword in ["블로그", "게시물", "카테고리", "포스트"])),
            ("게시물 내용 반영", any(keyword in response_text for keyword in ["글", "작성", "주제", "기술"])),
            ("개선 내용 포함", "**" in response_text or "개선" in response_text),
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "⚠️"
            print(f"{status} {check_name}: {'통과' if passed else '확인 필요'}")
        
    except Exception as e:
        print("\n❌ 테스트 실패!")
        print(f"에러: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_blog_with_specific_post():
    """특정 블로그 게시물 분석 테스트"""
    
    print("\n" + "="*80)
    print("🚀 테스트 5: 특정 블로그 게시물 분석")
    print("="*80)
    
    blog_post_resume = """
    ## 기술 블로그 활동
    
    - 블로그: https://day-to-day.tistory.com/
    - 주요 게시물: LLM Agent 구현 가이드
    - AI/ML 관련 기술 글 정기 작성
    """
    
    state = State(
        session_id="test_blog_post",
        resume=blog_post_resume,
        job_description=JOB_DESCRIPTION,
        company_summary=COMPANY_SUMMARY,
        user_resume=blog_post_resume,
        messages=[
            HumanMessage(content="블로그의 최근 게시물들을 분석해서 구체적인 기술 블로깅 활동을 이력서에 반영해주세요.")
        ]
    )
    
    print("\n📄 입력:")
    print(blog_post_resume)
    
    print("\n⏳ Agent 실행 중...\n")
    
    try:
        result = await suggest_agent(state)
        
        print("\n" + "="*80)
        print("✅ 개선 결과:")
        print("="*80)
        print(result["messages"][0].content if result.get("messages") else "결과 없음")
        
    except Exception as e:
        print(f"\n❌ 에러: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_github_and_blog_combined():
    """GitHub와 Blog URL이 모두 포함된 경우 테스트"""
    
    print("\n" + "="*80)
    print("🚀 테스트 6: GitHub + Blog 통합 테스트")
    print("="*80)
    
    combined_resume = """
    ## 온라인 프로필
    
    ### GitHub
    - https://github.com/Pseudo-Lab/JobPT
    - AI 기반 채용 매칭 시스템 개발
    
    ### 기술 블로그
    - https://day-to-day.tistory.com/
    - AI/ML 관련 기술 글 작성
    """
    
    state = State(
        session_id="test_combined",
        resume=combined_resume,
        job_description=JOB_DESCRIPTION,
        company_summary=COMPANY_SUMMARY,
        user_resume=combined_resume,
        messages=[
            HumanMessage(content="GitHub 프로젝트와 블로그 활동을 모두 조회해서 온라인 프로필 섹션을 개선해주세요.")
        ]
    )
    
    print("\n📄 입력:")
    print(combined_resume)
    
    print("\n⏳ Agent 실행 중...\n")
    
    try:
        result = await suggest_agent(state)
        
        print("\n" + "="*80)
        print("✅ 개선 결과:")
        print("="*80)
        print(result["messages"][0].content if result.get("messages") else "결과 없음")
        
        # 통합 평가
        print("\n📊 통합 테스트 평가:")
        response_text = result["messages"][0].content if result.get("messages") else ""
        
        checks = [
            ("GitHub 정보 반영", any(keyword in response_text for keyword in ["스타", "포크", "커밋", "레포"])),
            ("블로그 정보 반영", any(keyword in response_text for keyword in ["블로그", "게시물", "포스트", "글"])),
            ("통합 개선 완료", "**" in response_text),
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "⚠️"
            print(f"{status} {check_name}: {'통과' if passed else '확인 필요'}")
        
    except Exception as e:
        print(f"\n❌ 에러: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 실행"""
    
    print("\n" + "🧪 Suggestion Agent GitHub & Blog Tools 통합 테스트 시작")
    print("="*80)
    
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        return
    
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        print("✓ GITHUB_TOKEN 설정됨 (Rate Limit: 5000/hour)")
    else:
        print("⚠️ GITHUB_TOKEN 미설정 (Rate Limit: 60/hour)")
    
    print("\n" + "="*80)
    print("📋 사용 가능한 테스트:")
    print("="*80)
    print("1. GitHub 기본 테스트 (단일 GitHub URL)")
    print("2. GitHub 다중 URL 테스트")
    print("3. GitHub 사용자 프로필 테스트")
    print("4. Blog 기본 테스트 (단일 Blog URL)")
    print("5. Blog 게시물 분석 테스트")
    print("6. GitHub + Blog 통합 테스트")
    print("7. 전체 테스트 실행")
    print("0. 종료")
    print("="*80)
    
    choice = input("\n테스트 번호를 선택하세요 (기본값: 1): ").strip() or "1"
    
    if choice == "1":
        await test_suggestion_agent_with_github()
    elif choice == "2":
        await test_multiple_github_urls()
    elif choice == "3":
        await test_github_user_profile()
    elif choice == "4":
        await test_suggestion_agent_with_blog()
    elif choice == "5":
        await test_blog_with_specific_post()
    elif choice == "6":
        await test_github_and_blog_combined()
    elif choice == "7":
        print("\n🔄 전체 테스트 실행 중...\n")
        await test_suggestion_agent_with_github()
        await test_multiple_github_urls()
        await test_github_user_profile()
        await test_suggestion_agent_with_blog()
        await test_blog_with_specific_post()
        await test_github_and_blog_combined()
    elif choice == "0":
        print("테스트를 종료합니다.")
        return
    else:
        print(f"⚠️ 잘못된 선택: {choice}")
        print("기본 테스트(1)를 실행합니다.")
        await test_suggestion_agent_with_github()
    
    print("\n" + "="*80)
    print("🏁 테스트 종료")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

