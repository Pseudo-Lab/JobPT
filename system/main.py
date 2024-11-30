from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from parser import run_parser
from resume_JD_similarity.main import matching
app = FastAPI()

# OpenAI API 키 설정
import os

### DB connection
class Request(BaseModel):
    resume_path: str

# 라우터 정의
async def run(data: Request):
    resume_path = data['resume_path']

    ### pdf parsing
    resume = run_parser(resume_path)

    ### resume matching

    res = matching(resume)

    return {
        "output": res
    }    

if __name__ == "__main__":
    uvicorn.run('main:app', host='0.0.0.0')