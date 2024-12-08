from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel

from parser import run_parser
from get_similarity.main import matching

app = FastAPI()

# OpenAI API 키 설정
import os


### DB connection
class Request(BaseModel):
    resume_path: str


# 라우터 정의
async def run(data: Request):
    resume_path = data["resume_path"]

    ### pdf parsing
    resume = run_parser(resume_path)

    # sample resume load
    # resume_path = './resume_JD_similarity/data/sample_resume.txt'
    # with open (resume_path, "r") as file:
    #     resume = file.read()

    ### resume matching
    res, job_description = matching(resume)

    return {"JD": job_description, "output": res}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0")
