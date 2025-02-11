import openai
import pandas as pd
import re
from openai import OpenAI
import os

# 2. 처리할 CSV 파일 리스트 (필요에 따라 파일 경로 수정)
csv_files = ["summarized_news_data_groq.csv", "summarized_news_data_grok.csv", "summarized_news_data_gpt-4o-mini.csv"]
csv_files = ["summarized_news_data_grok.csv", "summarized_news_data_gpt-4o-mini.csv"]

# 3. 각 CSV 파일에 대해 평가 수행
for csv_file in csv_files:
    print(f"Processing file: {csv_file}")
    # CSV 파일 읽기
    df = pd.read_csv(csv_file)

    evaluations = []  # 각 행의 전체 평가 결과 텍스트 저장
    average_scores = []  # 각 행의 추출한 평균 점수 저장

    # CSV 파일의 각 행에 대해 평가 수행
    for idx, row in df.iterrows():
        original_text = row["description"]
        summary_text = row["summary"]

        # 평가 프롬프트 구성 (평가 기준: coherence, consistency, fluency, relevance)
        prompt = f"""
다음은 원문 내용과 요약문입니다.

[원문]
{original_text}

[요약문]
{summary_text}

아래 평가 기준에 따라 요약문의 질을 평가해주세요.
평가 기준:
- coherence: 요약문의 논리적 연결성과 전개가 얼마나 일관성 있게 이어지는지 평가합니다.
- consistency: 요약문이 원문의 정보와 모순 없이 일관되게 작성되었는지 평가합니다.
- fluency: 요약문의 문장이 자연스럽고 읽기 쉬운지 평가합니다.
- relevance: 요약문이 원문의 핵심 정보를 얼마나 잘 반영하고 있는지 평가합니다.

각 기준별로 1점(매우 부족)부터 5점(매우 우수)까지 점수를 매기고, 각 항목에 대한 간단한 설명도 덧붙여 주세요.
평가 결과 마지막 줄에는 각 점수의 평균을 소수점 한 자리까지 계산하여 아래와 같이 표기해 주세요.
예시 출력:
- coherence: 4점 (이유: …)
- consistency: 5점 (이유: …)
- fluency: 4점 (이유: …)
- relevance: 3점 (이유: …)
평균 점수: 4.0
        """

        try:
            # OpenAI ChatCompletion API 호출
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "당신은 텍스트 요약 평가를 전문으로 하는 평가자입니다."}, {"role": "user", "content": prompt}],
                max_tokens=4096,
            )
            evaluation_result = response.choices[0].message.content.strip()
        except Exception as e:
            evaluation_result = f"Error: {str(e)}"

        evaluations.append(evaluation_result)

        # 정규 표현식을 사용하여 "평균 점수: X.X" 형식의 값을 추출
        avg_match = re.search(r"평균\s*점수\s*[:：]\s*(\d+(\.\d+)?)", evaluation_result)
        if avg_match:
            avg_score = float(avg_match.group(1))
        else:
            avg_score = None  # 평균 점수를 찾지 못하면 None 처리
        average_scores.append(avg_score)

        print(f"File: {csv_file}, Row {idx} evaluation:\n{evaluation_result}\n{'-'*50}")

    # 평가 결과와 평균 점수를 데이터프레임에 추가
    df["evaluation"] = evaluations
    df["average_score"] = average_scores

    # 각 CSV 파일의 평가 결과를 새로운 파일로 저장 (예: evaluated_data1.csv)
    output_filename = f"evaluated_{csv_file}"
    df.to_csv(output_filename, index=False)
    print(f"평가 완료! '{output_filename}' 파일에 결과가 저장되었습니다.\n{'='*70}\n")
