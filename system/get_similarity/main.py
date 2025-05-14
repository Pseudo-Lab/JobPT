from get_similarity.nodes.retrieval import retrieveral, check_db_status
from get_similarity.nodes.generate import generation
from langchain_openai import OpenAIEmbeddings
from get_similarity.nodes.db_load import db_load
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
import os
from configs import COLLECTION, OPENAI_API_KEY, DB_PATH, PINECONE_API_KEY, PINECONE_INDEX

api_key = OPENAI_API_KEY
pinecone_key = PINECONE_API_KEY
pinecone_index = PINECONE_INDEX

def matching(resume, location, remote, jobtype):
    load_dotenv()
    search_filter = {}
    if location:
        search_filter["location"] = location
    if remote :
        search_filter["is_remote"] = remote
    if jobtype:
        search_filter["job_type"] = jobtype
    print("search_filter", search_filter)

    emb_model = OpenAIEmbeddings()
    print(">>>>"*30)
    if "chroma" in DB_PATH:
        print("Chroma DB 사용")
        db = db_load(DB_PATH, emb_model, COLLECTION)
        check_db_status(db, "chroma")
    else:
        print("Pinecone DB 사용")
        #Pinecone에서 index 정보 확인하려면 db가 아니라 index가 필요해서 db_load로 아직 안쌌습니다
        pc = Pinecone(api_key=pinecone_key)
        index = pc.Index(pinecone_index)
        db = PineconeVectorStore(index=index, embedding=emb_model)
        check_db_status(index, "pinecone", index)

    retriever = retrieveral(db, filter = search_filter)

    # resume_path = './data/CV/ml_engineer_CV_3.txt'
    # prompt_path = './data/prompt.yaml'

    answer, jd, jd_url, c_name = generation(retriever, resume)

    return answer, jd, jd_url, c_name
