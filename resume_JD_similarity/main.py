from nodes.retrieval import retriever
from nodes.generate import generation
from langchain_openai import OpenAIEmbeddings
from nodes.db_load import db_load
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

embedding = OpenAIEmbeddings()
DB_PATH = "./chroma_db"
collection_name = "semantic_0"
db = db_load(DB_PATH, embedding, collection_name)

retriever = retriever(db)

resume_path = './data/CV/ml_engineer_CV_3.txt'
prompt_path = './data/prompt.yaml'
    
answer = generation(retriever, prompt_path, resume_path)
print(answer)