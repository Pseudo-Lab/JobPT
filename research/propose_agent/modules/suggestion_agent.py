import os
from typing import List, Dict, Any
import requests
import json
from openai import OpenAI
from langgraph.graph import StateGraph, END
from config import MODEL
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class VectorDB:
    def search(self, query: str) -> str:
        # 실제 구현은 무시하고 더미 응답 반환
        return "더미 검색 결과입니다."


class WebSearchTool:
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

    def search(self, question: str) -> List[Dict]:
        """
        Tavily Search API를 사용하여 웹 검색을 수행합니다.

        Args:
            question: 검색할 질문

        Returns:
            검색 결과 목록 (제목, 내용, URL 포함)
        """
        if not self.tavily_api_key:
            print("Tavily API 키가 설정되지 않았습니다. 시뮬레이션된 결과를 반환합니다.")
            return self._get_simulated_results(question)

        try:
            # Tavily Search API 엔드포인트
            url = "https://api.tavily.com/search"

            # 요청 파라미터
            params = {
                "api_key": self.tavily_api_key,
                "query": question,
                "search_depth": "basic",  # basic 또는 advanced
                "include_domains": [],  # 특정 도메인만 포함 (선택 사항)
                "exclude_domains": [],  # 특정 도메인 제외 (선택 사항)
                "max_results": 5,  # 최대 결과 수
            }

            # API 요청
            response = requests.post(url, json=params)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

            # 응답 파싱
            search_data = response.json()

            # 결과 형식 변환
            results = []
            for result in search_data.get("results", []):
                results.append({"title": result.get("title", "제목 없음"), "snippet": result.get("content", "내용 없음"), "url": result.get("url", "URL 없음")})

            return results

        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")
            # 오류 발생 시 시뮬레이션된 결과 반환
            return self._get_simulated_results(question)

    def _get_simulated_results(self, question: str) -> List[Dict]:
        """시뮬레이션된 검색 결과를 반환합니다."""
        return [
            {
                "title": f"'{question}'에 관한 최신 트렌드",
                "snippet": f"{question}에 관한 최신 정보와 트렌드입니다. 이 분야는 최근 급속도로 발전하고 있습니다.",
                "url": "https://example.com/trends",
            },
            {
                "title": f"{question} 관련 직무 요구사항",
                "snippet": f"{question} 관련 직무에서는 최신 기술과 도구에 대한 이해가 필요합니다.",
                "url": "https://example.com/job-requirements",
            },
            {
                "title": f"{question}에 대한 전문가 의견",
                "snippet": f"전문가들은 {question}에 대해 다양한 의견을 제시합니다. 주요 관점은...",
                "url": "https://example.com/expert-opinions",
            },
        ]


class ModifyTool:
    def __init__(self):
        # API 키 설정
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            print("OpenAI API 키가 설정되지 않았습니다. 테스트 모드로 동작합니다.")
            self.client = None
        self.web_search_tool = WebSearchTool()

    def modify_specific_line(self, target_line: str, context_lines: str, summary: str) -> Dict:
        """
        특정 줄만 수정하는 기능입니다.

        Args:
            target_line: 수정할 대상 줄
            context_lines: 주변 맥락 내용
            summary: 회사의 최신 뉴스나 정보를 요약한 문구

        Returns:
            수정된 줄과 수정 사항 설명
        """
        # API 키가 설정되지 않은 경우 테스트 데이터 반환
        if not self.openai_api_key:
            return self._get_test_specific_line_result()

        try:
            # 관련 검색 수행
            search_results = self.web_search_tool.search(f"{target_line} {summary}")
            
            # 검색 결과를 텍스트로 변환
            search_context = "\n".join([f"제목: {result['title']}\n내용: {result['snippet']}\n출처: {result['url']}" for result in search_results])

            prompt = f"""
            # 작업: 이력서 특정 줄 개선
            
            ## 수정할 대상 줄:
            {target_line}
            
            ## 주변 맥락:
            {context_lines}
            
            ## 회사 최신 정보:
            {summary}
            
            ## 관련 검색 결과:
            {search_context}
            
            ## 지시사항:
            1. 위 정보를 바탕으로 대상 줄만 개선해주세요.
            2. 회사의 최신 뉴스나 정보를 반영하세요.
            3. 구체적이고 명확한 표현으로 수정하세요.
            4. 전문성을 강조하는 표현을 사용하세요.
            5. 주변 맥락과 자연스럽게 연결되도록 작성하세요.
            
            ## 응답 형식:
            다음 JSON 형식으로 응답해주세요:
            {{
                "modified_line": "수정된 줄 내용",
                "explanation": "수정 이유 및 개선 사항 설명"
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "당신은 이력서 개선을 돕는 전문 AI 어시스턴트입니다."}, {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            try:
                result = response.choices[0].message.content
                return json.loads(result)
            except Exception as e:
                print(f"응답 파싱 중 오류 발생: {str(e)}")
                return self._get_test_specific_line_result()

        except Exception as e:
            print(f"API 호출 중 오류 발생: {str(e)}")
            return self._get_test_specific_line_result()

    def _get_test_specific_line_result(self) -> Dict:
        """테스트용 특정 줄 수정 결과를 반환합니다."""
        return {
            "modified_line": "클라우드 기반 환경에서 확장 가능한 머신러닝 모델의 설계, 개발 및 배포, 지속 가능한 운영 관리 프로세스 확립",
            "explanation": "해당 줄은 AI 및 머신러닝 전문가의 요구사항을 반영하여, 클라우드 환경을 언급함으로써 확장성과 운영 용이성을 강조하였습니다. 또한 구체적인 작업 단계(설계, 개발, 배포, 운영 관리)를 상세히 기술하여 직무에 대한 전문성을 강화했습니다.",
        }


class SuggestionAgent:
    def __init__(self):
        self.web_search_tool = WebSearchTool()
        self.modify_tool = ModifyTool()
        self.vector_db = VectorDB()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.graph = self._build_graph()

    def search_and_modify_specific_line(self, target_line: str, context_lines: str, summary: str) -> Dict:
        """
        특정 줄만 검색 후 수정합니다.

        Args:
            target_line: 수정할 대상 줄
            context_lines: 주변 맥락 내용
            summary: 회사의 최신 뉴스나 정보를 요약한 문구

        Returns:
            수정된 줄과 수정 사항 설명
        """
        return self.modify_tool.modify_specific_line(target_line, context_lines, summary)

    def test_modify_specific_line(self, target_line: str, context_lines: str, summary: str) -> Dict:
        """
        테스트용 메서드: 실제 API 호출 없이 특정 줄 수정 결과를 반환합니다.

        Args:
            target_line: 수정할 대상 줄
            context_lines: 주변 맥락 내용
            summary: 회사의 최신 뉴스나 정보를 요약한 문구

        Returns:
            수정된 줄과 수정 사항 설명
        """
        # 테스트용 결과 반환
        return {
            "modified_line": "* 최신 머신러닝 및 딥러닝 모델 설계, 개발 및 클라우드 환경(AWS, GCP)에 배포",
            "explanation": "기존 표현을 더 구체적으로 개선했습니다. 최신 트렌드에 맞게 딥러닝을 추가하고, 클라우드 환경을 명시하여 기술적 전문성을 강조했습니다.",
        }

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(Dict)

        # 노드 추가
        graph.add_node("search", self.search_web)
        graph.add_node("modify_specific_line", self.modify_specific_line_node)

        # 조건부 엣지 추가 - search 노드에서 분기
        graph.add_edge("search", "modify_specific_line")

        # 종료 엣지 추가
        graph.add_edge("modify_specific_line", END)

        # 시작 노드 설정
        graph.set_entry_point("search")

        return graph.compile()

    def should_modify_specific_line(self, state: Dict) -> bool:
        """특정 줄 수정 모드인지 확인합니다."""
        # 명시적으로 Boolean 값 반환
        has_target_line = "target_line" in state and state.get("target_line")
        return bool(has_target_line)

    def search_web(self, state: Dict) -> Dict:
        """웹 검색을 수행합니다."""
        summary = state.get("summary", "")
        target_line = state.get("target_line", "")

        # 검색 쿼리 생성
        query = f"{target_line} {summary}" if target_line else summary

        # 웹 검색 수행
        search_results = self.web_search_tool.search(query)
        
        # 디버그용 검색 결과 출력
        print("\n===== 검색 결과 =====")
        for i, result in enumerate(search_results):
            print(f"\n결과 {i+1}:")
            print(f"제목: {result.get('title', 'N/A')}")
            print(f"내용: {result.get('snippet', 'N/A')}")
            print(f"URL: {result.get('url', 'N/A')}")
        print("=====================\n")

        # 최신 정보 추출
        latest_info = self.vector_db.search(query)

        return {**state, "search_results": search_results, "latest_info": latest_info}

    def modify_specific_line_node(self, state: Dict) -> Dict:
        """특정 줄을 수정합니다. (그래프 노드용)"""
        target_line = state.get("target_line", "")
        context_lines = state.get("context_lines", "")
        summary = state.get("summary", "")
        search_results = state.get("search_results", [])

        # 특정 줄 수정
        result = self.modify_tool.modify_specific_line(target_line, context_lines, summary)

        return {**state, "specific_line_result": result}

    def run_specific_line(self, target_line: str, context_lines: str, summary: str) -> Dict:
        """
        특정 줄과 주변 맥락, 요약 정보를 입력으로 받아 특정 줄 수정 제안을 생성합니다.

        Args:
            target_line: 수정할 대상 줄
            context_lines: 주변 맥락 내용
            summary: 회사의 최신 뉴스나 정보를 요약한 문구

        Returns:
            수정 결과를 포함한 상태 딕셔너리
        """
        initial_state = {"target_line": target_line, "context_lines": context_lines, "summary": summary}

        try:
            # 그래프 실행 시도
            try:
                # stream() 메서드를 사용하여 그래프 실행
                events = list(self.graph.stream(initial_state))

                # 마지막 이벤트의 값 반환
                if events:
                    # LangGraph 0.3.20에서는 이벤트 구조가 다를 수 있음
                    # 마지막 이벤트의 값을 추출
                    final_state = None
                    for event in events:
                        if hasattr(event, "value"):
                            final_state = event.value
                        elif hasattr(event, "data"):
                            final_state = event.data
                        elif isinstance(event, dict):
                            final_state = event

                    if final_state and "specific_line_result" in final_state:
                        return final_state
            except Exception as e:
                print(f"그래프 실행 중 오류 발생: {str(e)}")

            # 그래프 실행에 실패하거나 결과가 없는 경우 직접 메서드 호출
            print("직접 메서드를 호출하여 결과 생성")
            result = self.modify_tool.modify_specific_line(target_line, context_lines, summary)
            return {"specific_line_result": result}
        except Exception as e:
            print(f"최종 오류 발생: {str(e)}")
            # 모든 방법이 실패한 경우 테스트 결과 반환
            return {"specific_line_result": self.modify_tool._get_test_specific_line_result()}


# 테스트 코드
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # 환경 변수 로드
    load_dotenv()

    # API 키 확인
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if tavily_api_key:
        print("Tavily API 키가 설정되었습니다.")
    else:
        print("Tavily API 키가 설정되지 않았습니다. 시뮬레이션된 결과를 사용합니다.")

    if openai_api_key:
        print("OpenAI API 키가 설정되었습니다.")
    else:
        print("OpenAI API 키가 설정되지 않았습니다. 테스트 모드로 동작합니다.")

    # 에이전트 초기화
    agent = SuggestionAgent()

    # 테스트용 대상 줄
    target_line = "* 머신러닝 모델 개발 및 배포"

    # 주변 맥락
    context_lines = """
    경력
    - ABC 회사 (2020-현재)
      * 머신러닝 모델 개발 및 배포
      * 데이터 분석 및 처리
    """

    # 회사 최신 정보
    summary = "ABC 회사는 최근 클라우드 기반 AI 솔루션을 출시하고 금융 분야에서 혁신적인 머신러닝 적용 사례를 발표했습니다."

    print("\n===== 수정할 대상 줄 =====\n")
    print(target_line)

    print("\n===== 주변 맥락 =====\n")
    print(context_lines)

    print("\n===== 회사 최신 정보 =====")
    print(summary)

    print("\n===== 줄 수정 중... =====\n")

    # run_specific_line 메서드를 사용하여 그래프 실행
    result = agent.run_specific_line(target_line, context_lines, summary)

    print("\n===== 수정 결과 =====\n")
    if "specific_line_result" in result:
        specific_line_result = result["specific_line_result"]
        print("수정된 줄:")
        print(specific_line_result.get("modified_line", ""))
        print("\n설명:")
        print(specific_line_result.get("explanation", ""))
    else:
        print("수정 결과를 가져올 수 없습니다.")
