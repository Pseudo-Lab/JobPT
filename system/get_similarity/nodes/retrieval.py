from get_similarity.nodes.db_load import db_load
from langchain.embeddings.openai import OpenAIEmbeddings


def check_db_status(db, db_type="chroma", index=None):
    """
    DB 상태를 확인하는 함수
    """
    if db_type == "chroma":
        try:
            print("DB 상태 확인 중...")
            print(f"- Collection name: {db._collection.name}")
            print(f"- 총 문서 수: {db._collection.count()}")
        except Exception as e:
            print(f"DB 상태 확인 중 에러 발생: {str(e)}")
            raise
    elif db_type == "pinecone":
        try:
            print("DB 상태 확인 중...")
            print(f"- 총 문서 수: {db.describe_index_stats()}")
        except Exception as e:
            print(f"DB 상태 확인 중 에러 발생: {str(e)}")
            raise



def retrieveral(db, debug=False):
    print("\n=== Retriever 설정 및 검색 시작 ===")
    print(f"Debug 모드: {debug}")

    try:
        # DB 상태 확인
        # print(f"DB 상태:")
        # print(f"- Collection name: {db._collection.name}")
        # print(f"- 총 문서 수: {db._collection.count()}")

        # embedding 모델 생성
        embedding = OpenAIEmbeddings()

        # retriever 설정에 embedding 추가
        retriever = db.as_retriever(search_kwargs={"k": 3}, embedding_function=embedding)  # top-3 문서 검색  # 임베딩 모델 명시적 지정
        print("Retriever 설정 완료")
        print(f"- Search kwargs: {retriever.search_kwargs}")
        print(f"- Embedding model: {type(embedding)}")

        if debug:
            # debug 코드는 유지
            pass
        else:
            print("\n일반 모드: retriever 객체 반환")
            return retriever

    except Exception as e:
        print(f"Retriever 설정 중 에러 발생: {str(e)}")
        raise
