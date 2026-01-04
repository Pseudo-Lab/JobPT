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


async def summarize_chapter(k, content):
    request = [
        {"role": "system", "content": prompts["chapter_summary_prompt"]["system"]},
        {"role": "user", "content": f"다음 항목을 요약해 주세요\n{k}:{content}"}
    ]
    result = await model.summary(request)
    return k, result.replace("\n\n", "\n")



def get_description_before_main_work(row):
    description = str(row["description"])
    main_work = str(row["main_work"])
    if main_work and main_work in description:
        parts = description.split(main_work)
        return parts[0].strip()
    return description.strip()  # main_work가 없거나 포함되어 있지 않다면 전체 반환
### 본문구성
def format_jd_to_prompt_short(jd_data):
    items = {k: v for k, v in dict(jd_data).items() if str(v).strip() not in ('', 'nan', 'NaN', 'None') and 
             k in ['title', 'company_name', "location", "experience_requirement", "company_description", "main_work", "qualification", "preferences", "welfare"]}
    return items

async def summarize_chapter_batch(batch_df_texts):
    tasks = [summarize_chapter(k, v) for k, v in batch_df_texts.items()]
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
    df = df.iloc[:10]    ### 테스트용
    df["deadline"] = df["deadline"].apply(parse_deadline)
    df["company_description"] = df.apply(get_description_before_main_work, axis=1)
    batch_df_texts = [format_jd_to_prompt_short(row) for i, row in df.iterrows()]
    
    for item in batch_df_texts:
        if "company_description" in item:
            item["회사소개"] = item["company_description"]
        if "main_work" in item:
            item["주요업무"] = item["main_work"].replace("주요업무 ", "")
        if "qualification" in item:
            item["자격요건"] = item["qualification"].replace("자격요건 ", "")
        if "preferences" in item:
            item["우대사항"] = item["preferences"].replace("우대사항 ", "")
        if "welfare" in item:
            item["혜택및복지"] = item["welfare"].replace("혜택 및 복지 ", "")

    # 모든 태스크 생성
    all_tasks = []
    for item in batch_df_texts:
        for k in ["회사소개", "주요업무", "자격요건", "우대사항", "혜택및복지"]:
            if k in item:
                all_tasks.append(summarize_chapter(k, item[k]))
    
    # 비동기 실행 (30개씩 배치 처리)
    batch_size = 30
    results = []
    print(f"총 {len(all_tasks)}개 항목 요약 중... (배치 크기: {batch_size})")
    
    async def run_batch(tasks):
        return await asyncio.gather(*tasks)
    
    for start_idx in tqdm(range(0, len(all_tasks), batch_size), desc="배치 처리"):
        end_idx = min(start_idx + batch_size, len(all_tasks))
        batch_tasks = all_tasks[start_idx:end_idx]
        batch_results = asyncio.run(run_batch(batch_tasks))
        results.extend(batch_results)
        print(f"배치 {start_idx//batch_size + 1} 완료: {start_idx}~{end_idx-1} ({len(batch_results)}개)")
    
    # 결과를 각 행별로 재구성
    summaries = []
    chapters = ["회사소개", "주요업무", "자격요건", "우대사항", "혜택및복지"]
    for i in range(len(batch_df_texts)):
        summary_parts = ["#[{company_name}]{title}".format(company_name=batch_df_texts[i]["company_name"], title=batch_df_texts[i]["title"])]
        for j, chapter in enumerate(chapters):
            if chapter in batch_df_texts[i]:
                idx = i * len(chapters) + j
                if idx < len(results):
                    k, content = results[idx]
                    summary_parts.append(f"## {k}\n{content}")
        summaries.append("\n\n".join(summary_parts))
    
    df["summary"] = summaries
    df.to_csv(output_path, index=False)
    print(f"저장 완료: {output_path}")