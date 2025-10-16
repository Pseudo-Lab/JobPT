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
from tqdm import tqdm

from utils import preprocess

load_dotenv(dotenv_path="../backend/.env")

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


@app.post("/update_index")
async def update_index(file: UploadFile, collection: str="korea-jd-test"):
    if not file.filename.endswith('.csv'):
        # CSV 파일이 아닌 경우 오류 처리
        return JSONResponse(
            status_code=400, 
            content={"message": "CSV 파일만 업로드할 수 있습니다."}
        )
    try: 
        uploaded_file = file.file
        df = pd.read_csv(uploaded_file)
        total_chunks = preprocess(df)

        index_name = collection
        result = check_index(collection)
        index = pc.Index(index_name)

        emb_model = OpenAIEmbeddings()
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