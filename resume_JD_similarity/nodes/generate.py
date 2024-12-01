from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import yaml 
import pandas as pd
from configs import RAG_MODEL, PROMPT

llm = ChatOpenAI(model=RAG_MODEL)

def generation(retriever, resume):
    # user prompt(resume) load
    # with open (resume_path, "r") as file:
    #     resume = file.read()
        
    # prompt load
    with open(PROMPT, 'r') as file:
        prompt_data = yaml.safe_load(file)

    # prompt load
    task = "resume alignment evaluation"
    prompt_template = prompt_data['prompts'][task]['prompt_template']
    prompt = PromptTemplate.from_template(prompt_template)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # 가장 첫번째 job description 반환
    job_descriptions = retriever.invoke(resume)
    top_job_description  = job_descriptions[0].metadata['description']

    # chain 실행하기
    answer = rag_chain.invoke(resume)
    return answer, top_job_description

def format_docs(docs):
    """doc의 metadata에 저장되어있는 원본 description을 가져오기"""
    doc_list = [doc.metadata['description'] for doc in docs]

    return doc_list[0] # top 1


    