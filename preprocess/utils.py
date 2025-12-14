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
from datetime import datetime
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
    
    ### 여기까지는 csv가 컬럼명을 그대로 가지고 온다 null 값만 chk해서 메타데이터 그대로 사용
    for i, desciption in enumerate(sentences):
        meta_data = [{"job_url": table.iloc[i]["url"],
        "company": table.iloc[i]["company_name"],
        "location": table.iloc[i]["location"],
        "experience_requirement": table.iloc[i]["experience_requirement"],
        "summary": table.iloc[i]["summary"],
        "deadline": table.iloc[i]["deadline"]
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


def make_documents_from_csv(df, text_column="text"):
    """
    CSV 데이터프레임을 Document 리스트로 변환합니다.
    (청킹 없이 텍스트 그대로 사용 - 팀원이 직접 청킹한 데이터용)
    
    Args:
        df: pandas DataFrame (CSV에서 읽어온 데이터)
        text_column: 임베딩할 텍스트가 있는 컬럼명 (기본값: "text")
    
    Returns:
        documents: List[Document] - Document 리스트
    
    Example:
        >>> df = pd.read_csv("data.csv")
        >>> docs = make_documents_from_csv(df, text_column="description")
    """
    from langchain_core.documents import Document
    
    if text_column not in df.columns:
        raise ValueError(f"'{text_column}' 컬럼이 데이터프레임에 없습니다. 사용 가능한 컬럼: {list(df.columns)}")
    
    documents = []
    metadata_columns = [col for col in df.columns if col != text_column]
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Document 생성중"):
        text = row[text_column]
        
        # text가 비어있으면 스킵
        if pd.isna(text) or not str(text).strip():
            print(f"⚠️ Row {idx}: 텍스트가 비어있어 스킵합니다.")
            continue
        
        # 메타데이터 생성 (text_column 제외한 나머지 컬럼들)
        # Pinecone에서 허용하는 타입만 포함: str, int, float, bool, list[str/int/float]
        meta_data = {}
        for col in metadata_columns:
            value = row[col]
            
            # NaN이나 None은 빈 문자열로 변환
            if pd.isna(value) or value is None:
                meta_data[col] = ""
            # 숫자 타입은 그대로 유지
            elif isinstance(value, (int, float, bool)):
                meta_data[col] = value
            # 나머지는 문자열로 변환
            else:
                meta_data[col] = str(value)
        
        doc = Document(page_content=str(text), metadata=meta_data)
        documents.append(doc)
    
    print(f"✅ 원본 데이터 개수: {len(df)}")
    print(f"✅ 생성된 Document 개수: {len(documents)}")
    
    return documents


def check_deadline(deadline_str):
    # 날짜 형식에 맞게 변환
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
    except ValueError:
        return False  # 파싱 불가(상시채용 등) 시 False 반환
    ### 현재시간보다 미래일시 True, 과거일시 False, 최종적으로 False는 모두 제거해야함
    return deadline > datetime.now()

def delete_vectors(index, ids):
    """
    Pinecone에서 벡터 삭제
    
    Args:
        index: Pinecone index 객체
        ids: 단일 ID(str) 또는 ID 리스트(list)
    
    Returns:
        삭제된 ID 개수
    """
    # 단일 ID면 리스트로 변환
    if isinstance(ids, str):
        ids = [ids]
    
    # 배치 삭제 (한 번에 최대 1000개)
    batch_size = 1000
    deleted_count = 0
    
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        index.delete(ids=batch)
        deleted_count += len(batch)
    
    print(f"✅ {deleted_count}개의 벡터가 삭제되었습니다.")
    return deleted_count





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


def get_all_ids(index):
    all_ids = []
    for batch in index.list():
        for vid in batch:
            all_ids.append(vid)
    return all_ids

def get_metadata_by_id(index, vid):
    resp = index.fetch(ids=[vid])
    vectors = resp.vectors[vid]
    metadata = vectors.metadata
    return metadata  # 없으면 None


class Upstage:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.upstage.ai/v1"
        )

    async def summary(self, messages: list[dict]):
        response = self.client.chat.completions.create(
            model="solar-pro2",
            messages=messages,
            max_tokens=2048,
            temperature=0.3,
            frequency_penalty=0.1,
            top_p=0.9

        )
        return response.choices[0].message.content