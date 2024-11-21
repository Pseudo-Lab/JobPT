"""
ChromaDB에 청크를 저장하는 기능입니다.
"""
from utils.preprocess import preprocess
# from langchain_text_splitters import CharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain_chroma import Chroma
from pandas import DataFrame

from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def load_emb_model(cache=True):
    """embedding model을 로드하고 캐싱하는 함수입니다."""
    embedding = OpenAIEmbeddings()

    # Embedding model 캐싱하기
    if cache:
        cache_path = "./cache/"
        store = LocalFileStore(cache_path)
        cached_embedder = CacheBackedEmbeddings.from_bytes_store(
            embedding, store, namespace=embedding.model
        )
        return cached_embedder
    return embedding

def set_splitter(emb_model):
    """splitter를 셋업하는 함수입니다."""
    text_splitter = SemanticChunker(
        emb_model, breakpoint_threshold_type="percentile"
    )
    return text_splitter

def get_chunks(df, text_splitter):
    total_chunks = []
    for i, desciption in enumerate(df['description']):
        chunk = text_splitter.create_documents([desciption])
        chunk[0].metadata = df.iloc[i].to_dict()
        total_chunks.extend(chunk)
    return total_chunks

def insert_chunks(document_path: str, collection: str):
    DB_PATH = "./chroma_db"
    emb_model = load_emb_model()

    preprocessed_doc = preprocess(document_path)
    total_chunks = get_chunks(preprocessed_doc, set_splitter(emb_model))
    
    # 청크를 디스크에 저장. 저장시 persist_directory에 저장할 경로 지정
    # VectorDB에 저장할 때 임베딩 모델도 지정
    db = Chroma.from_documents(
        total_chunks, emb_model, persist_directory=DB_PATH, collection_name=collection
    )

    return None
    
if __name__ == "__main__":
    jd_path = './data/USA_jobs_total.csv'
    collection_name = "semantic_0"
    
    insert_chunks(jd_path, collection_name)