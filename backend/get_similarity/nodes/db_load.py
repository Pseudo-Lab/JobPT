from langchain_chroma import Chroma
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from configs import PINECONE_API_KEY, PINECONE_INDEX
from get_similarity.nodes.retrieval import check_db_status

def get_db(DB_PATH, emb_model, collection, DB_TYPE):
    """
    Vector DB를 로드하는 함수
    Args:
        DB_PATH: Vector DB의 저장 경로(로컬일때만 사용, 현재는 Pinecone이라 사용x)
        emb_model: 임베딩 모델
        collection: Chroma의 collection 이름
        DB_TYPE: DB 타입 ["Chroma", "Pinecone"]
    Returns:
        persist_db: 로드된 Vector DB
    """
    if DB_TYPE == "Chroma":
        print("Chroma DB 사용")
        persist_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=emb_model,
            collection_name=collection,
        )
        check_db_status(persist_db, "chroma")

    elif DB_TYPE == "Pinecone":
        print("Pinecone DB 사용")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)
        # text 필드가 없으므로 job_id를 텍스트로 쓰게 함 (Chunk ID 추출용으로만 사용)
        persist_db = PineconeVectorStore(index=index, embedding=emb_model, text_key="job_id")
        check_db_status(index, "pinecone", index)
        # 중요: Raw Index 객체를 함께 반환해야 fetch_vectors가 가능함
        return persist_db, index

    return persist_db, None