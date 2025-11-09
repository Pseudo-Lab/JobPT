"""
GitHub Agent 테스트 스크립트

이 스크립트는 github_agent.py의 기능을 테스트합니다.
LangGraph를 사용하여 간단한 그래프를 구성하고 GitHub 스크래핑 도구들을 테스트합니다.
"""

import asyncio
from multi_agents.states.states import State
from multi_agents.agent.github_agent import github_agent
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage


async def create_github_test_graph():
    """GitHub Agent를 테스트하기 위한 간단한 그래프 생성"""
    builder = StateGraph(State)
    
    # GitHub Agent 노드 추가
    builder.add_node("github_agent", github_agent)
    
    # Start → GitHub Agent → End
    builder.add_edge("__start__", "github_agent")
    builder.add_edge("github_agent", "__end__")
    
    return builder.compile()


async def test_github_agent():
    """GitHub Agent 테스트 실행"""
    
    # 테스트 케이스들
    test_cases = [
        {
            "description": "테스트 1: 사용자 프로필 분석",
            "github_url": "https://github.com/Pseudo-Lab",
            "query": "JobPT 레포에 대해서 요약해줘",
        },
        # {
        #     "description": "테스트 2: 저장소 상세 분석",
        #     "github_url": "https://github.com/Pseudo-Lab",
        #     "query": "이 저장소의 README, 최근 커밋, 사용 언어를 분석해주세요.",
        # },
        # {
        #     "description": "테스트 3: 조직 분석",
        #     "github_url": "https://github.com/Pseudo-Lab",
        #     "query": "이 조직의 주요 오픈소스 프로젝트들을 파악하고, 어떤 기술 스택을 사용하는지 분석해주세요.",
        # },
    ]
    
    # 그래프 생성
    graph = await create_github_test_graph()
    
    print("=" * 80)
    print("GitHub Agent 테스트 시작")
    print("=" * 80)
    print()
    
    # 각 테스트 케이스 실행
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"{case['description']}")
        print(f"{'=' * 80}")
        print(f"GitHub URL: {case['github_url']}")
        print(f"사용자 질문: {case['query']}")
        print("-" * 80)
        
        # State 초기화
        state = State(
            session_id=f"test_session_{i}",
            github_url=case['github_url'],
            company_name=case['github_url'].split('/')[-1],  # URL에서 마지막 부분을 이름으로 사용
            messages=[HumanMessage(content=case['query'])],
        )
        
        try:
            # 그래프 실행
            print("Agent 실행 중...\n")
            result = await graph.ainvoke(state)
            
            # 결과 출력
            print("=" * 80)
            print("분석 결과:")
            print("=" * 80)
            if result.get("messages"):
                final_message = result["messages"][-1]
                print(final_message.content)
            else:
                print("결과가 없습니다.")
                
        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print(f"테스트 {i} 완료")
        print("=" * 80)
        
        # 다음 테스트 전 잠시 대기 (API rate limit 방지)
        if i < len(test_cases):
            print("\n다음 테스트까지 3초 대기...\n")
            await asyncio.sleep(3)
    
    print("\n" + "=" * 80)
    print("모든 테스트 완료!")
    print("=" * 80)




async def main():
    """메인 테스트 함수"""
    import sys
    
    print("\n" + "=" * 80)
    print("GitHub Agent 통합 테스트 프로그램")
    print("=" * 80)
    print("\n테스트 모드를 선택하세요:")
    print("1. 전체 에이전트 테스트 (LangGraph 사용)")
    print("2. 개별 도구 테스트 (도구 직접 호출)")
    print("3. 둘 다 실행")
    
    # 자동 실행 모드 (인자가 있으면)
    await test_github_agent()



if __name__ == "__main__":
    # 간단한 사용법
    # python test_github_agent.py 1  # 전체 에이전트 테스트
    # python test_github_agent.py 2  # 개별 도구 테스트
    # python test_github_agent.py 3  # 둘 다 실행
    # python test_github_agent.py     # 대화형 모드
    
    asyncio.run(main())

