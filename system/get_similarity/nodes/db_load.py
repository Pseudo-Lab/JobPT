from langchain_chroma import Chroma

def db_load(DB_PATH, emb_model, collection):
    # 디스크에서 문서를 로드
    persist_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=emb_model,
        collection_name=collection,
    )
    return persist_db