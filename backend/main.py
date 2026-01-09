from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import uuid
import os
import json
import traceback

from util.parser import run_parser
from util.resume_structured_parser import parse_resume_to_structured
from get_similarity.main import matching
from openai import OpenAI
import uvicorn
import logging

from multi_agents.states.states import State
from multi_agents.graph import create_graph
from langchain_core.messages import HumanMessage
from configs import *

from langfuse.langchain import CallbackHandler

from ATS_agent.ats_analyzer_improved import ATSAnalyzer
from util.jd_crawler import crawl_jd_from_url

from db.database import engine, Base
from db import models
from routers import auth

# Create database tables
models.Base.metadata.create_all(bind=engine)


# 캐시 저장소
resume_cache = {}
resume_structured_cache = {}  # 구조화된 이력서 데이터 캐시
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

# auth router는 먼저 등록 (prefix 없음)
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
        error_traceback = traceback.format_exc()
        logger.error(f"[UPLOAD ERROR] Failed to upload resume: {str(e)}")
        logger.error(f"[UPLOAD ERROR] Filename: {file.filename if file else 'None'}")
        logger.error(f"[UPLOAD ERROR] Location: {location}, Remote: {remote}, Job Type: {job_type}")
        logger.error(f"[UPLOAD ERROR] Traceback:\n{error_traceback}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload resume: {str(e)}"
        )


@api_router.post("/matching")
async def run(data: MatchRequest):
    """
    사용자의 이력서를 기반으로 벡터 DB에서 채용공고를 검색하고
    LLM을 이용해 CV, JD 리뷰를 수행하는 함수
    """
    trace_id = str(uuid.uuid4())
    resume_path = data.resume_path
    logger.info(f"[{trace_id}] /matching start resume_path={resume_path}")

    if not resume_path:
        raise HTTPException(status_code=400, detail="resume_path is required.")
    if not os.path.exists(resume_path):
        raise HTTPException(status_code=400, detail="resume_path file not found.")

    # PDF를 JPG로 변환 후 저장
    # PDF를 직접 파싱 (JPG 변환 없이)
    resume = run_parser(resume_path)
    resume_content_text = resume[0]  # 첫 번째 반환값이 텍스트

    # 캐시 저장 (기존 문자열 저장)
    resume_cache[resume_path] = resume_content_text
    logger.info(f"[{trace_id}] parsed_pages={len(resume_content_text)} total_chars={len(resume_content_text)}")

    # 구조화된 데이터 생성 및 저장
    try:
        if resume_path not in resume_structured_cache or resume_structured_cache[resume_path] is None:
            structured_resume = await parse_resume_to_structured(resume_content_text)
            if structured_resume:
                resume_structured_cache[resume_path] = structured_resume
                logger.info(f"[{trace_id}] structured resume data saved")
                # 구조화된 이력서 결과를 JSON 형식으로 로그 출력
                logger.info(f"[{trace_id}] ========== 구조화된 이력서 파싱 결과 ==========")
                logger.info(f"[{trace_id}] {json.dumps(structured_resume, ensure_ascii=False, indent=2)}")
                logger.info(f"[{trace_id}] ============================================")
    except Exception as e:
        logger.warning(f"[{trace_id}] failed to parse structured resume: {e}")
        # 구조화 파싱 실패해도 기존 로직은 계속 진행

    # 채용공고 추천
    # res, job_description, job_url, c_name = await matching(
    #     resume_content_text, location=location_cache, remote=remote_cache, jobtype=job_type_cache
    # )

    jd_summaries, jd_urls, c_names = await matching(
        resume_content_text, location=location_cache, remote=remote_cache, jobtype=job_type_cache
    )

    logger.info(f">>>>"*30)
    logger.info(f"[{trace_id}] jd_summaries={jd_summaries}")
    logger.info(f"[{trace_id}] jd_urls={jd_urls}")
    logger.info(f"[{trace_id}] c_names={c_names}")


    def to_list(value):
        if isinstance(value, list):
            return value
        if value is None:
            return []
        if isinstance(value, str) and not value.strip():
            return []
        return [value]

    def normalize_text(value: str) -> str:
        return " ".join(value.split()).strip().lower()

    def deduplicate(recs):
        seen_urls = set()
        seen_jds = set()
        unique = []
        for rec in recs:
            url = rec.get("job_url")
            normalized_url = url.strip().lower() if isinstance(url, str) else None
            jd_text = rec.get("JD")
            normalized_jd = normalize_text(jd_text) if isinstance(jd_text, str) else None

            if normalized_url and normalized_url in seen_urls:
                continue
            if normalized_jd and normalized_jd in seen_jds:
                continue

            if normalized_url:
                seen_urls.add(normalized_url)
            if normalized_jd:
                seen_jds.add(normalized_jd)
            unique.append(rec)
        return unique

    summaries_list = to_list(jd_summaries)
    urls_list = to_list(jd_urls)
    names_list = to_list(c_names)

    recommendations = []
    for summary, url, name in zip(summaries_list, urls_list, names_list):
        recommendations.append(
            {
                "JD": summary,
                "job_url": url,
                "company": name,
            }
        )

    deduped_recommendations = deduplicate(recommendations)
    primary = deduped_recommendations[0] if deduped_recommendations else {}

    analysis_cache[resume_path] = {
        "output": primary.get("JD", ""),
        "JD": primary.get("JD", ""),
        "name": primary.get("company", ""),
        "recommendations": deduped_recommendations,
    }

    logger.info(
        f"[{trace_id}] matching success results={len(deduped_recommendations)} "
        f"primary_company={primary.get('company', '')} url={primary.get('job_url', '')}"
    )

    return {
        "recommendations": deduped_recommendations,
        "primary": primary,
        "trace_id": trace_id,
    }


# /chat - 캐시된 이력서/분석 결과 기반 OpenAI 응답
langfuse_handler = CallbackHandler()

@api_router.post("/chat")
async def chat(request: Request):
    """
    채팅 엔드포인트 - LangGraph의 MemorySaver를 사용한 자동 상태 관리
    
    - thread_id (session_id)로 세션 구분
    - 상태는 자동으로 저장/복원됨
    - messages는 add_messages reducer로 자동 누적
    """
    data = await request.json()
    session_id = data["session_id"]
    user_input = data["message"]
    company_name = data.get("company", "")
    resume_path = data.get("resume_path", "")

    # 이력서 캐시 확인
    if resume_path not in resume_cache or resume_cache[resume_path] is None:
        resume = run_parser(resume_path)
        resume_content_text = resume[0]
        resume_cache[resume_path] = resume_content_text
        
        # 구조화된 데이터 생성 및 저장
        try:
            if resume_path not in resume_structured_cache or resume_structured_cache[resume_path] is None:
                structured_resume = await parse_resume_to_structured(resume_content_text)
                if structured_resume:
                    resume_structured_cache[resume_path] = structured_resume
                    # 구조화된 이력서 결과를 JSON 형식으로 로그 출력
                    logger.info(f"[CHAT] ========== 구조화된 이력서 파싱 결과 ==========")
                    logger.info(f"[CHAT] resume_path={resume_path}")
                    logger.info(f"[CHAT] {json.dumps(structured_resume, ensure_ascii=False, indent=2)}")
                    logger.info(f"[CHAT] ============================================")
        except Exception as e:
            logger.warning(f"[CHAT] failed to parse structured resume: {e}")
            # 구조화 파싱 실패해도 기존 로직은 계속 진행
    else:
        resume_content_text = resume_cache[resume_path]

    print(f"[DEBUG] Resume content length: {len(resume_content_text)}")

    # Graph 생성 (한 번만 생성, checkpointer 포함)
    graph = create_graph()

    # 초기 상태 구성 (사용자 메시지 추가)
    input_state: State = {
        "messages": [HumanMessage(content=user_input)],
        "job_description": data.get("jd", ""),
        "resume": resume_content_text,
        "company_name": company_name,
        "next_agent": "",
        "agent_outputs": {},
        "final_answer": "",
        "github_url": "",
        "blog_url": "",
    }

    # thread_id를 config에 전달하여 세션별 상태 관리
    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": [langfuse_handler]
    }

    # Graph 실행 (상태는 자동으로 저장/복원됨)
    result = await graph.ainvoke(input_state, config=config)
    
    # 마지막 AI 메시지 추출
    answer = result["messages"][-1].content
    
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


# /resume/structured - 구조화된 이력서 데이터 조회
class StructuredResumeRequest(BaseModel):
    resume_path: str


@api_router.post("/resume/structured")
async def get_structured_resume(request: StructuredResumeRequest):
    """
    구조화된 이력서 데이터를 조회합니다.

    Args:
        resume_path: 이력서 파일 경로

    Returns:
        JSONResponse: 구조화된 이력서 데이터 (스키마에 맞는 형식)
    """
    resume_path = request.resume_path
    
    if not resume_path:
        raise HTTPException(status_code=400, detail="resume_path is required.")
    
    # 캐시에서 조회
    if resume_path in resume_structured_cache:
        structured_data = resume_structured_cache[resume_path]
        if structured_data:
            return JSONResponse(content=structured_data)
    
    # 캐시에 없으면 텍스트에서 생성 시도
    if resume_path in resume_cache:
        try:
            resume_content_text = resume_cache[resume_path]
            structured_resume = await parse_resume_to_structured(resume_content_text)
            if structured_resume:
                resume_structured_cache[resume_path] = structured_resume
                return JSONResponse(content=structured_resume)
        except Exception as e:
            logger.warning(f"failed to parse structured resume: {e}")
    
    # 모두 실패 시 기본 구조 반환
    default_structured = {
        "basic_info": {
            "name": None,
            "phone": None,
            "email": None,
            "address": None
        },
        "summary": None,
        "careers": [],
        "educations": [],
        "skills": [],
        "activities": [],
        "languages": [],
        "links": [],
        "additional_info": {}
    }
    return JSONResponse(content=default_structured)


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
        result = crawl_jd_from_url(request.url)

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

# API router를 앱에 등록 (모든 라우트 정의 후에 등록해야 함)
app.include_router(api_router)


# 개발용 실행 명령
if __name__ == "__main__":
    ### 한국어 BM25 retrieval 추가시 활용
    # nltk.download("punkt")
    # nltk.download("punkt_tab")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)