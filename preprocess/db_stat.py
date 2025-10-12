from fastapi import FastAPI
import uvicorn
import os
from dotenv import load_dotenv
import pandas as pd

from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm

load_dotenv(dotenv_path="../backend/.env")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
collection = "korea-jd-test"



app = FastAPI()
async def check_index(collection: str="korea-jd-test"):
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
    result = await check_index(collection)
    if result["message"]:
        index = pc.Index(index_name)
        stat = index.describe_index_stats()
        stat = stat.to_dict()
        return stat
    else:
        return {"message": "인덱스가 존재하지 않습니다"}


@app.get("/update_index")
async def update_index(collection: str="korea-jd-test", data_path: str="data/data.csv"):
    index_name = collection
    result = await check_index(collection)
    if result["message"]:
        index = pc.Index(index_name)
        df = pd.read_csv(data_path)
        sentences = list(df["sentence"])
        ### 청킹엔 특정한 처리가 들어가진 않았음, 추후 추가된다면 모듈화 예정
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100, separators=["<chunk_sep>","\r\n","\n\n", "\n", "\t", " ", ""])
        total_chunks = []

        ### 구분자 기반 메타데이터 파싱
        for i, desciption in enumerate(sentences):
            parts = df.iloc[i]["company_name"].split(" ")
            parts1 = parts[0].split("∙")
            parts2 = parts[1].split("∙")
            if len(parts) > 2:
                parts3 = parts[2].split("∙")[0]
            else:
                parts3 = "0년"

            company = parts1[0]
            location = parts2[0]
            experience = parts2[1]
            requirement = parts3

            meta_data = [{"description":df.iloc[i]["description"],
            "job_url": df.iloc[i]["url"],
            "company": company,
            "location": location,
            "experience": experience,
            "requirement": requirement}]
            chunks = text_splitter.create_documents([desciption], meta_data)
            total_chunks.extend(chunks)

        emb_model = OpenAIEmbeddings()
        vector_store = PineconeVectorStore(index=index, embedding=emb_model)

        ### 데이터가 남아있을때 데이터 제거(소량일때만 사용 예정), 추후 모듈화
        if len(index.describe_index_stats()["namespaces"]) > 0:
            index.delete(delete_all=True, namespace="")

        ### 파인콘 API로 한번에 대용량 update가 불가능하여 배치처리
        total = len(total_chunks)
        batch_size = 100
        for start in tqdm(range(0, total, batch_size), desc="Upserting to Pinecone"):
            end = start + batch_size
            batch_docs = total_chunks[start:end]
            vector_store.add_documents(documents=batch_docs)


        return {"message": "인덱스가 업데이트되었습니다"}
    else:
        return {"message": "인덱스가 존재하지 않습니다"}





if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)