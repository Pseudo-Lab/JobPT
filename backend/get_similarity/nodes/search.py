from langchain_upstage import ChatUpstage
from configs import *
import numpy as np
from collections import defaultdict

# Upstage API 사용 (solar-pro2)
llm = ChatUpstage(
    model=RAG_MODEL,
    api_key=UPSTAGE_API_KEY
)
search_dict = defaultdict(list)

def make_rank(results,k, full=False):
    ## query와 db를 넣으면 id의 list를 리턴
    search_range = min(k, len(results))
    scores = np.empty(search_range, dtype=object)
    for i in range(search_range):
        scores[i] = results[i].metadata['id']
        search_dict[results[i].metadata['id']].append(results[i])
    return scores

def rrf(multi_scores, k=1):        #n*10개의 입력, id로 들어옴
    score = 0.0
    score_dict = defaultdict(int)
    for scores in multi_scores:
        for rank, id in enumerate(scores):
            score = 1.0 / ( k + rank+1)       #index는 0부터 시작하므로 +1
            score_dict[id]+=score
    score_dict = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    return score_dict



async def search_jd(retriever, lexical_retriever, resume):
    """
    사용자의 이력서를 기반으로 벡터 DB에서 채용공고를 검색하고
    LLM을 이용해 CV, JD 리뷰를 수행하는 함수
    Args:
        retriever: semantic retriever
        lexical_retriever: lexical retriever
        resume: 사용자의 이력서
    Returns:
        answer: LLM을 통한 CV, JD 리뷰
        top_job_description: 첫 번째 문서(top-similarity)의 채용공고 전문
        top_job_url: 첫 번째 문서의 채용공고 URL
        top_company_name: 첫 번째 문서의 회사 이름
    """
    print("\n=== Generation 함수 시작 ===")
    print(f"입력된 resume 길이: {len(resume)} 문자")
    print("입력된 resume 내용:", resume[:200], "...")  # 긴 텍스트는 일부만 출력
    job_descriptions = retriever.invoke(resume)

    ### 한국어 BM25 retrieval 추가시 활용
    if lexical_retriever:
        lexical_job_descriptions = lexical_retriever.invoke(resume)
        sem_rank = make_rank(job_descriptions, k=10)
        lex_rank = make_rank(lexical_job_descriptions, k=10)
        job_descriptions = search_dict[rrf([sem_rank, lex_rank], k=1.2)[0][0]]

    # Retriever 실행
    print("\n=== Retriever 실행 ===")
    # print("job_descriptions:", job_descriptions)      # retrieval된 모든 결과 출력



    # 결과가 없는 경우 처리
    if not job_descriptions:
        print("검색된 문서가 없습니다!")
        return "No matches found", "", "", ""


    # Metadata 접근(채용공고 전문 포함)
    try:
        top_job_description = job_descriptions[0].metadata["description"]
        top_job_url = job_descriptions[0].metadata["job_url"]
        top_company_name = job_descriptions[0].metadata["company"]
        print("==================================================")
        print("\n첫 번째 문서 전문 및 메타데이터 확인:")
        print("JD 전문:", top_job_description)
        print("==================================================")
        print("job_url:", top_job_url)
        print("company:", top_company_name)
    except Exception as e:
        print("메타데이터 접근 중 에러:", str(e))
        return "Error accessing metadata", "", "", ""



    return top_job_description, top_job_url, top_company_name
