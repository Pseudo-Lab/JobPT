import asyncio
from langgraph.prebuilt import create_react_agent
from langchain_upstage import ChatUpstage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from typing import Dict, List, cast
from configs import *


async def summary_agent(state: State) -> Dict[str, List[AIMessage]]:

    model = ChatUpstage(model=AGENT_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)

    # Option 1 from error message: client = MultiServerMCPClient(...)
    try:
        client = MultiServerMCPClient(
            {
                "tavily-mcp": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@smithery/cli@latest",
                        "run",
                        "@tavily-ai/tavily-mcp",
                        "--key",
                        os.getenv("SMITHERY_API_KEY"),
                    ],
                    "transport": "stdio",
                }
            }
        )
        tools = await client.get_tools()
        agent = create_react_agent(model, tools)
    except Exception as e:
        print("summary_agent mcp error:", e)
        agent = create_react_agent(model, [])

    system_message = f"""당신은 기업 관련 정보를 수집하고 요약하는 데 특화된 어시스턴트입니다. 
    입력으로 회사명이 주어지면, 웹과 관련 플랫폼(뉴스 기사, 회사 웹사이트, 블로그, YouTube 포함)을 검색하여 해당 회사에 대한 핵심 인사이트를 수집하고 요약하는 것이 임무입니다.

    회사명: {state.company_name}

    아래 항목들에 집중하세요:
    산업 및 도메인
    - 회사가 속한 산업과 시장을 설명하세요.
    - 뉴스 기사 기반으로 최근 도메인 동향을 포함하세요.

    경쟁 우위
    - 동일 산업 내 주요 경쟁사와 비교했을 때 회사의 차별화 요소와 강점을 강조하세요.
    - 뉴스 기사에서 얻은 인사이트로 뒷받침하세요.

    주요 서비스
    - 채용 공고와 관련된 핵심 서비스나 제품을 요약하세요.
    - 뉴스 기사나 최근 업데이트에서 언급된 내용을 중심으로 작성하세요.

    인재상
    - 공식 웹사이트의 채용/커리어 페이지를 참고하여 회사가 원하는 인재 유형을 파악하세요.

    팀 문화
    - 회사 블로그, 인터뷰, YouTube 영상을 참조하여 조직 문화나 팀 문화를 설명하세요.

    진행 중인 프로젝트 및 이니셔티브
    - 채용 직무와 연관된 주목할 만한 프로젝트, 연구 분야, 혁신 이니셔티브를 뉴스 기사나 공식 발표에서 찾아 나열하세요.

    최신성 있고 관련성 높은 정보를 찾기 위해 웹 검색 및 YouTube 검색 등의 도구를 활용하세요.
    """

    messages = [SystemMessage(content=system_message), *state.messages]
    response = cast(AIMessage, await agent.ainvoke({"messages": messages}))
    return {
        "messages": [response["messages"][-1]],
        "agent_name": "summary_agent",
        "company_summary": response["messages"][-1].content,
    }
