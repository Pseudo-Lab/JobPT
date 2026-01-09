from get_similarity.nodes.retrieval import get_retriever
from get_similarity.nodes.search import search_jd, search_jd_summary
from get_similarity.nodes.generate import generation
from get_similarity.nodes.db_load import get_db
import pickle#로컬에서 그대로 받는거라 강조는 안되지만 필요
from configs import COLLECTION, DB_PATH, DB_TYPE

async def matching(resume, location, remote, jobtype):
    """
    사용자의 이력서와 필터링을 위한 메타데이터를 입력 받고 적합한 채용공고를 반환합니다.

    Args:
        resume: 사용자의 이력서 텍스트
        location: 근무 희망 위치 ['USA', 'Germany', 'UK']
        remote: 원격 근무 여부 ['True', 'False']
        jobtype: 근무 유형 ['fulltime', 'parttime']
    Returns:
        answer: 채용공고에 대한 답변 텍스트
        jd: 채용공고 전문
        jd_url: 채용공고 URL
        c_name: 채용공고를 올린 회사 이름
    """
    search_filter = {}
    if location:
        search_filter["location"] = location
    if remote :
        search_filter["is_remote"] = remote
    if jobtype:
        search_filter["job_type"] = jobtype

    from langchain_upstage import UpstageEmbeddings
    from configs import UPSTAGE_API_KEY
    # 노트북과 동일한 모델 사용
    emb_model = UpstageEmbeddings(model="solar-embedding-1-large", api_key=UPSTAGE_API_KEY)

    print(">>>>"*30)
    print("Loading vector DB...")
    print("Loading vector DB...")
    db, pinecone_index = get_db(DB_PATH, emb_model, COLLECTION, DB_TYPE)
    ## lexical DB 로딩
    ### 한국어 BM25 retrieval 추가시 활용
    # with open("backend/get_similarity/data/bm25_retriever_final.pkl", "rb") as f:
    #     lexical_retriever = pickle.load(f)
    lexical_retriever = None

    retriever = get_retriever(db, emb_model, filter=search_filter)

    # ## 기존 1개 결과 Retrieval, Generation 방식
    # jd, jd_url, c_name = await search_jd(retriever, lexical_retriever, resume, pinecone_index)
    # answer = await generation(resume, jd)


    jd_summaries, jd_urls, c_names = await search_jd_summary(retriever, lexical_retriever, resume, pinecone_index)
    return jd_summaries, jd_urls, c_names
