from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import uuid
import os

from parser import run_parser, convert_pdf_to_jpg
from get_similarity.main import matching
from openai import OpenAI
import uvicorn
import nltk

from multi_agents.states.states import State, get_session_state, end_session, add_user_input_to_state, add_assistant_response_to_state
from multi_agents.graph import create_graph
from configs import *

# from langfuse import Langfuse
# from langfuse.callback import CallbackHandler

from ats_analyzer_improved import ATSAnalyzer


# 캐시 저장소
resume_cache = {}
analysis_cache = {}

location_cache = ""  # ['USA' 'Germany' 'UK']
remote_cache = ""  # [ True False]
job_type_cache = ""  # ['fulltime' 'parttime']

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에선 모두 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 통합된 파일 저장소 설정 (configs에서 가져오기)
from configs import UPLOAD_PATH, PROCESSED_PATH, CACHE_PATH

UPLOAD_DIR = os.path.join(UPLOAD_PATH, "resumes")
PROCESSED_DIR = PROCESSED_PATH
CACHE_DIR = CACHE_PATH

# 디렉토리 생성
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


# /matching - 이력서 분석 및 JD 매칭
class MatchRequest(BaseModel):
    resume_path: str



@app.post("/upload")
async def upload_resume(file: UploadFile = File(...), location: str = Form(""), remote: str = Form("any"), job_type: str = Form("any")):
    """
    사용자의 이력서를 업로드하고, 이력서의 정보를 캐시{file_path}에 저장합니다.

    Args:
        file: 사용자가 업로드한 이력서 파일(PDF)
        
        아래 3개의 인자는 검색시 메타데이터 필터링을 위해 사용됨(e.g. Location=USA)
        location: 근무 희망 위치 ['USA', 'Germany', 'UK']
        remote: 원격 근무 여부 ['True', 'False']
        job_type: 근무 유형 ['fulltime', 'parttime']
    Returns:
        JSONResponse: 업로드된 이력서의 파일 경로
    """
    try:
        file_ext = os.path.splitext(file.filename)[-1]
        file_id = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_id)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 로그 또는 활용 예시
        print(f"[UPLOAD] location={location}, remote={remote}, job_type={job_type}")
        location_cache = location
        remote_cache = remote
        job_type_cache = job_type

        return JSONResponse(content={"resume_path": file_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/matching")
async def run(data: MatchRequest):
    """
    사용자의 이력서를 기반으로 벡터 DB에서 채용공고를 검색하고
    LLM을 이용해 CV, JD 리뷰를 수행하는 함수
    Args:
        data: MatchRequest
    Returns:
        JSONResponse: 
            - JD: 첫 번째 문서(top-similarity)의 채용공고 전문
            - JD_url: 채용공고 URL
            - output: LLM을 통한 CV, JD 리뷰
            - name: 회사 이름
    """
    resume_path = data.resume_path
    output_folder = PROCESSED_DIR

    # PDF를 JPG로 변환 후 저장
    image_paths = convert_pdf_to_jpg(resume_path, output_folder)
    resume_content = []
    # 이력서 각 페이지(이미지)별로 텍스트 변환(Upstage API)
    for image_path in image_paths:
        resume = run_parser(image_path)
        resume_content.append(resume[0])

    resume_content_text = "".join(resume_content)

    # 캐시 저장
    resume_cache[resume_path] = resume_content_text
    print(f"이력서 내용이 캐시에 저장됨: {resume_path}")

    # 채용공고 추천
    res, job_description, job_url, c_name = await matching(resume_content_text, location=location_cache, remote=remote_cache, jobtype=job_type_cache)

    analysis_cache[resume_path] = {"output": res, "JD": job_description, "JD_url": job_url, "name": c_name}
    print(f"분석 결과가 캐시에 저장됨: {resume_path}")

    return {"JD": job_description, "JD_url": job_url, "output": res, "name": c_name}


# /chat - 캐시된 이력서/분석 결과 기반 OpenAI 응답
# langfuse_handler = CallbackHandler(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_SECRET_KEY, host="https://cloud.langfuse.com")


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data["session_id"]
    user_input = data["message"]
    company_name = data.get("company", "")
    resume_path = data.get("resume_path", "")

    if resume_cache[resume_path] is None:
        output_folder = PROCESSED_DIR
        image_paths = convert_pdf_to_jpg(resume_path, output_folder)
        resume_content = []
        for image_path in image_paths:
            resume = run_parser(image_path)
            resume_content.append(resume[0])
        resume_content_text = "".join(resume_content)
    else:
        resume_content_text = resume_cache[resume_path]
    
    print(resume_content_text)
    state = get_session_state(
        session_id,
        job_description=data.get("jd", ""),
        resume=resume_content_text,
        company_name=company_name,
        user_resume=data.get("user_resume", ""),
        route_decision=data.get("route_decision", ""),
    )

    add_user_input_to_state(state, user_input)
    graph, state = await create_graph(state)

    result = await graph.ainvoke(state)
    answer = result["messages"][-1].content
    add_assistant_response_to_state(state, answer)
    return {"response": answer}


@app.post("/mock_chat")
async def chat(request_data: dict = Body(...)):
    message = request_data.get("message", "")
    resume_path = request_data.get("resume_path", "")
    company_name = request_data.get("company_name", "")
    jd = request_data.get("jd", "")

    resume_content = ""
    if resume_path in resume_cache:
        resume_content = resume_cache[resume_path]

    analysis_result = ""
    if resume_path in analysis_cache:
        analysis = analysis_cache[resume_path]
        analysis_result = analysis.get("output", "")
        if not company_name:
            company_name = analysis.get("name", "")
        if not jd:
            jd = analysis.get("JD", "")

    prompt = f"""
        당신은 이력서 개선을 도와주는 JobPT 챗봇입니다. 다음 정보를 바탕으로 질문에 답해주세요.

        회사: {company_name}

        채용 공고: 
        {jd}

        이력서 내용:
        {resume_content if resume_content else "이력서 내용을 가져올 수 없습니다."}

        이력서 분석 결과:
        {analysis_result if analysis_result else "분석 결과를 가져올 수 없습니다."}

        사용자 질문: {message}

        답변을 명확하고 구체적으로, 그리고 친절하게 제공해주세요. 분석 결과를 참고하여 이력서 개선 방향과 채용 공고에 맞는 구체적인 조언을 제시해주세요.
    """

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Build a detailed, professional system prompt in English, including user preferences
        preference_info = []
        if request_data.get("location"):
            preference_info.append(f"Preferred location: {request_data['location']}")
        if request_data.get("remote"):
            preference_info.append(f"Remote work preference: {request_data['remote']}")
        if request_data.get("job_type"):
            preference_info.append(f"Job type: {request_data['job_type']}")
        preference_text = "\n".join(preference_info)

        system_prompt = (
            "You are JobPT, an expert AI resume and career advisor. "
            "Your role is to provide detailed, professional, and actionable feedback to help users improve their resumes and job search strategies. "
            "Always tailor your advice to the user's target job description, company, and personal preferences. "
            "If the user has specified a preferred location, remote work preference, or job type, incorporate these into your analysis and suggestions. "
            "Be specific, objective, and constructive. Use advanced HR and recruiting insights.\n"
            f"{preference_text}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7,
        )
        return {"response": response.choices[0].message.content.strip()}
    except Exception as e:
        print("OpenAI API 호출 오류:", e)
        return {"response": f"AI 응답 생성에 실패했습니다. 오류: {str(e)}"}


# /evaluate - ATS 분석 및 HTML 리포트 반환
class EvaluateRequest(BaseModel):
    resume_path: str
    jd_text: str
    model: int = 1


@app.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    try:
        analyzer = ATSAnalyzer(request.resume_path, request.jd_text, model=request.model)
        html_path = analyzer.run_full_analysis(advanced=True, generate_html=True)
        # HTML 파일을 읽어서 문자열로 반환
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return JSONResponse(content={"html": html_content})
    except Exception as e:
        print(f"ATS 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 개발용 실행 명령
if __name__ == "__main__":
    ### 한국어 BM25 retrieval 추가시 활용
    # nltk.download("punkt")
    # nltk.download("punkt_tab")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
