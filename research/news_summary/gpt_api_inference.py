import os
import pandas as pd
import openai

# 환경 변수에서 OpenAI API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")

def prompts(text):
      prompt = f"""Article: {text}
You will generate increasingly concise, entity-dense summaries of the above article. 

Repeat the following 2 steps 5 times. 

Step 1. Identify 1-3 informative entities (";" delimited) from the article which are missing from the previously generated summary. 
Step 2. Write a new, denser summary of identical length which covers every entity and detail from the previous summary plus the missing entities. 

A missing entity is:
- relevant to the main story, 
- specific yet concise (5 words or fewer), 
- novel (not in the previous summary), 
- faithful (present in the article), 
- anywhere (can be located anywhere in the article).

Guidelines:

- The first summary should be long (4-5 sentences, ~80 words) yet highly non-specific, containing little information beyond the entities marked as missing. Use overly verbose language and fillers (e.g., "this article discusses") to reach ~80 words.
- Make every word count: rewrite the previous summary to improve flow and make space for additional entities.
- Make space with fusion, compression, and removal of uninformative phrases like "the article discusses".
- The summaries should become highly dense and concise yet self-contained, i.e., easily understood without the article. 
- Missing entities can appear anywhere in the new summary.
- Never drop entities from the previous summary. If space cannot be made, add fewer new entities. 

Remember, use the exact same number of words for each summary.
Answer in JSON. The JSON should be a list (length 5) of dictionaries whose keys are "Missing_Entities" and "Denser_Summary".

Results:"""
      return prompt

def summarize_text(input_text, model="gpt-4o-mini"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompts(input_text)}
            ],
            max_tokens=2048,
            temperature=0.5
        )
        # 요약된 텍스트 반환
        summary = response['choices'][0]['message']['content']
        return summary

    except openai.error.OpenAIError as e:
        print(f"Error: {e}")
        return None


def process_csv(file_path, output_file_path, n):
    """
    상위 N개의 'description' 열을 요약하여 새로운 파일에 저장.

    Args:
        file_path (str): 입력 CSV 파일 경로.
        output_file_path (str): 출력 CSV 파일 경로.
        n (int): 처리할 행 개수. 기본값은 3.
    """
    try:
        # CSV 파일 읽기
        df = pd.read_csv(file_path)

        # 상위 N개 데이터 선택
        top_df = df.head(n).copy()

        # description 열 요약 추가
        print(f"Summarizing top {n} descriptions...")
        top_df['summary'] = top_df['description'].apply(lambda x: summarize_text(x) if isinstance(x, str) else None)

        # 결과 출력 및 저장
        print("=== Summary Results ===")
        print(top_df[['description', 'summary']])
        
        top_df.to_csv(output_file_path, index=False)
        print(f"Summarized top {n} descriptions saved to {output_file_path}")

    except Exception as e:
        print(f"Error processing CSV: {e}")



if __name__ == "__main__":
    input_csv = "news_data.csv"  # 입력 파일 경로
    output_csv = "summarized_news_data.csv"  # 출력 파일 경로

    # 환경 변수 확인
    if not openai.api_key:
        print("Error: OPENAI_API_KEY is not set in your environment variables.")
    else:
        process_csv(input_csv, output_csv, n=3)