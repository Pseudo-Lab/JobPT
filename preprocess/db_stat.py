from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
import pandas as pd

from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_upstage import UpstageEmbeddings
from langchain_upstage import UpstageEmbeddings
from tqdm import tqdm
import yaml

from utils import *

load_dotenv(dotenv_path="../backend/.env")
prompts = yaml.safe_load(open("prompts.yaml", "r", encoding="utf-8"))

### Summarizer model
model = Upstage(api_key=os.getenv("UPSTAGE_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
collection = "korea-jd-test"



app = FastAPI()
def check_index(collection: str="korea-jd-test"):
    """
    인덱스 존재 여부를 조회합니다.
    """
    index_name = collection
    if pc.has_index(index_name):
        return {"message": True}
    else:
        return {"message": False}



@app.get("/list_indexes")
async def list_indexes():
    """
    현재 존재하는 모든 Pinecone 인덱스의 이름과 개수를 조회합니다.
    
    return: 
        - total_count: 전체 인덱스 개수
        - indexes: 인덱스 이름 리스트
    """
    try:
        indexes = pc.list_indexes()
        index_names = [index.name for index in indexes]
        
        return {
            "total_count": len(index_names),
            "indexes": index_names
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"인덱스 목록 조회 실패: {str(e)}"}
        )


@app.get("/stat")
async def stat(collection: str="korea-jd-test"):
    """
    index의 상태를 조회합니다.

    parameter:
        collection: 인덱스 이름
    return: 인덱스 상태
        [vector_count]에 표기되는 백터 개수는 데이터 개수가 아니라 청킹이 완료된 백터 개수입니다.
    """
    index_name = collection
    result = check_index(collection)
    if result["message"]:
        index = pc.Index(index_name)
        stat = index.describe_index_stats()
        stat = stat.to_dict()
        return stat
    else:
        return {"message": "인덱스가 존재하지 않습니다"}


@app.get("/check_unique_columns")
async def check_unique_column(file: UploadFile,):
    """
    데이터프레임의 고유 컬럼을 조회합니다.
    ### 추후 구현 예정
    """
    uploaded_file = file.file
    df = pd.read_csv(uploaded_file)





@app.get("/create_index")
async def create_index(index_name: str = "index-name-for-create", dimension: int=4096):
    """
    Pinecone 인덱스를 생성하는 API
    """
    try:
        # 인덱스 생성
        pc.create_index(
            index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        # 생성된 인덱스 객체 로드
        return {
            "index_name": index_name,
            "status": "success",
            "detail": "Index created successfully."
        }
    except Exception as e:
        # Pinecone 에러 메시지를 그대로 전달
        return {
            "index_name": index_name,
            "status": "error",
            "detail": str(e)
        }

@app.get("/drop_index")
async def drop_index(collection: str="index-name-for-drop"):
    """
    인덱스를 삭제합니다.
    """
    try:
        index_name = collection
        pc.delete_index(name=index_name)
        return {
            "index_name": index_name,
            "status": "success",
            "detail": "Index deleted successfully."
        }
    except Exception as e:
        return {
            "index_name": index_name,
            "status": "error",
            "detail": str(e)
        }


# @app.post("/upsert_data")
# async def upsert_jd(file: UploadFile, collection: str="korea-jd-dev"):
#     """
#     CSV를 업로드하고 Pinecone에 저장합니다.
#     """
#     if not file.filename.endswith('.csv'):
#         return JSONResponse(
#             status_code=400, 
#             content={"message": "CSV 파일만 업로드할 수 있습니다."}
#         )

#     try: 
#         ### 요약전 인덱스 부터 chk
#         index_name = collection
#         result = check_index(collection)
#         index = pc.Index(index_name)

#         uploaded_file = file.file
#         df = pd.read_csv(uploaded_file)





@app.post("/upsert_jd")
async def update_index(file: UploadFile, collection: str="korea-jd-dev"):
    """
    - korea-jd-dev: 개발용
    - korea-jd-prod: 배포용

    """
    if not file.filename.endswith('.csv'):
        
        # CSV 파일이 아닌 경우 오류 처리
        return JSONResponse(
            status_code=400, 
            content={"message": "CSV 파일만 업로드할 수 있습니다."}
        )
    try: 
        ### 요약전 인덱스 부터 chk
        index_name = collection
        result = check_index(collection)
        index = pc.Index(index_name)
        ids = get_all_ids(index)
        url_set = set()
        date_dicts = {}
        for id in tqdm(ids, desc="Getting URLs from Pinecone"):
            row = get_metadata_by_id(index, id)
            url_set.add(row["job_url"])
            date_dicts[id] = row["deadline"]
            # url_set.add(get_metadata_by_id(index, id)["job_url"])
        print(url_set)
        if result == False:
            raise ValueError("Index check failed: result is False")

        uploaded_file = file.file
        df = pd.read_csv(uploaded_file)
        print(f"📊 CSV에서 읽은 데이터: {len(df)}개")
        print(f"📊 Pinecone에 있는 URL: {len(url_set)}개")
        
        # INSERT_YOUR_CODE
        # df["url"] 컬럼에서 url_set에 존재하는 url이 있는 행 제거
        before = len(df)
        df = df[~df["url"].isin(url_set)].reset_index(drop=True)
        removed = before - len(df)
        after = len(df)
        
        print(f"📊 처리 전: {before}개")
        print(f"📊 처리 후: {after}개")
        print(f"📊 제거된 행: {removed}개")

        delete_ids = []
        for k, v in date_dicts.items():
            if check_deadline(v)==False:
                delete_ids.append(k)
        delete_vectors(index, delete_ids)
        print(f"✅ {len(delete_ids)}개의 벡터가 삭제되었습니다.")

        total_chunks = preprocess(df)

        # index = pc.Index(index_name)

        # emb_model = OpenAIEmbeddings()
        emb_model = UpstageEmbeddings(model="solar-embedding-1-large")

        vector_store = PineconeVectorStore(index=index, embedding=emb_model)

        ### 데이터가 남아있을때 데이터 제거(소량일때만 사용), 추후 모듈화
        # if len(index.describe_index_stats()["namespaces"]) > 0:
        #     index.delete(delete_all=True, namespace="")

        ### 파인콘 API로 한번에 대용량 update가 불가능하여 배치처리
        total = len(total_chunks)
        batch_size = 100
        for start in tqdm(range(0, total, batch_size), desc="Upserting to Pinecone"):
            end = start + batch_size
            batch_docs = total_chunks[start:end]
            # print(batch_docs)
            vector_store.add_documents(documents=batch_docs)
        return JSONResponse(
            status_code=200, 
            content={"message": "인덱스가 업데이트되었습니다"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"message": str(e)}
        )


@app.post("/upsert_custom_csv")
async def update_index(file: UploadFile, collection: str="test-custom-index"):
    """
    - korea-jd-dev, korea-jd-prod 사용불가

    """
    if not file.filename.endswith('.csv'):
        
        # CSV 파일이 아닌 경우 오류 처리
        return JSONResponse(
            status_code=400, 
            content={"message": "CSV 파일만 업로드할 수 있습니다."}
        )
    try: 
        ### 요약전 인덱스 부터 chk
        index_name = collection
        result = check_index(collection)
        if result["message"] == False:
            index = await create_index(index_name)
        else:
            index = pc.Index(index_name)
        uploaded_file = file.file
        df = pd.read_csv(uploaded_file)
        total_chunks = make_documents_from_csv(df)
        emb_model = UpstageEmbeddings(model="solar-embedding-1-large")

        vector_store = PineconeVectorStore(index=index, embedding=emb_model)

        ### 데이터가 남아있을때 데이터 제거(소량일때만 사용), 추후 모듈화
        if len(index.describe_index_stats()["namespaces"]) > 0:
            index.delete(delete_all=True, namespace="")

        ### 파인콘 API로 한번에 대용량 update가 불가능하여 배치처리
        total = len(total_chunks)
        batch_size = 100
        for start in tqdm(range(0, total, batch_size), desc="Upserting to Pinecone"):
            end = start + batch_size

            batch_docs = total_chunks[start:end]
            # print(batch_docs)
            vector_store.add_documents(documents=batch_docs)
        return JSONResponse(
            status_code=200, 
            content={"message": "인덱스가 업데이트되었습니다"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"message": str(e)}
        )



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)