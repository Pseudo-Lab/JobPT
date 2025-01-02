from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel

from parser import run_parser, convert_pdf_to_jpg
from get_similarity.main import matching

app = FastAPI()

# OpenAI API 키 설정
import os


### DB connection
class Request(BaseModel):
    resume_path: str


# 라우터 정의
@app.post("/matching")
async def run(data: Request):
    resume_path = data.resume_path
    output_folder = "data"
    image_paths = convert_pdf_to_jpg(resume_path, output_folder)
    print(image_paths)
    ### pdf parsing
    resume_content = []
    for image_path in image_paths:
        resume = run_parser(image_path)
        resume_content.append(resume)

    resume_content = "".join(resume_content)
    print(resume_content)
    ### resume matching
    # sample resume load
    # resume_path = './resume_JD_similarity/data/sample_resume.txt'
    # with open (resume_path, "r") as file:
    #     resume = file.read()

    ### resume matching
    res, job_description, job_url, c_name = matching(resume_content)

    return {"JD": job_description, "JD_url": job_url, "output": res, "name": c_name}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0")
