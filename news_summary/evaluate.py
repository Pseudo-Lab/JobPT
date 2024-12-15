import pandas as pd
from rouge_score import rouge_scorer

# 엑셀 파일 읽기
file_path = "summary_results.xlsx"  # 실제 파일 경로에 맞춰 수정하세요.
sheet_names = ["google_t5-small", "google_t5-base", "google_t5-3b", "finetuned-summarize-news", "google-t5-large"]

# ROUGE 스코어 계산기 설정
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

# 새로운 엑셀 파일에 각 시트 저장
with pd.ExcelWriter("summaries_with_rouge_scores.xlsx") as writer:
    for sheet_name in sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # ROUGE 스코어를 저장할 빈 리스트 생성
        rouge1_scores = []
        rouge2_scores = []
        rougeL_scores = []
        
        # 각 행의 summary와 answer를 비교하여 ROUGE 스코어 계산
        for index, row in df.iterrows():
            summary = row["summary"]
            answer = row["answer"]
            
            # ROUGE 스코어 계산
            scores = scorer.score(answer, summary)
            
            # 각 스코어의 fmeasure 값을 리스트에 추가
            rouge1_scores.append(scores["rouge1"].fmeasure)
            rouge2_scores.append(scores["rouge2"].fmeasure)
            rougeL_scores.append(scores["rougeL"].fmeasure)

        # 계산한 ROUGE 스코어를 새로운 컬럼으로 추가
        df["rouge1"] = rouge1_scores
        df["rouge2"] = rouge2_scores
        df["rougeL"] = rougeL_scores
        
        # 해당 시트를 새로운 엑셀 파일에 저장
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
print("ROUGE 스코어가 추가된 파일이 'summaries_with_rouge_scores.xlsx'로 저장되었습니다.")