from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
MODEL = "gpt-4.1-mini"

class SuggestionAgent:
    def __init__(self):
        self.client = OpenAI()

    def suggest(self, resume: str, summary: str):
        """
        이력서와 요약 정보를 바탕으로 개선 제안 생성
        """
        suggestions = []
        # OpenAI API 사용
        prompt = f"""
당신은 이력서 개선을 도와주는 전문가입니다.
아래 이력서와 직무(회사) 요약 정보를 참고하여, 다음 조건에 따라 3~5개의 구체적이고 실질적인 개선 제안을 생성하세요.

[조건]
- 각 제안은 반드시 한 줄로 명확하게 작성하세요.
- 이력서와 직무 요약을 모두 반영하세요.
- 직무 요구사항에 부합하는 경험, 기술, 성과, 프로젝트, 리더십, 최신 트렌드 반영 등 다양한 관점에서 제안하세요.
- 실질적으로 이력서에 추가하거나 개선하면 좋은 점을 구체적으로 제시하세요.
- 제안은 번호 목록(1. 2. 3...)으로 출력하세요.

[이력서]
{resume}

[직무 요약]
{summary}
"""
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "위 조건을 반드시 지켜서 이력서 개선 제안을 작성해 주세요."},
            ],
        )
        if response.choices and response.choices[0].message.content:
            # 여러 줄 제안 분리
            suggestions = [s.strip("-• ").strip() for s in response.choices[0].message.content.strip().split("\n") if s.strip()]

        return suggestions


if __name__ == "__main__":
    agent = SuggestionAgent()
    resume = """
    저는 5년 경력의 소프트웨어 엔지니어로 Python과 JavaScript에 능숙합니다.
    웹 애플리케이션 및 머신러닝 프로젝트 경험이 있습니다.
    데이터 분석과 시각화 작업을 수행한 경험이 있으며, 팀 프로젝트에서 리더 역할을 맡았습니다.
    """
    summary = """
    AI 및 머신러닝 전문가를 찾고 있습니다.
    자연어 처리와 컴퓨터 비전 경험이 있는 분을 우대합니다.
    최신 딥러닝 프레임워크 활용 능력이 필요합니다.
    """
    print("개선 제안:")
    for idx, res in enumerate(agent.suggest(resume, summary), 1):
        print(res)
