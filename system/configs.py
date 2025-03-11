import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
RAG_MODEL = os.getenv("RAG_MODEL", "gpt-4o-mini")  # default: gpt-4o-mini
DB_PATH = "/app/chroma_db"
PROMPT_YAML = "system/get_similarity/data/prompt.yaml"
JD_MATCH_PROMPT = "prompt_template_1"
JD_PATH = "/app/data/jd_origin"
COLLECTION = "semantic_0"
