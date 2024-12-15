import pandas as pd
import json
import glob

# answer.json 파일 읽기
with open("t5_results/answer.json", "r", encoding="utf-8") as f:
    answer_data = json.load(f)

# answer.json의 summary 열을 answer로 변환
answer_df = pd.DataFrame(answer_data).rename(columns={'summary': 'answer'})[['article_id', 'answer']]

# Excel 파일 생성
with pd.ExcelWriter("summary_results.xlsx", engine="xlsxwriter") as writer:
    # 모든 JSON 파일 찾기
    for file in glob.glob("t5_results/*.json"):
        # answer.json 파일은 스킵
        if "answer.json" in file:
            continue
        
        # 파일 이름에서 확장자 제외한 부분을 시트 이름으로 사용
        sheet_name = file.split("/")[-1].replace(".json", "")
        
        # JSON 파일 읽기
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # JSON 데이터를 DataFrame으로 변환
        df = pd.DataFrame(data)
        
        # answer_df와 article_id를 기준으로 병합하여 answer 열 추가
        df = pd.merge(df, answer_df, on="article_id", how="left")
        
        # Excel 파일에 시트로 저장
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel 파일이 성공적으로 생성되었습니다.")