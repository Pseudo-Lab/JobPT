import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") 
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini") #default: gpt-4o-mini
PROMPT = './resume_JD_similarity/data/prompt.yaml'