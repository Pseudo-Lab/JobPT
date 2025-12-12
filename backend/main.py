from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import uuid
import os

from parser import run_parser
from get_similarity.main import matching
from openai import OpenAI
import uvicorn
import nltk
import logging

from multi_agents.states.states import (
    State,
    get_session_state,
    end_session,
    add_user_input_to_state,
    add_assistant_response_to_state,
)
from multi_agents.graph import create_graph
from configs import *

from langfuse.langchain import CallbackHandler

from ATS_agent.ats_analyzer_improved import ATSAnalyzer
from util.jd_crawler import scrape_jd_from_url

from db.database import engine, Base
from db import models
from routers import auth

# Create database tables
models.Base.metadata.create_all(bind=engine)


# 캐시 저장소
resume_cache = {}
analysis_cache = {}

# 전역 변수로 선언 (함수 내에서 global 키워드 사용)
location_cache = ""
remote_cache = ""
job_type_cache = ""

app = FastAPI(
    title="JobPT",
    description="JobPT Backend Service",
    version="1.0.0",
)

# # Middleware to strip /api prefix for local development
# @app.middleware("http")
# async def strip_api_prefix(request: Request, call_next):
#     if request.url.path.startswith("/api"):
#         request.scope["path"] = request.url.path[4:]
#     response = await call_next(request)
#     return response

# /api prefix를 모든 라우트에 추가
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

# API router를 앱에 등록
app.include_router(api_router)
app.include_router(auth.router)

# 로거 설정
logger = logging.getLogger("jobpt")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("[%(levelname)s] %(asctime)s %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

# CORS 설정
raw = os.environ.get("FRONTEND_CORS_ORIGIN", "")
origins = [o.strip() for o in raw.split(",") if o.strip()] or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
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


@api_router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...), location: str = Form(""), remote: str = Form("any"), job_type: str = Form("any")
):
    """
    사용자의 이력서를 업로드하고, 이력서의 정보를 캐시{file_path}에 저장합니다.

    Args:
        file: 사용자가 업로드한 이력서 파일(PDF)

        아래 3개의 인자는 검색시 메타데이터 필터링을 위해 사용됨(e.g. Location=Korea)
        location: 근무 희망 위치 ['Korea']
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
        global location_cache, remote_cache, job_type_cache
        location_cache = location
        remote_cache = remote
        job_type_cache = job_type

        return JSONResponse(content={"resume_path": file_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/matching")
async def run(data: MatchRequest):
    """
    사용자의 이력서를 기반으로 벡터 DB에서 채용공고를 검색하고
    LLM을 이용해 CV, JD 리뷰를 수행하는 함수
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] /matching start resume_path={data.resume_path}")
    resume_path = data.resume_path

    # PDF를 JPG로 변환 후 저장
    # PDF를 직접 파싱 (JPG 변환 없이)
    resume = run_parser(resume_path)
    resume_content_text = resume[0]  # 첫 번째 반환값이 텍스트

    # 캐시 저장
    resume_cache[resume_path] = resume_content_text
    logger.info(f"[{trace_id}] parsed_pages={len(resume_content_text)} total_chars={len(resume_content_text)}")

    # 채용공고 추천
    # res, job_description, job_url, c_name = await matching(
    #     resume_content_text, location=location_cache, remote=remote_cache, jobtype=job_type_cache
    # )

    jd_summaries, jd_urls, c_names = await matching(resume_content_text, location=location_cache, remote=remote_cache, jobtype=job_type_cache)

    # 첫 번째 결과만 사용 (배열 -> 문자열)
    jd_summary = jd_summaries[0] if isinstance(jd_summaries, list) and jd_summaries else jd_summaries
    jd_url = jd_urls[0] if isinstance(jd_urls, list) and jd_urls else jd_urls
    c_name = c_names[0] if isinstance(c_names, list) and c_names else c_names

    analysis_cache[resume_path] = {
        "output": jd_summary,
        "JD": jd_summary,
        "name": c_name,
    }
    logger.info(f"[{trace_id}] matching success company={c_name} url={jd_url}")

    return {"JD": jd_summary, "output": jd_summary, "JD_url": jd_url, "name": c_name, "trace_id": trace_id}


# /chat - 캐시된 이력서/분석 결과 기반 OpenAI 응답
langfuse_handler = CallbackHandler()


@api_router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data["session_id"]
    user_input = data["message"]
    company_name = data.get("company", "")
    resume_path = data.get("resume_path", "")

    if resume_cache[resume_path] is None:
        # PDF를 직접 파싱 (JPG 변환 없이)
        resume = run_parser(resume_path)
        resume_content_text = resume[0]  # 첫 번째 반환값이 텍스트
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

    result = await graph.ainvoke(state, config={"callbacks": [langfuse_handler]})
    answer = result["messages"][-1].content
    add_assistant_response_to_state(state, answer)
    return {"response": answer}


@api_router.post("/mock_chat")
async def mock_chat(request_data: dict = Body(...)):
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
        from configs import UPSTAGE_API_KEY
        client = OpenAI(
            api_key=UPSTAGE_API_KEY,
            base_url="https://api.upstage.ai/v1"
        )
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
            model="solar-pro2",
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


@api_router.post("/evaluate")
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


# /scrape-jd - JD URL 크롤링
class ScrapeJDRequest(BaseModel):
    url: str


@api_router.post("/scrape-jd")
async def scrape_jd(request: ScrapeJDRequest):
    """
    채용 공고 URL에서 텍스트를 크롤링합니다.

    Args:
        url: 채용 공고 URL

    Returns:
        JSONResponse: {
            "success": bool,
            "text": str,  # 추출된 JD 텍스트
            "site": str,  # 사이트명
            "error": str  # 에러 메시지 (실패시)
        }
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] /scrape-jd start url={request.url}")

    try:
        result = scrape_jd_from_url(request.url)

        if result["success"]:
            logger.info(f"[{trace_id}] scraping success site={result['site']} text_length={len(result['text'])}")
        else:
            logger.warning(f"[{trace_id}] scraping failed error={result['error']}")

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"[{trace_id}] unexpected error: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "text": "",
                "site": "",
                "error": f"서버 오류가 발생했습니다: {str(e)}"
            },
            status_code=500
        )


# 개발용 실행 명령
if __name__ == "__main__":
    ### 한국어 BM25 retrieval 추가시 활용
    # nltk.download("punkt")
    # nltk.download("punkt_tab")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
