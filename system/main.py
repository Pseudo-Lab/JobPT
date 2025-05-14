from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil
import uuid
import os

from parser import run_parser, convert_pdf_to_jpg
from get_similarity.main import matching
from openai import OpenAI
import uvicorn

from multi_agents.states.states import get_session_state, end_session, add_user_input_to_state, add_assistant_response_to_state
from multi_agents.graph import create_graph

# 캐시 저장소
resume_cache = {}
analysis_cache = {}

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에선 모두 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드 디렉토리 설정
UPLOAD_DIR = "uploaded_resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# /upload - 파일 업로드 및 경로 반환
from fastapi import Form


@app.post("/upload")
async def upload_resume(file: UploadFile = File(...), location: str = Form(""), remote: str = Form("any"), job_type: str = Form("any")):
    try:
        file_ext = os.path.splitext(file.filename)[-1]
        file_id = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_id)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 로그 또는 활용 예시
        print(f"[UPLOAD] location={location}, remote={remote}, job_type={job_type}")

        return JSONResponse(content={"resume_path": file_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# /matching - 이력서 분석 및 JD 매칭
class MatchRequest(BaseModel):
    resume_path: str


@app.post("/matching")
async def run(data: MatchRequest):
    resume_path = data.resume_path
    output_folder = "data"

    image_paths = convert_pdf_to_jpg(resume_path, output_folder)
    resume_content = []
    for image_path in image_paths:
        resume = run_parser(image_path)
        resume_content.append(resume[0])

    resume_content_text = "".join(resume_content)

    # 캐시 저장
    resume_cache[resume_path] = resume_content_text
    print(f"이력서 내용이 캐시에 저장됨: {resume_path}")

    res, job_description, job_url, c_name = matching(resume_content_text)

    analysis_cache[resume_path] = {"output": res, "JD": job_description, "JD_url": job_url, "name": c_name}
    print(f"분석 결과가 캐시에 저장됨: {resume_path}")

    return {"JD": job_description, "JD_url": job_url, "output": res, "name": c_name}


# /chat - 캐시된 이력서/분석 결과 기반 OpenAI 응답
class ChatRequest(BaseModel):
    message: str
    resume_path: Optional[str] = None
    company_name: Optional[str] = None
    jd: Optional[str] = None


from langfuse import Langfuse
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key="pk-lf-ce2e725b-703f-450c-a734-1b8a9274b9e1", secret_key="sk-lf-f2495882-bceb-4b46-ac59-65da8dd8b251", host="https://cloud.langfuse.com"
)


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    session_id = data["session_id"]
    user_input = data["message"]
    company_name = data.get("company_name", "")
    resume_path = data.get("resume_path", "")

    state = get_session_state(
        session_id,
        job_description=data.get("jd", ""),
        resume=resume_cache.get(resume_path, ""),
        company_name=company_name,
        user_resume=data.get("user_resume", ""),
    )

    add_user_input_to_state(state, user_input)
    graph = await create_graph()
    result = await graph.ainvoke(state, config={"callbacks": [langfuse_handler]})
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
from ats_analyzer_improved import ATSAnalyzer
from fastapi.responses import JSONResponse


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
