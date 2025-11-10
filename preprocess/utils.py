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
from openai import OpenAI # openai==1.52.2

### 전역변수 가져와서 넣기
# table = pd.read_csv("/home/yhkim/code/JobPT/backend/get_similarity/data/korean_jd_105.csv")



def build_embedding_sentence(table):
    """
    각 row(텍스트, 메타데이터)에서 임베딩을 위한 문장을 생성합니다.
    청킹 전 메타데이터도 embedding 영역에추가 아래 보이는 3개 영역을 나누는 구분자 추가하여 문장 생성
    입력: table(pandas DataFrame)
    출력: table(pandas DataFrame)
    """
    table["sentence"] = table.apply(lambda x: "<chunk_sep>".join([x["description"],\
    f"\n\n하는일: {x['main_work']}\n\n자격요건: {x['qualification']}",\
    f"\n\nurl: {x['url']}\n\njob_name: {x['job_name']}\n\ncompany_name: {x['company_name']}\n\nwelfare: {x['welfare']}"]), axis=1)
    return table

def make_chunks(sentences, table):
    """
    청킹&구분자 제거 및 메타데이터 추출
    입력: sentences(list), table(pandas DataFrame)
    출력: total_chunks(List(Document))
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100, separators=["<chunk_sep>","\r\n","\n\n", "\n", "\t", " ", ""])
    total_chunks = []
    for i, desciption in enumerate(sentences):
        meta_data = [{"job_url": table.iloc[i]["url"],
        "company": table.iloc[i]["company_name"],
        "location": table.iloc[i]["location"],
        "experience_requirement": table.iloc[i]["experience_requirement"],
        "summary": table.iloc[i]["summary"]
        }]
        chunks = text_splitter.create_documents([desciption], meta_data)

        for chunk in chunks:
            chunk.page_content = chunk.page_content.replace("<chunk_sep>","")
            # 빈 chunk는 추가하지 않음
            if chunk.page_content and chunk.page_content.strip():
                total_chunks.append(chunk)
            else:
                print(f"⚠️ Chunk {i} is empty, skipping...")
    return total_chunks




def preprocess(table):
    print("전처리를 시작합니다")
    table = table.drop_duplicates()
    table = build_embedding_sentence(table)

    sentences = table["sentence"]
    total_chunks = make_chunks(sentences, table)
    print(f"문장처리&청킹 완료")
    print(f"원본 데이터 개수: {len(table)}")
    print(f"청크 개수: {len(total_chunks)}")

    return total_chunks




class Upstage:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1"
        )

    def summary(self, messages: list[dict]):
        response = self.client.chat.completions.create(
            model="solar-pro2",
            messages=messages,
            max_tokens=2048,
            temperature=0.3,
            frequency_penalty=0.1,
            top_p=0.9

        )
        return response.choices[0].message.content