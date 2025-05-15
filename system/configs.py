import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = "jd-dataset"
UPSTAGE_API_KEY=os.getenv("UPSTAGE_API_KEY", "")
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini")  # default: gpt-4o-mini
# DB_PATH = "/app/data/chroma_db"
DB_PATH = "Pinecone"
PROMPT_YAML = "get_similarity/data/prompt.yaml"
JD_MATCH_PROMPT = "prompt_template_1"
JD_PATH = "/app/data/jd_origin"
COLLECTION = "semantic_0"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
MODEL = "gpt-4o-mini"