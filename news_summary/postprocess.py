import csv
import re
import sys
import pandas as pd

csv.field_size_limit(sys.maxsize)


def clean_prediction_column(input_file, output_file):
    # CSV 파일 읽기
    df = pd.read_csv(input_file, encoding="utf-8")

    # split을 사용해 </example>와 <summary>로 텍스트 추출
    def extract_summary(text):
        # 먼저 </example>로 split하여 필요한 부분을 가져옴
        # <summary>로 다시 split하여 필요한 텍스트만 추출
        print(text.split("Assistant:"))
        text = text.split("Assistant:")
        text = text[-1]
        return text

    df["prediction"] = df["prediction"].apply(extract_summary)
    print(df["prediction"])
    # 결과를 새로운 CSV 파일로 저장
    df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"{output_file} 파일에 후처리된 데이터를 저장했습니다.")


# 파일 경로 예시

input_file = "Qwen2.5-7B-Instruct.csv"
output_file = "Qwen2.5-7B-Instruct_cleaned.csv"

# 함수 호출
clean_prediction_column(input_file, output_file)
