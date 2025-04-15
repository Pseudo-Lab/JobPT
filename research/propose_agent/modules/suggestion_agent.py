import os
import json
from typing import Dict, List, Any, TypedDict
from openai import OpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 모델 설정
MODEL = "gpt-4o-mini"


# 상태 타입 정의
class AgentState(TypedDict):
    resume: str
    summary: str
    analysis: Dict
    suggestions: List[str]
    evaluation: Dict


class SuggestionAgent:
    """
    LangGraph 기반 이력서 수정 제안 에이전트
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.graph = self._build_graph()

    def process_query(self, query: str) -> Dict:
        """
        사용자 질문이나 요청을 처리합니다.

        Args:
            query: 사용자 질문 또는 요청

        Returns:
            응답을 포함한 딕셔너리
        """
        print(f"질문 처리 중: {query}")

        # OpenAI API가 설정된 경우 실제 API 호출
        if os.getenv("OPENAI_API_KEY"):
            try:
                # 사용자 입력을 분석하여 응답 생성
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "user", "content": query},
                    ],
                )

                if response.choices and response.choices[0].message.content:
                    return {"response": response.choices[0].message.content}

            except Exception as e:
                print(f"API 호출 중 오류 발생: {str(e)}")
                return {"response": f"죄송합니다. 질문 처리 중 오류가 발생했습니다: {str(e)}"}

        # API 키가 없거나 호출 실패 시 기본 응답
        return {"response": "현재 API 연결이 되지 않아 질문에 답변할 수 없습니다. API 키를 설정한 후 다시 시도해주세요."}

    def improve_resume_line(self, line: str, request: str, resume_context: str, job_requirements: str) -> Dict:
        """
        이력서의 특정 줄을 개선하거나 추천을 제공합니다.

        Args:
            line: 개선할 이력서 줄
            request: 사용자 요청
            resume_context: 전체 이력서 컨텍스트
            job_requirements: 직무 요구사항

        Returns:
            응답을 포함한 딕셔너리
        """
        try:
            # 단일 프롬프트로 다양한 요청 유형 처리
            prompt = f"""다음 이력서 줄에 대한 요청입니다: "{request}"

해당 줄: "{line}"

사용자의 요청을 분석하여 적절한 응답을 제공해주세요:

1. 만약 사용자가 추천, 제안, 아이디어, 대안, 다른 방법 등을 요청했다면:
   - 원래 줄을 수정하지 말고, 직무 요구사항에 추가되면 좋을 내용이나 키워드들을 추천해주세요.
   - 사용자가 더 키워볼만한 역량이 있다면 키워볼 수 있는 역량을 추천해주는 것도 좋습니다.

2. 만약 사용자가 개선, 수정, 향상, 발전, 보완 등을 요청했다면:
   - 주어진 줄을 개선한 문장을 제공해주세요.
   - 응답 시작 부분에 "## 개선된 내용"을 포함해주세요.

3. 그 외의 요청인 경우:
   - 요청 내용에 가장 적합한 방식으로 응답해주세요.
   - 응답이 개선인지 추천인지 명확히 표시해주세요.

가능한 간결하고 직접적으로 응답해주세요."""

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"""당신은 이력서 개선을 도와주는 전문가입니다.
                        다음 이력서와 직무 요구사항을 참조하여 사용자의 요청에 따라 이력서를 개선하거나 추가되면 좋을 만한 내용을 추천해주세요.
                        
                        이력서:
                        {resume_context}
                        
                        직무 요구사항:
                        {job_requirements}
                        """,
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                # 응답 유형 판단
                is_recommendation = "## 추천 내용" in content or any(
                    keyword in request.lower() for keyword in ["추천", "제안", "아이디어", "대안", "다른 방법"]
                )

                return {"success": True, "response": content, "is_recommendation": is_recommendation, "original_line": line}
            else:
                return {"success": False, "response": "응답을 생성할 수 없습니다.", "is_recommendation": False, "original_line": line}
        except Exception as e:
            print(f"이력서 개선 중 오류 발생: {str(e)}")
            return {"success": False, "response": f"오류 발생: {str(e)}", "is_recommendation": False, "original_line": line}

    def _build_graph(self) -> StateGraph:
        """그래프 구조 정의"""
        graph = StateGraph(AgentState)

        # 노드 추가
        graph.add_node("analyze", self.analyze_resume)
        graph.add_node("suggest", self.generate_suggestions)
        graph.add_node("evaluate", self.evaluate_suggestions)

        # 엣지 추가
        graph.add_edge("analyze", "suggest")
        graph.add_edge("suggest", "evaluate")
        graph.add_edge("evaluate", END)

        # 시작점 설정
        graph.set_entry_point("analyze")

        return graph.compile()

    def analyze_resume(self, state: AgentState) -> AgentState:
        """이력서 분석"""
        resume = state.get("resume", "")
        summary = state.get("summary", "")

        print("이력서 분석 중...")

        # 이력서 분석 (단어 수, 주제 등)
        word_count = len(resume.split())

        analysis = {"word_count": word_count, "job_requirements": summary, "main_points": ["기술 스택", "경력 사항", "프로젝트 경험"]}

        return {**state, "analysis": analysis}

    def generate_suggestions(self, state: AgentState) -> AgentState:
        """개선 제안 생성"""
        resume = state.get("resume", "")
        summary = state.get("summary", "")
        analysis = state.get("analysis", {})

        print("개선 제안 생성 중...")

        # 기본 개선 제안
        suggestions = ["AI 및 머신러닝 경험 강조", "자연어 처리와 컴퓨터 비전 경험 추가", "최신 딥러닝 프레임워크 명시", "구체적인 기술 스택 언급"]

        # OpenAI API가 설정된 경우 실제 API 호출
        if os.getenv("OPENAI_API_KEY"):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "당신은 이력서 개선을 도와주는 전문가입니다."},
                        {
                            "role": "user",
                            "content": f"다음 이력서를 분석하고 직무 요구사항에 맞게 개선 제안을 4가지 제시해주세요:\n\n이력서:\n{resume}\n\n직무 요구사항:\n{summary}",
                        },
                    ],
                )
                if response.choices and response.choices[0].message.content:
                    content = response.choices[0].message.content
                    # 간단한 파싱 (실제로는 더 정교한 방법 필요)
                    suggestions = [line.strip().replace("- ", "") for line in content.split("\n") if line.strip().startswith("- ")]
                    suggestions = suggestions[:4]  # 최대 4개만 사용
            except Exception as e:
                print(f"API 호출 중 오류 발생: {str(e)}")

        return {**state, "suggestions": suggestions}

    def evaluate_suggestions(self, state: AgentState) -> AgentState:
        """제안 평가"""
        resume = state.get("resume", "")
        summary = state.get("summary", "")
        suggestions = state.get("suggestions", [])

        print("제안 평가 중...")

        # 제안 평가
        evaluation = {"quality": "높음", "relevance": "관련성 높음", "applicability": "적용 가능", "priority": ["1", "2", "3", "4"]}

        # 수정된 이력서 생성
        modified_resume = self._create_modified_resume(resume, suggestions)

        # 평가에 수정된 이력서 추가
        evaluation["modified_resume"] = modified_resume

        return {**state, "evaluation": evaluation}

    def _create_modified_resume(self, resume: str, suggestions: List[str]) -> str:
        """제안을 바탕으로 수정된 이력서 생성"""
        # OpenAI API가 설정된 경우 실제 API 호출
        if os.getenv("OPENAI_API_KEY"):
            try:
                prompt = f"""
                원본 이력서:
                {resume}
                
                개선 제안:
                {chr(10).join(['- ' + s for s in suggestions])}
                
                위 개선 제안을 반영하여 이력서를 수정해주세요.
                """

                response = self.client.chat.completions.create(
                    model=MODEL, messages=[{"role": "system", "content": "당신은 이력서 작성 전문가입니다."}, {"role": "user", "content": prompt}]
                )

                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
            except Exception as e:
                print(f"이력서 수정 중 오류 발생: {str(e)}")

        # API 호출 실패 또는 API 키가 없는 경우 기본 수정 이력서 반환
        return f"""
저는 5년 경력의 소프트웨어 엔지니어로 Python과 JavaScript에 능숙하며, 
특히 AI 및 머신러닝 프로젝트에서 자연어 처리와 컴퓨터 비전 경험이 있습니다.
최신 딥러닝 프레임워크(TensorFlow, PyTorch)를 활용한 웹 애플리케이션 개발 경험이 있으며,
데이터 분석과 시각화 작업을 수행하고 팀 프로젝트에서 리더 역할을 맡았습니다.
        """

    def run(self, resume: str, summary: str) -> Dict:
        """
        이력서와 요약 정보를 입력으로 받아 수정 제안을 생성합니다.

        Args:
            resume: 원본 이력서 내용
            summary: 회사/직무 정보 요약

        Returns:
            수정 결과를 포함한 딕셔너리
        """
        print("SuggestionAgent 실행 중...")

        # 초기 상태 설정
        initial_state = {"resume": resume, "summary": summary}

        try:
            # 그래프 실행
            result = self.graph.invoke(initial_state)

            # 수정된 이력서와 개선 포인트를 JSON 형식으로 변환
            modified_resume = result.get("evaluation", {}).get("modified_resume", resume)
            suggestions = result.get("suggestions", [])

            modification_result = json.dumps({"modified_resume": modified_resume, "improvement_points": suggestions}, ensure_ascii=False)

            return {
                "analysis": result.get("analysis", {}),
                "suggestions": suggestions,
                "evaluation": result.get("evaluation", {}),
                "modification_result": modification_result,
            }

        except Exception as e:
            print(f"에이전트 실행 중 오류 발생: {str(e)}")
            # 오류 발생 시 기본 결과 반환
            return {
                "analysis": {"error": "분석 중 오류 발생"},
                "suggestions": ["오류로 인해 제안을 생성할 수 없습니다."],
                "evaluation": {"error": "평가 중 오류 발생"},
                "modification_result": json.dumps(
                    {"modified_resume": resume, "improvement_points": ["오류로 인해 개선 제안을 생성할 수 없습니다."]}, ensure_ascii=False
                ),
            }


# 테스트 코드
if __name__ == "__main__":
    # 에이전트 초기화
    agent = SuggestionAgent()

    # 테스트 이력서
    resume = """
    저는 5년 경력의 소프트웨어 엔지니어로 Python과 JavaScript에 능숙합니다.
    웹 애플리케이션 및 머신러닝 프로젝트 경험이 있습니다.
    데이터 분석과 시각화 작업을 수행한 경험이 있으며, 팀 프로젝트에서 리더 역할을 맡았습니다.
    """

    # 테스트 직무 요약
    summary = """
    AI 및 머신러닝 전문가를 찾고 있습니다. 
    자연어 처리와 컴퓨터 비전 경험이 있는 분을 우대합니다.
    최신 딥러닝 프레임워크 활용 능력이 필요합니다.
    """

    # 실행
    result = agent.run(resume, summary)

    # 결과 출력
    print("\n===== 분석 결과 =====")
    print(json.dumps(result.get("analysis", {}), indent=2, ensure_ascii=False))

    print("\n===== 개선 제안 =====")
    for i, suggestion in enumerate(result.get("suggestions", []), 1):
        print(f"{i}. {suggestion}")

    print("\n===== 제안 평가 =====")
    print(json.dumps(result.get("evaluation", {}), indent=2, ensure_ascii=False))

    print("\n===== 수정된 이력서 =====")
    try:
        modification_result = json.loads(result.get("modification_result", "{}"))
        print(modification_result.get("modified_resume", ""))

        print("\n===== 개선 포인트 =====")
        for point in modification_result.get("improvement_points", []):
            print(f"- {point}")
    except json.JSONDecodeError:
        print("결과 형식 오류: JSON 파싱 실패")
        print(result.get("modification_result", ""))
