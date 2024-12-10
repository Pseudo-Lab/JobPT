import pandas as pd

def preprocess(data_path):
    JD_csv = pd.read_csv(data_path)

    # column drop - interval, min_amount, max_amount, currency, num_urgent_words, benefits, emails
    JD_csv.drop(['interval', 'min_amount', 'max_amount', 'currency', 'num_urgent_words', 'benefits', 'emails'], axis=1, inplace=True)

    # description null인 행만 지우기
    JD_csv.dropna(subset=['description', 'is_remote'], inplace=True)

    # is_remote null 값 처리 - description을 llm에 전달한 후 job_type 넣기
    JD_csv['job_type'] = JD_csv['job_type'].fillna('fulltime')
    JD_csv = JD_csv.reset_index(drop=True)
    JD_csv.drop(columns=['site'], inplace=True)

    return JD_csv