from configs import *
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_upstage import ChatUpstage
from langchain_core.prompts import PromptTemplate
import yaml

# Upstage API 사용 (solar-pro2)
llm = ChatUpstage(
    model=RAG_MODEL,
    api_key=UPSTAGE_API_KEY
)

# def format_docs(docs):
#     print("\n=== format_docs 함수 실행 ===")
#     print("입력된 docs 수:", len(docs) if docs else 0)
#     try:
#         doc_list = [doc.metadata["description"] for doc in docs]
#         print("메타데이터 추출 성공")
#         return doc_list[0]
#     except Exception as e:
#         print("format_docs 에러:", str(e))
#         return ""


async def generation(resume, jd_description):
    # YAML 로드 부분
    try:
        with open(PROMPT_YAML, "r", encoding="utf-8") as file:
            prompt_data = yaml.safe_load(file)
            print("YAML 파일 로드 성공")
    except UnicodeDecodeError:
        print("UTF-8 로드 실패, CP949로 시도")
        with open(PROMPT_YAML, "r", encoding="cp949") as file:
            prompt_data = yaml.safe_load(file)
    except Exception as e:
        print("YAML 로드 중 에러:", str(e))
        return "Error prompt"

    # Prompt 설정
    task = "resume alignment evaluation"
    prompt_template = prompt_data["prompts"][task][JD_MATCH_PROMPT]
    print("프롬프트 템플릿:", prompt_template[:100], "...")
    prompt = PromptTemplate.from_template(prompt_template)

    # RAG Chain 설정
    rag_chain = {"context": RunnableLambda(lambda x: x["jd_description"]), "question": RunnableLambda(lambda x: x["resume"])} | prompt | llm | StrOutputParser()
    print("RAG Chain 설정 완료")

    # Chain 실행(LLM을 통한 CV, JD 리뷰)
    print("\n=== Chain 실행 ===")
    try:
        answer = rag_chain.invoke(
            {
                "jd_description": jd_description,
                "resume": resume
            }
        )
        print("Chain 실행 결과:", answer[:100], "...")
    except Exception as e:
        print("Chain 실행 중 에러:", str(e))
        return "Error in chain execution"

        
    return answer