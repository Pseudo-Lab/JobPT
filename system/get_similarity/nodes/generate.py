from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import yaml
import pandas as pd
from configs import *

llm = ChatOpenAI(model=RAG_MODEL)


def generation(retriever, resume):
    print("\n=== Generation 함수 시작 ===")
    print("입력된 resume:", resume[:100], "...")  # 긴 텍스트는 일부만 출력

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
        return "Error prompt", "", "", ""

    # Prompt 설정
    task = "resume alignment evaluation"
    prompt_template = prompt_data["prompts"][task][JD_MATCH_PROMPT]
    print("프롬프트 템플릿:", prompt_template[:100], "...")
    prompt = PromptTemplate.from_template(prompt_template)

    # RAG Chain 설정
    rag_chain = {"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()
    print("RAG Chain 설정 완료")

    # Retriever 실행
    print("\n=== Retriever 실행 ===")
    job_descriptions = retriever.invoke(resume)
    print("검색된 문서 수:", len(job_descriptions) if job_descriptions else 0)
    print("job_descriptions 타입:", type(job_descriptions))
    print("job_descriptions 내용:", job_descriptions)

    # 결과가 없는 경우 처리
    if not job_descriptions:
        print("검색된 문서가 없습니다!")
        return "No matches found", "", "", ""

    # Metadata 접근
    try:
        top_job_description = job_descriptions[0].metadata["description"]
        job_url = job_descriptions[0].metadata["job_url"]
        company_name = job_descriptions[0].metadata["company"]
        print("==================================================")
        print(job_descriptions)
        print("==================================================")
        print("\n첫 번째 문서 메타데이터 확인:")
        print("description 존재:", "description" in job_descriptions[0].metadata)
        print("job_url 존재:", "job_url" in job_descriptions[0].metadata)
    except Exception as e:
        print("메타데이터 접근 중 에러:", str(e))
        return "Error accessing metadata", "", "", ""

    # Chain 실행
    print("\n=== Chain 실행 ===")
    try:
        answer = rag_chain.invoke(resume)
        print("Chain 실행 결과:", answer[:100], "...")
    except Exception as e:
        print("Chain 실행 중 에러:", str(e))
        return "Error in chain execution", top_job_description, job_url, ""

    return answer, top_job_description, job_url, company_name


def format_docs(docs):
    print("\n=== format_docs 함수 실행 ===")
    print("입력된 docs 수:", len(docs) if docs else 0)
    try:
        doc_list = [doc.metadata["description"] for doc in docs]
        print("메타데이터 추출 성공")
        return doc_list[0]
    except Exception as e:
        print("format_docs 에러:", str(e))
        return ""
