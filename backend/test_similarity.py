import asyncio
import os
import sys

# 프로젝트 루트 경로 추가 (모듈 import 문제 해결)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from get_similarity.main import matching

# 테스트용 더미 이력서 (CV)
TEST_RESUME = """
저는 3년차 머신러닝 엔지니어입니다.
주로 Python, PyTorch, TensorFlow를 사용하여 자연어 처리(NLP) 모델을 개발했습니다.
LLM(Large Language Model)의 파인튜닝과 RAG(Retrieval-Augmented Generation) 시스템 구축 경험이 있습니다.
Docker와 Kubernetes를 활용한 모델 서빙 및 배포 경험도 보유하고 있으며,
AWS 클라우드 환경에서 ML 파이프라인(MLOps)을 구축해 본 경험이 있습니다.
최근에는 Agent 기반의 시스템 평가 및 최적화 작업에 관심이 많습니다.
협업 툴로는 Jira, Confluence, Slack을 능숙하게 사용합니다.
"""

async def run_test():
    print(">>> 테스트 시작: Dense-Only Multi-aspect Matching 검증")
    print("-" * 60)
    
    try:
        # main.py의 matching 함수 직접 호출
        # location, remote, jobtype은 None으로 설정하여 필터링 없이 전체 검색
        results = await matching(
            resume=TEST_RESUME, 
            location=None, 
            remote=None, 
            jobtype=None
        )
        
        # results는 (jd_summaries, jd_urls, c_names) 튜플
        summaries, urls, companies = results
        
        print("\n>>> 검색 결과 확인")
        print("-" * 60)
        
        if isinstance(summaries, str) and "No matches" in summaries:
            print("❌ 매칭된 결과가 없습니다.")
        else:
            for i, (comp, url, summ) in enumerate(zip(companies, urls, summaries)):
                print(f"[{i+1}위] {comp}")
                print(f"🔗 URL: {url}")
                print(f"📝 요약: {summ[:100]}...") # 너무 길면 자르기
                print("-" * 30)
                
            print("\n✅ 테스트 완료: 로직이 정상적으로 수행되었습니다.")
            
    except Exception as e:
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
