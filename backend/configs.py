import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

### JD 추천 관련 api
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY", "")
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini")  # default: gpt-4o-mini
DB_TYPE = "Pinecone"    #["Chroma", "Pinecone"]
PINECONE_INDEX = "korea-jd-test"
DB_PATH = "Pinecone"    #크로마에서만 사용
COLLECTION = "semantic_0"   #크로마에서만 사용
PROMPT_YAML = "get_similarity/data/prompt.yaml"

### General api key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
UPSTAGE_API_KEY=os.getenv("UPSTAGE_API_KEY", "")
JD_MATCH_PROMPT = "prompt_template_korean"
JD_PATH = "./data/jd_origin"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "")
AGENT_MODEL = "gpt-4o-mini"