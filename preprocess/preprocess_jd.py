### vdb 업데이트를 위한 크롤링된 csv 파일 chk
import pandas as pd
import os
import sys
import time
import requests
import json
import re
import random


import pandas as pd
import textwrap

from dotenv import load_dotenv
import pandas as pd
import os
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
import argparse
import yaml
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio
from utils import *

prompts = yaml.safe_load(open("prompts.yaml", "r", encoding="utf-8"))
model = Upstage(api_key=os.getenv("UPSTAGE_API_KEY"))


MESSAGES = [
{"role": "system", "content": prompts["prompts_ver1"]["system"]},
# {"role": "user", "content": prompts["prompts_ver1"]["user"].format(jd=df.iloc[i]["description"])}
]

def parse_deadline(x):
    x = str(x).strip()
    try:
        dt = datetime.strptime(x, "%Y.%m.%d")
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    except:
        pass
    return (datetime.now() + relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0)


async def summarize_batch(df, start_idx, end_idx):
    requests = [
        [
            {"role": "system", "content": prompts["prompts_ver1"]["system"]},
            {"role": "user", "content": prompts["prompts_ver1"]["user"].format(jd=df.iloc[i]["description"])}
        ]
        for i in range(start_idx, end_idx)
    ]
    tasks = [model.summary(req) for req in requests]
    return await asyncio.gather(*tasks)





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="입력 CSV 파일 경로")
    args = parser.parse_args()

    input_path = args.input_file
    base, ext = os.path.splitext(input_path)
    mmdd = datetime.now().strftime("%m%d")
    output_path = f"{base}_preprocessed_{mmdd}{ext}"

    df = pd.read_csv(input_path)
    # df = df.iloc[:10]    ### 테스트용
    df["deadline"] = df["deadline"].apply(parse_deadline)

    batch_size = 5
    summaries = []
    for i in tqdm(range(0, len(df), batch_size), desc="JD 요약 중"):
        end_idx = min(i + batch_size, len(df))
        batch_result = asyncio.run(summarize_batch(df, i, end_idx))
        summaries.extend(batch_result)
    
    df["summary"] = summaries
    df.to_csv(output_path, index=False)
    print(f"저장 완료: {output_path}")