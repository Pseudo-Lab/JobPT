import os
from dotenv import load_dotenv
from modules.suggestion_agent import SuggestionAgent
from modules.review_llm import ReviewLLM

load_dotenv()


def main():
    print("JobPT Document Processing System")
    suggestion_agent = SuggestionAgent()
    review_llm = ReviewLLM()

    # 요약 결과

    # 요약 Agent의 input 형식으로 받기
    document = """
인공지능(AI)은 인간의 지능을 모방하여 학습, 문제 해결, 패턴 인식 등을 수행하는 기술입니다.
머신러닝은 AI의 하위 분야로, 데이터로부터 학습하여 예측이나 결정을 내리는 알고리즘을 개발합니다.
딥러닝은 머신러닝의 한 종류로, 인간 뇌의 신경망 구조를 모방한 인공 신경망을 사용합니다.
    """

    suggestion_results = suggestion_agent.run(document)
    print("\n===== Initial Suggestion Agent Results =====")
    print(suggestion_results)
    while True:
        review_results = review_llm.run(suggestion_results["modified_doc"])
        print("\n===== Review LLM Results =====")
        print(review_results)
        if "no further action required" in review_results["jd_report"].lower():
            print("\nReview LLM has determined no further action is needed.")
            break
        if "<finish>" in review_results["jd_report"]:
            print("\nReview LLM has signaled completion with <finish>.")
            break
        suggestion_results = suggestion_agent.run(review_results["jd_report"])
        print("\n===== Refined Suggestions =====")
        print(suggestion_results)


if __name__ == "__main__":
    main()
