from nodes.retrieval import retriever
from nodes.generate import generation
from langchain_openai import OpenAIEmbeddings
from nodes.db_load import db_load
from dotenv import load_dotenv
import os

DB_PATH = "./chroma_db"
api_key = os.getenv("OPENAI_API_KEY")

def matching(resume):
    load_dotenv()

    emb_model = OpenAIEmbeddings()
    collection_name = "semantic_0"
    db = db_load(DB_PATH, emb_model, collection_name)

    retriever = retriever(db)

    # resume_path = './data/CV/ml_engineer_CV_3.txt'
    # prompt_path = './data/prompt.yaml'
        
    answer = generation(retriever, resume)
    print(answer)