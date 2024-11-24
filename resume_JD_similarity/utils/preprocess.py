import os
import pandas as pd

def save_dataframe_to_csv(folder_path, file_name, df):
    os.makedirs(folder_path, exist_ok=True)
    
    # Construct the full file path
    file_path = os.path.join(folder_path, file_name)
    
    # Save the DataFrame to CSV
    df.to_csv(file_path, index=False)
    
    print(f"DataFrame saved to {file_path}")

def preprocess(data_path):
    JD_csv = pd.read_csv(data_path)

    # column drop - interval, min_amount, max_amount, currency, num_urgent_words, benefits, emails
    JD_csv.drop(['interval', 'min_amount', 'max_amount', 'currency', 'num_urgent_words', 'benefits', 'emails'], axis=1, inplace=True)

    # description null인 행만 지우기
    JD_csv.dropna(subset=['description', 'is_remote'], inplace=True)

    # is_remote null 값 처리 - description을 llm에 전달한 후 job_type 넣기
    JD_csv['job_type'] = JD_csv['job_type'].fillna('fulltime')
    JD_csv['index'] = [f"job_{i}" for i in range(len(JD_csv))]
    JD_csv = JD_csv.reset_index(drop=True)
    JD_csv.drop(columns=['job_url', 'site'], inplace=True)
    
    # save JD_csv
    folder = "./data/preprocessed"
    file_name = f"{data_path.split('/')[-1]}"
    
    # Save the DataFrame
    save_dataframe_to_csv(folder, file_name, JD_csv)
    return JD_csv