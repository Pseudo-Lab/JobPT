"""
GitHub Agent + Graph 통합 테스트

기존 graph.py의 구조를 확장하여 github_agent를 포함한 테스트를 실행합니다.
"""

import asyncio
from multi_agents.states.states import State
from multi_agents.agent.github_agent import github_agent
from multi_agents.agent.summary_agent import summary_agent
from multi_agents.agent.suggestion_agent import suggest_agent
from multi_agents.agent.supervisor_agent import router, refine_answer
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage


async def create_extended_graph():
    """GitHub Agent를 포함한 확장된 그래프 생성"""
    builder = StateGraph(State)
    
    # 기존 노드들
    builder.add_node("supervisor", router)
    builder.add_node("summary_agent", summary_agent)
    builder.add_node("suggestion_agent", suggest_agent)
    builder.add_node("refine_answer", refine_answer)
    
    # 새로운 GitHub Agent 노드 추가
    builder.add_node("github_agent", github_agent)
    
    # Start → Supervisor
    builder.add_edge("__start__", "supervisor")
    
    # Supervisor 라우팅 로직
    def route_supervisor(state: State):
        import json
        
        msg = state.messages[-1].content
        try:
            if isinstance(msg, str) and msg.strip().startswith("{"):
                seq = json.loads(msg).get("sequence", "")
            else:
                seq = msg
        except Exception:
            seq = msg
        
        # github_agent 경로 추가
        if seq not in {"summary", "suggestion", "summary_suggestion", "github", "END"}:
            seq = "END"
        state.route_decision = seq
        return seq
    
    builder.add_conditional_edges(
        source="supervisor",
        path=route_supervisor,
        path_map={
            "summary": "summary_agent",
            "suggestion": "suggestion_agent",
            "summary_suggestion": "summary_agent",
            "github": "github_agent",
            "END": "refine_answer",
        },
    )
    
    # Summary Agent 이후 라우팅
    def route_after_summary(state: State):
        state.route_decision = state.messages[-2].content
        if state.route_decision == "summary_suggestion":
            return "suggestion_agent"
        else:
            return "refine_answer"
    
    builder.add_conditional_edges(
        source="summary_agent",
        path=route_after_summary,
        path_map={
            "suggestion_agent": "suggestion_agent",
            "refine_answer": "refine_answer",
        },
    )
    
    # Suggestion Agent → Refine Answer
    builder.add_edge("suggestion_agent", "refine_answer")
    
    # GitHub Agent → Refine Answer
    builder.add_edge("github_agent", "refine_answer")
    
    # Refine Answer → End
    builder.add_edge("refine_answer", "__end__")
    
    return builder.compile()


async def test_github_only():
    """GitHub Agent만 단독으로 테스트"""
    print("\n" + "=" * 80)
    print("GitHub Agent 단독 테스트")
    print("=" * 80)
    
    test_cases = [
        {
            "description": "Linus Torvalds 프로필 분석",
            "github_url": "https://github.com/torvalds",
            "query": "이 개발자의 GitHub 프로필과 주요 프로젝트를 분석해주세요.",
        },
        {
            "description": "React 저장소 분석",
            "github_url": "https://github.com/facebook/react",
            "query": "이 저장소의 기술 스택, 최근 업데이트, README 내용을 요약해주세요.",
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {case['description']}")
        print(f"{'=' * 80}")
        print(f"GitHub URL: {case['github_url']}")
        print(f"질문: {case['query']}")
        print("-" * 80)
        
        # State 초기화
        state = State(
            session_id=f"github_test_{i}",
            github_url=case['github_url'],
            company_name=case['github_url'].split('/')[-1],
            messages=[HumanMessage(content=case['query'])],
        )
        
        try:
            # GitHub Agent 직접 호출
            print("GitHub Agent 실행 중...\n")
            result = await github_agent(state)
            
            # 결과 출력
            print("=" * 80)
            print("분석 결과:")
            print("=" * 80)
            if result.get("messages"):
                print(result["messages"][-1].content)
            else:
                print("결과가 없습니다.")
                
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        
        # 다음 테스트 전 대기
        if i < len(test_cases):
            print("다음 테스트까지 3초 대기...\n")
            await asyncio.sleep(3)


async def test_integrated_graph():
    """확장된 그래프로 통합 테스트"""
    print("\n" + "=" * 80)
    print("통합 그래프 테스트 (Supervisor + GitHub Agent)")
    print("=" * 80)
    
    graph = await create_extended_graph()
    
    test_cases = [
        {
            "description": "GitHub 분석 요청",
            "github_url": "https://github.com/openai",
            "supervisor_decision": "github",
            "query": "OpenAI의 GitHub 조직을 분석해주세요. 어떤 오픈소스 프로젝트들이 있나요?",
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {case['description']}")
        print(f"{'=' * 80}")
        print(f"GitHub URL: {case['github_url']}")
        print(f"질문: {case['query']}")
        print(f"Supervisor 결정: {case['supervisor_decision']}")
        print("-" * 80)
        
        # State 초기화
        # Supervisor의 결정을 시뮬레이션하기 위해 messages에 결정 추가
        state = State(
            session_id=f"integrated_test_{i}",
            github_url=case['github_url'],
            company_name=case['github_url'].split('/')[-1],
            messages=[
                HumanMessage(content=case['query']),
                HumanMessage(content=case['supervisor_decision']),  # Supervisor 결정 시뮬레이션
            ],
        )
        
        try:
            print("그래프 실행 중...\n")
            result = await graph.ainvoke(state)
            
            # 결과 출력
            print("=" * 80)
            print("최종 결과:")
            print("=" * 80)
            if result.get("messages"):
                final_msg = result["messages"][-1]
                print(final_msg.content)
            else:
                print("결과가 없습니다.")
                
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)


async def test_simple_scraping():
    """간단한 스크래핑 테스트 (API 없이)"""
    from multi_agents.agent.github_agent import (
        scrape_user_profile,
        scrape_user_repos,
    )
    
    print("\n" + "=" * 80)
    print("간단한 스크래핑 테스트 (OpenAI API 없이)")
    print("=" * 80)
    
    print("\n1. 사용자 프로필 스크래핑: torvalds")
    print("-" * 80)
    try:
        result = scrape_user_profile.invoke({"username": "torvalds"})
        print(f"✓ 성공!")
        print(f"  - 이름: {result.get('name')}")
        print(f"  - Bio: {result.get('bio', 'N/A')}")
        print(f"  - 팔로워: {result.get('followers')}")
        print(f"  - 저장소: {result.get('repositories')}")
    except Exception as e:
        print(f"✗ 실패: {e}")
    
    await asyncio.sleep(2)
    
    print("\n2. 저장소 목록 스크래핑: facebook")
    print("-" * 80)
    try:
        result = scrape_user_repos.invoke({"username": "facebook", "page": 1})
        print(f"✓ 성공!")
        print(f"  - 저장소 수: {result.get('count')}")
        if result.get('repositories'):
            print(f"  - 첫 저장소: {result['repositories'][0].get('name')}")
    except Exception as e:
        print(f"✗ 실패: {e}")
    
    print("\n" + "=" * 80)


async def main():
    """메인 함수"""
    import sys
    
    print("\n" + "=" * 80)
    print("GitHub Agent 통합 테스트 프로그램")
    print("=" * 80)
    print("\n테스트 모드를 선택하세요:")
    print("1. 간단한 스크래핑 테스트 (OpenAI API 불필요)")
    print("2. GitHub Agent 단독 테스트 (OpenAI API 필요)")
    print("3. 통합 그래프 테스트 (Supervisor + GitHub Agent)")
    print("4. 모두 실행")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\n선택 (1/2/3/4): ").strip()
    
    if choice == "1":
        await test_simple_scraping()
    elif choice == "2":
        await test_github_only()
    elif choice == "3":
        await test_integrated_graph()
    elif choice == "4":
        await test_simple_scraping()
        await test_github_only()
        await test_integrated_graph()
    else:
        print("잘못된 선택입니다. 1, 2, 3, 또는 4를 선택해주세요.")
    
    print("\n테스트 완료!")


if __name__ == "__main__":
    """
    사용법:
    python test_github_graph_integration.py 1  # 간단한 스크래핑 테스트
    python test_github_graph_integration.py 2  # GitHub Agent 단독 테스트
    python test_github_graph_integration.py 3  # 통합 그래프 테스트
    python test_github_graph_integration.py 4  # 모두 실행
    python test_github_graph_integration.py     # 대화형 모드
    """
    asyncio.run(main())

