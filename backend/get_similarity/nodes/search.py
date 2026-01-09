from langchain_upstage import ChatUpstage
from configs import *
import numpy as np
from collections import defaultdict

llm = ChatUpstage(model=RAG_MODEL, api_key=UPSTAGE_API_KEY)
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
    print("입력된 resume:", resume[:100], "...")  # 긴 텍스트는 일부만 출력
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


async def search_jd_summary(retriever, lexical_retriever, resume, pinecone_index=None):
    from get_similarity.utils.segmenter import HierarchicalSegmenter
    from get_similarity.utils.matcher import DenseMatcher
    
    print("\n=== Summary 검색 함수 시작 ===")
    print("입력된 resume:", resume[:100], "...")  # 긴 텍스트는 일부만 출력

    # 1. 문서 검색 (Candidate Selection)
    # 기존 invoke(resume)는 '문서' 단위 유사도로 k개를 가져옵니다.
    # 하지만 우리의 목표는 'JD id' 후보군을 뽑는 것입니다.
    # 따라서 넉넉하게 k=30~50개를 가져와서 unique job_id를 추립니다.
    
    # retriever search_kwargs 업데이트 (잠시 후보군 탐색용으로 확장)
    original_k = retriever.search_kwargs.get("k", 10)
    retriever.search_kwargs["k"] = 50
    
    candidates = retriever.invoke(resume)
    
    # 2. 후보군 Job ID 추출
    candidate_job_ids = set()
    job_to_metadata = {}
    
    candidate_job_ids = set()
    job_to_metadata = {}
    
    if candidates:
        print(f"[DEBUG] 첫 번째 문서 Metadata 예시: {candidates[0].metadata}")

    for doc in candidates:
        job_id = None
        # 1. doc.id 파싱 (wd_1234__c0001)
        did = getattr(doc, "id", "")
        if did and "__" in did:
            job_id = did.split("__")[0]
            
        # 2. metadata 확인
        if not job_id:
             job_id = doc.metadata.get("job_id")
        
        # 3. URL 확인
        if not job_id:
             url = doc.metadata.get("job_url") or doc.metadata.get("url")
             if url:
                 job_id = str(url).rstrip("/").split("/")[-1]

        if job_id:
            candidate_job_ids.add(job_id)
            # 메타데이터 저장
            # 중요: doc.metadata에 회사명 등이 있어야 함.
            if job_id not in job_to_metadata:
                 job_to_metadata[job_id] = doc.metadata

    print(f"후보군 추출 완료: {len(candidate_job_ids)}개의 고유 JD 발견")

    # Pinecone Index가 없으면 기존 로직(search_dict 사용)으로 fallback
    if not pinecone_index:
        print("[WARN] Pinecone Index 객체가 없습니다. 기존 단순 검색 로직으로 수행합니다.")
        retriever.search_kwargs["k"] = original_k # 복구
        job_descriptions = candidates[:10] # 상위 10개만
        # ... (기존 RRF 로직 생략, 필요한 경우 추가) ...
    else:
        # 3. Dense Multi-aspect Re-ranking 수행
        print(">>> Dense Multi-aspect Re-ranking 시작")
        
        # (A) CV Segmentation & Embedding
        # Embedder는 retriever가 가지고 있는 모델을 재사용하거나 새로 선언
        # 여기서는 retriever.embeddings 객체가 있다고 가정 (LangChain 표준)
        segmenter = HierarchicalSegmenter(min_chunk_length=100, max_chunk_length=300)
        cv_chunks = segmenter.segment(resume) 
        if not cv_chunks:
            cv_chunks = segmenter._segment_plaintext(resume)
            
        print(f"CV 청크 분할: {len(cv_chunks)}개")
        
        # CV 청크 벡터화
        # retriever가 embedding_function을 가지고 있음
        embedding_model = retriever.tags[0] if hasattr(retriever, "tags") else None
        # LangChain Retriever 구조상 embedding_function 접근이 다를 수 있음.
        # 가장 확실한 건 전달받은 retriever 객체 내부를 사용하는 것임.
        # 만약 접근이 어렵다면 main.py에서 emb_model을 넘겨받는 게 좋으나,
        # 여기서는 retriever.vectorstore.embedding_function 등을 시도하거나 
        # OpenAIEmbeddings을 새로 인스턴스화 하는 오버헤드를 줄이기 위해 노력함.
        
        # 접근법: retriever -> vectorstore -> embeddings
        emb_fn = None
        if hasattr(retriever, "vectorstore"):
             emb_fn = retriever.vectorstore.embeddings
        
        if not emb_fn:
            # Fallback: 새로 생성 (비효율적이지만 안전)
            from langchain_openai import OpenAIEmbeddings
            emb_fn = OpenAIEmbeddings()

        cv_vectors = emb_fn.embed_documents(cv_chunks)
        cv_vectors_np = [np.array(v) for v in cv_vectors]

        # (B) JD Full Vectors Fetching
        # [Full Scan Mode Implementation]
        # 노트북 로직 복제: DB 전체 벡터를 가져와서 Scoring 수행
        
        # 2. JD Full Scan (Pinecone에서 모든 벡터 가져오기)
        TOTAL_VECTORS_TO_FETCH = 2000 # temp 인덱스 전체 크기 커버 (약 2000개)
        print(f">>> 2. JD 전체 데이터 로드 (Full Scan Mode, Target: {TOTAL_VECTORS_TO_FETCH} vectors)")
        
        # 이전 단계 candidates 루프에서 수집한 메타데이터는 무시하고 새로 수집 (Full Scan이므로)
        job_embeddings_map = defaultdict(list)
        job_to_metadata = {}
        
        if pinecone_index:
            try:
                # CV 첫 청크 벡터를 Query로 사용 (어차피 k가 매우 커서 다 딸려옴)
                # 만약 차원이 4096이 아니라면 임베딩 모델 확인 필요.
                query_vec = cv_vectors[0]
                
                # include_metadata=True, include_values=True 필수
                resp = pinecone_index.query(
                    vector=query_vec, 
                    top_k=TOTAL_VECTORS_TO_FETCH, 
                    include_metadata=True, 
                    include_values=True,
                    namespace=""
                )
                
                matches = resp.get("matches", [])
                print(f"Pinecone Full Query 완료: {len(matches)}개 청크 확보")
                
                for m in matches:
                    # m is ScoredVector (id, score, values, metadata)
                    vid = m["id"]
                    vals = m["values"]
                    meta = m.get("metadata", {})
                    
                    # Job ID 추출
                    job_id = None
                    if "__" in vid:
                        job_id = vid.split("__")[0]
                    # 메타데이터에 job_id가 있는 경우
                    elif meta and "job_id" in meta:
                        job_id = str(meta["job_id"])
                    
                    if job_id:
                        # 메타데이터 저장 (회사명 등)
                        if job_id not in job_to_metadata:
                            job_to_metadata[job_id] = meta
                        
                        # 텍스트 추출 (Coverage용)
                        text_content = str(meta.get("text", "") or meta.get("chunk_text", "") or meta.get("context", ""))

                        job_embeddings_map[job_id].append({
                            "text": text_content,
                            "values": np.array(vals)
                        })
                        
            except Exception as e:
                print(f"Pinecone Full Query Error: {e}")
                import traceback
                traceback.print_exc()
                
        else:
            print("[ERROR] Pinecone Index Required for Full Scan")

        print(f"JDs 재조립 완료: {len(job_embeddings_map)}개 Job (유효 벡터 보유)")

        # 3. Scoring (Parallel & JIT Optimized)
        print(">>> 3. Dense Multi-aspect Scoring (Similarity Only)")
        matcher = DenseMatcher(num_workers=4)
        
        scored_jobs = matcher.compute_batch_parallel(cv_vectors_np, job_embeddings_map)
        
        # 메타데이터 병합
        for job in scored_jobs:
            jid = job["job_id"]
            job["metadata"] = job_to_metadata.get(jid, {})

        # 정렬
        scored_jobs.sort(key=lambda x: x["final_score"], reverse=True)
        top_jobs = scored_jobs[:4]
        
        # 결과 포맷팅
        top_job_summaries = []
        top_job_urls = []
        top_company_names = []
        
        print("\n>>> 검색 결과 확인")
        print("-" * 60)

        for job in top_jobs:
            meta = job["metadata"]
            url = meta.get("job_url") or meta.get("url") or ""
            company = meta.get("company_name") or meta.get("company") or ""
            summary = meta.get("summary") or meta.get("text") or "요약 없음"
            
            # 중요: None 방지
            if not company and job["job_id"]:
                 company = f"Job {job['job_id']}"
            
            # Coverage 출력 제거
            print(f"[Rank] Score: {job['final_score']:.4f} | {company}")
            print(f"🔗 URL: {url}")
            print(f"📝 요약: {str(summary)[:100]}...")
            print("-" * 30)

            top_job_summaries.append(summary)
            top_job_urls.append(url)
            top_company_names.append(company)

        retriever.search_kwargs["k"] = original_k # 복구
        return top_job_summaries, top_job_urls, top_company_names
    
