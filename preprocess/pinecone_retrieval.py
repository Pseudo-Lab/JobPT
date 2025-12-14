from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings
from configs import PINECONE_API_KEY, PINECONE_INDEX, UPSTAGE_API_KEY


def embed_text(text: str, emb_model=None):
    """
    텍스트를 임베딩 벡터로 변환하는 함수
    
    Args:
        text: 임베딩할 텍스트
        emb_model: 임베딩 모델 (None이면 기본 Upstage 모델 사용)
    
    Returns:
        임베딩 벡터 (list of float)
    
    Example:
        >>> vector = embed_text("백엔드 개발자를 찾습니다")
        >>> print(len(vector))  # 4096
    """
    if emb_model is None:
        emb_model = UpstageEmbeddings(
            api_key=UPSTAGE_API_KEY,
            model="solar-embedding-1-large"
        )
    
    # 텍스트를 임베딩 벡터로 변환
    vector = emb_model.embed_query(text)
    
    return vector


def retrieve_from_pinecone(query: str, k: int = 10, filter: dict = None, emb_model=None, index="index"):
    """
    Pinecone에서 유사한 문서를 검색하는 함수
    
    Args:
        query: 검색 쿼리 텍스트
        k: 검색할 문서 개수 (default: 10)
        filter: 메타데이터 필터 (예: {"company": "구글"})
        emb_model: 임베딩 모델 (None이면 기본 Upstage 모델 사용)
    
    Returns:
        검색된 문서 리스트 [{"content": str, "metadata": dict, "score": float}, ...]
    
    Example:
        >>> results = retrieve_from_pinecone("백엔드 개발자", k=5)
        >>> for doc in results:
        >>>     print(f"Score: {doc['score']}, Content: {doc['content'][:100]}")
    """
    # 임베딩 모델 초기화
    if emb_model is None:
        emb_model = UpstageEmbeddings(
            api_key=UPSTAGE_API_KEY,
            model="solar-embedding-1-large"
        )
    
    # Pinecone 초기화
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index)
    
    # VectorStore 생성
    vector_store = PineconeVectorStore(index=index, embedding=emb_model)
    
    # 유사도 검색
    results = vector_store.similarity_search_with_score(
        query=query,
        k=k,
        filter=filter
    )
    
    # 결과 포맷팅
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score)
        })
    
    return formatted_results

