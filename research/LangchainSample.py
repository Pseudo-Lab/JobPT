from transformers import pipeline
from langchain.llms import HuggingFacePipeline
from langchain import PromptTemplate, LLMChain

# Hugging Face Pipeline 초기화
generator = pipeline("text-generation", model="distilgpt2")

# LangChain LLM 초기화
llm = HuggingFacePipeline(pipeline=generator)

# 프롬프트 템플릿 생성
template = PromptTemplate(template="Summarize the following text: {text}")

# 간단한 체인 구성
chain = LLMChain(llm=llm, prompt=template)

# 입력 예제
input_text = "Artificial Intelligence is transforming industries by automating tasks and enabling new possibilities."


if __name__ == "__main__":
    # 에이전트 실행
    response = chain.run({"text": input_text})
    print("LangChain Agent Response:", response)