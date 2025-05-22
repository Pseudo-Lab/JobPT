"""
입력 경로에 들어있는 csv 파일들을 전처리한 다음
Pinecone에 업로드하고 BM25 retriever를 생성하는 코드입니다.
"""

import os
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_chroma import Chroma
from configs import JD_PATH, COLLECTION, DB_PATH,PINECONE_INDEX
from langchain_pinecone import PineconeVectorStore
from langchain_community.retrievers import BM25Retriever
import string
from uuid import uuid4
import pickle
from pathlib import Path
from tqdm import tqdm
import argparse

from pinecone import Pinecone, ServerlessSpec
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

from dotenv import load_dotenv
import pandas as pd

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def preprocess(df):
    df.dropna(subset=['description', 'is_remote'], inplace=True)
    df = df.reset_index(drop=True)
    return df

def clean_tokens(text: str):
    """공백 기준 토큰화 후 특수문자 제거·소문자 변환"""
    tokens = text.split()                       # ① 공백 기준 분리
    cleaned = []
    for tok in tokens:
        # ② 토큰 앞뒤 특수문자 제거  ( ###Job**  →  Job )
        tok = tok.strip(string.punctuation)
        # ③ 소문자 변환
        tok = tok.lower()
        # ④ 빈 토큰·순수 특수문자 토큰은 건너뛰기
        if tok and not all(ch in string.punctuation for ch in tok):
            cleaned.append(tok)
    return cleaned


def load_emb_model(cache=True):
    """embedding model을 로드하고 캐싱하는 함수입니다."""
    embedding = OpenAIEmbeddings()

    # Embedding model 캐싱하기
    if cache:
        cache_path = "./cache/"
        store = LocalFileStore(cache_path)
        cached_embedder = CacheBackedEmbeddings.from_bytes_store(embedding, store, namespace=embedding.model)
        return cached_embedder
    return embedding


def set_splitter(emb_model):
    """splitter를 셋업하는 함수입니다."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100, separators=["#","##,""###","####","**","---","\r\n","\n\n", "\n", "\t", " ", ""])
    return text_splitter


def get_chunks(df, text_splitter):
    total_chunks = []
    for i, desciption in enumerate(df["description"]):
        meta_data = [df.iloc[i].to_dict()]
        unique_id = str(uuid4())    #랜덤 id 생성
        ## RRF를 위해 id를 메타데이터로 추가
        ## 한 문서에 여러 개의 chunk가 생기기 때문에 vectorDB의 id로 추가하면 중복되서 사라진다
        meta_data[0]["id"] = unique_id

        chunks = text_splitter.create_documents([desciption], meta_data)
        total_chunks.extend(chunks)
    return total_chunks


def insert_chunks(total_chunks, collection: str):
    index_name = collection
    if pc.has_index(index_name):
        print("인덱스가 이미 존재합니다")
        index = pc.Index(index_name)
        ## 데이터가 남아있을때 데이터 제거
        if len(index.describe_index_stats()["namespaces"]) > 0:
            index.delete(delete_all=True, namespace="")
    else:
        ## openAI의 embedding dimension과 동일
        ## dimension은 embedding model을 변경한다면 설정하기
        pc.create_index(index_name, dimension=1536, metric="cosine",
            spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ) ) #서버리스 인덱스 생성
        index = pc.Index(index_name)

    vector_store = PineconeVectorStore(index=index, embedding=emb_model)
    batch_size = 100           # 한 번에 보낼 문서 수
    total = len(total_chunks)    # 전체 문서 개수
    for start in tqdm(range(0, total, batch_size), desc="Upserting to Pinecone"):
        end = start + batch_size
        batch_docs = total_chunks[start:end]
        vector_store.add_documents(documents=batch_docs)
    # vector_store.add_documents(documents=total_chunks)
    print("Pinecone DB 세팅 완료")
    # pinecone와 같은 메타데이터를 사용해 rank fusion하므로 무조건 동시에 생성할 것
    bm25retriever = BM25Retriever.from_documents(total_chunks, preprocess_func=clean_tokens, k=10)
    SAVE_PATH = Path("bm25_retriever.pkl")
    with SAVE_PATH.open("wb") as f:
        pickle.dump(bm25retriever, f)
    print("BM25 retriever 세팅 완료")

    return None



def classify_jobpype(df):
    remove_index = []
    for idx, data in df.iterrows():
        job_type = data["job_type"]
        if "fulltime" in job_type:
            label="fulltime"
        elif "parttime" in job_type:
            label="parttime"
        elif "contract" in job_type:
            label="fulltime"
        elif "internship" in job_type:
            label="fulltime"
        else:
            remove_index.append(idx)

        df.at[idx, "job_type"] = label

    for index in remove_index:
        print(f"Removing index: {index}")
        df.drop(index, inplace=True)
        
    return df





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd_folder",type=str, help="JD csv 폴더 경로", default="../research/Retrieval/updated_jd")
    jd_folder = parser.parse_args().jd_folder
    # collection_name = PINECONE_INDEX        #in system/configs.py, (jd-dataset)
    collection_name = "test-index"  #phase1 vectorDB 인덱스


    full_paths = []
    for jd_path in os.listdir(jd_folder):
        full_paths.append(os.path.join(jd_folder, jd_path))

    all_dfs = []
    for path in full_paths:
        df = pd.read_csv(path)
        df["location"] = path.split("/")[-1].split("_")[0]
        all_dfs.append(df)
    # 하나의 DataFrame으로 병합
    merged_df = pd.concat(all_dfs, ignore_index=True)
    # print(f"location example: {merged_df['location'][0]}")

    #description 기준 중복값 제거
    merged_df_dedup = merged_df.drop_duplicates(subset="description")
    print(f"중복 제거 전 description 개수: {len(merged_df)}")
    print(f"중복 제거 후 description 개수: {len(merged_df_dedup)}")
    # job_type 분류
    merged_df_dedup = classify_jobpype(merged_df_dedup)
    max_len = 10000
    merged_df_dedup = merged_df_dedup[merged_df_dedup['description'].apply(lambda x: len(x) <= max_len if isinstance(x, str) else True)]
    print(f"최대 길이 {max_len} 이하 description 개수: {len(merged_df_dedup)}")

    final_df = preprocess(merged_df_dedup)
    
    emb_model = load_emb_model()
    total_chunks = get_chunks(final_df, set_splitter(emb_model))   # semantic chunking, langchain document list 반환
    ### research/Retrieval/pinecone_upsert.ipynb의 결과와 동일한 갯수의 청크가 생성되었는지 확인
    print("청크 개수: ", len(total_chunks))      
    insert_chunks(total_chunks, collection_name)  # 청크를 DB에 저장하는 함수 호출