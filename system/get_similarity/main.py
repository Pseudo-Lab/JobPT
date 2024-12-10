from get_similarity.nodes.retrieval import retrieveral
from get_similarity.nodes.generate import generation
from langchain_openai import OpenAIEmbeddings
from get_similarity.nodes.db_load import db_load
from dotenv import load_dotenv
import os
from configs import COLLECTION, OPENAI_API_KEY, DB_PATH

api_key = OPENAI_API_KEY

def matching(resume):
    load_dotenv()

    emb_model = OpenAIEmbeddings()
    db = db_load(DB_PATH, emb_model, COLLECTION)

    retriever = retrieveral(db)

    # resume_path = './data/CV/ml_engineer_CV_3.txt'
    # prompt_path = './data/prompt.yaml'
        
    answer, jd, jd_url = generation(retriever, resume)
    
    return answer, jd, jd_url
