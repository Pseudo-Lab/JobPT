import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") 
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini") #default: gpt-4o-mini
DB_PATH = './chroma_db'
PROMPT = './resume_JD_similarity/data/prompt.yaml'
JD_PATH = './resume_JD_similarity/data/jd_origin'
COLLECTION = 'semantic_0'