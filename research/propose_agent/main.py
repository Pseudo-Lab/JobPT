import os
import json
import sys
from dotenv import load_dotenv
from modules.suggestion_agent import SuggestionAgent
from modules.utils import save_results

# 환경 변수 로드
load_dotenv()

# 고정된 이력서와 직무 요구사항
EXAMPLE_RESUME = """
저는 5년 경력의 소프트웨어 엔지니어로 Python과 JavaScript에 능숙합니다.
웹 애플리케이션 및 머신러닝 프로젝트 경험이 있습니다.
데이터 분석과 시각화 작업을 수행한 경험이 있으며, 팀 프로젝트에서 리더 역할을 맡았습니다.
TensorFlow와 PyTorch를 사용한 딥러닝 모델 개발 경험이 있습니다.
자연어 처리와 컴퓨터 비전 분야에서 여러 프로젝트를 진행했습니다.
"""

EXAMPLE_JOB_REQUIREMENTS = """
AI 및 머신러닝 전문가를 찾고 있습니다. 
자연어 처리와 컴퓨터 비전 경험이 있는 분을 우대합니다.
최신 딥러닝 프레임워크 활용 능력이 필요합니다.
팀 프로젝트 경험과 리더십이 있는 분을 선호합니다.
Python과 JavaScript에 능숙한 분을 찾습니다.
"""

# 고정된 타겟 줄 (2번 줄: 웹 애플리케이션 및 머신러닝 프로젝트 경험이 있습니다.)
TARGET_LINE_NUM = 2


def main():
    print("JobPT 이력서 개선 시스템")

    # 에이전트 초기화
    agent = SuggestionAgent()

    # 대화형 모드 실행
    interactive_mode(agent)


def interactive_mode(agent):
    """사용자 입력을 받아 처리하는 대화형 모드"""
    print("\n===== 대화형 모드 =====")
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.")

    # 이력서와 직무 요구사항 출력
    print("\n===== 예시 이력서 =====")
    resume_lines = EXAMPLE_RESUME.strip().split("\n")
    for i, line in enumerate(resume_lines, 1):
        if i == TARGET_LINE_NUM:
            print(f"{i}: {line} <-- 현재 작업 중인 줄")
        else:
            print(f"{i}: {line}")

    print("\n===== 예시 직무 요구사항 =====")
    job_lines = EXAMPLE_JOB_REQUIREMENTS.strip().split("\n")
    for i, line in enumerate(job_lines, 1):
        print(f"{i}: {line}")

    print(f"\n현재 {TARGET_LINE_NUM}번 줄을 개선하고 있습니다.")
    print(f"개선 요청은 '더 구체적으로 작성해줘'와 같이 입력하세요.")
    print(f"추천 요청은 '더 나은 내용을 추천해줘'와 같이 입력하세요.")
    target_line = resume_lines[TARGET_LINE_NUM - 1]
    print(f'대상 줄: "{target_line}"')

    while True:
        # 사용자 질문 입력 받기
        user_input = input("\n요청을 입력하세요: ")

        # 종료 조건 확인
        if user_input.lower() in ["exit", "quit"]:
            print("프로그램을 종료합니다.")
            break

        # 빈 입력 처리
        if not user_input.strip():
            print("요청을 입력해주세요.")
            continue

        # 사용자 입력 처리
        print("\n요청 처리 중...")

        try:
            # SuggestionAgent의 개선된 메서드 호출
            result = agent.improve_resume_line(line=target_line, request=user_input, resume_context=EXAMPLE_RESUME, job_requirements=EXAMPLE_JOB_REQUIREMENTS)

            if result["success"]:
                print("\n===== 응답 =====")
                print(f"원본 {TARGET_LINE_NUM}번 줄: {target_line}")
                print(result["response"])
            else:
                print("\n요청을 처리할 수 없습니다. 다시 시도해주세요.")
                print(f"오류: {result['response']}")
        except Exception as e:
            print(f"\n오류 발생: {str(e)}")
            print("다시 시도해주세요.")


if __name__ == "__main__":
    main()
