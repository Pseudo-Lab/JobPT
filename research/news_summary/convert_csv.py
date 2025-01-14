import pandas as pd
import json
import glob

# 모든 JSON 파일에서 데이터를 읽고 저장할 리스트 초기화
data_frames = []

# 모든 JSON 파일 읽기
path = "t5_results"
for file in glob.glob(f"{path}/*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
        # 파일 이름을 추출하여 열 이름에 그대로 사용 (예: google_t5-base, google_t5-large 등)
        file_name = file.split("/")[-1].replace(".json", "")
        
        # DataFrame으로 변환하고 필요한 열 선택
        df = pd.DataFrame(data)
        
        # 중복 article 제거를 위해 첫 파일만 article 포함
        if not data_frames:  # 첫 번째 파일인 경우
            data_frames.append(df[['article_id', 'article']])
        
        # 이후 파일들에 대해서는 article 컬럼 제외하고 파일명 컬럼 추가
        df = df[['article_id', 'summary']].rename(columns={'summary': file_name})
        data_frames.append(df)

# article_id를 기준으로 병합하여 하나의 DataFrame으로 생성
merged_df = data_frames[0]
for df in data_frames[1:]:
    merged_df = pd.merge(merged_df, df, on="article_id", how="outer")

# 결과를 CSV로 저장
merged_df.to_csv("merged_articles.csv", index=False, encoding="utf-8")

print("병합된 CSV 파일이 성공적으로 생성되었습니다.")