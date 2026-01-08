"""
이력서 텍스트를 구조화된 JSON 형식으로 변환하는 모듈
"""
import json
import re
import logging
from typing import Dict, Any, Optional
from langchain_upstage import ChatUpstage
from configs import UPSTAGE_API_KEY, RAG_MODEL

logger = logging.getLogger("jobpt")


def parse_json_loose(text: str) -> dict:
    """
    LLM 출력에서 JSON을 추출하는 함수 (코드펜스, 불완전한 JSON 처리)
    """
    # 코드펜스 제거
    cleaned = re.sub(r"```[a-zA-Z]*\n?|```", "", text).strip()
    # 첫 번째 {...} 블록만 추출
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        raise ValueError("No JSON object found in LLM output")
    obj = m.group(0)
    # 따옴표 없는 키에 따옴표 부여: {sequence: "x"} -> {"sequence": "x"}
    obj = re.sub(r"(\{|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1 "\2":', obj)
    return json.loads(obj)


async def parse_resume_to_structured(resume_text: str) -> Optional[Dict[str, Any]]:
    """
    이력서 텍스트를 구조화된 JSON 형식으로 변환
    
    Args:
        resume_text: 파싱된 이력서 텍스트
        
    Returns:
        구조화된 이력서 데이터 (스키마에 맞는 형식) 또는 None (실패 시)
    """
    if not resume_text or not resume_text.strip():
        return None
    
    llm = ChatUpstage(model=RAG_MODEL, temperature=0, api_key=UPSTAGE_API_KEY)
    
    prompt = f"""다음 이력서 텍스트를 구조화된 JSON 형식으로 변환해주세요.

이력서 텍스트:
{resume_text}

다음 JSON 스키마에 맞춰서 변환해주세요:
{{
  "basic_info": {{
    "name": "string | null",
    "phone": "string | null",
    "email": "string | null",
    "address": "string | null"
  }},
  "summary": "string | null",
  "careers": [
    {{
      "company_name": "string",
      "period": "string | null",
      "employment_type": "string | null",
      "role": "string | null",
      "achievements": []
    }}
  ],
  "educations": [
    {{
      "school_name": "string",
      "period": "string | null",
      "graduation_status": "string | null",
      "major_and_degree": "string | null",
      "content": "string | null"
    }}
  ],
  "skills": ["string"],
  "activities": [
    {{
      "activity_name": "string",
      "period": "string | null",
      "activity_type": "string | null",
      "content": "string | null"
    }}
  ],
  "languages": [
    {{
      "language_name": "string",
      "level": "string | null",
      "certification": "string | null",
      "acquisition_date": "string | null"
    }}
  ],
  "links": ["string"],
  "additional_info": {{}}
}}

주의사항:
- 정보가 없는 필드는 null로 설정
- 배열이 비어있으면 빈 배열 []로 설정
- 정확한 JSON 형식으로만 응답 (추가 설명 없이)
- company_name, school_name, activity_name, language_name은 필수 필드
- skills는 최대 50개까지
- links는 중복 제거된 URL 배열

JSON만 응답해주세요:"""

    try:
        logger.info("[ResumeParser] LLM을 통한 구조화 파싱 시작")
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"[ResumeParser] LLM 응답 수신 완료 (길이: {len(content)} 문자)")
        
        # JSON 파싱
        structured_data = parse_json_loose(content)
        logger.info("[ResumeParser] JSON 파싱 완료")
        
        # 빈 문자열을 null로 변환하는 헬퍼 함수
        def normalize_value(value):
            """빈 문자열이나 공백만 있는 문자열을 null로 변환"""
            if value is None:
                return None
            if isinstance(value, str):
                return value.strip() if value.strip() else None
            return value
        
        # basic_info 정규화
        basic_info_raw = structured_data.get("basic_info", {})
        if isinstance(basic_info_raw, dict):
            basic_info = {
                "name": normalize_value(basic_info_raw.get("name")),
                "phone": normalize_value(basic_info_raw.get("phone")),
                "email": normalize_value(basic_info_raw.get("email")),
                "address": normalize_value(basic_info_raw.get("address")),
            }
        else:
            basic_info = {
                "name": None,
                "phone": None,
                "email": None,
                "address": None
            }
        
        # 기본 구조 검증 및 기본값 설정
        result = {
            "basic_info": basic_info,
            "summary": normalize_value(structured_data.get("summary")),
            "careers": structured_data.get("careers", []),
            "educations": structured_data.get("educations", []),
            "skills": structured_data.get("skills", []),
            "activities": structured_data.get("activities", []),
            "languages": structured_data.get("languages", []),
            "links": structured_data.get("links", []),
            "additional_info": structured_data.get("additional_info", {})
        }
        
        # skills 최대 50개 제한
        if len(result["skills"]) > 50:
            result["skills"] = result["skills"][:50]
        
        logger.info(f"[ResumeParser] 구조화 파싱 완료 - 기본정보: name={result['basic_info'].get('name')}, phone={result['basic_info'].get('phone')}, email={result['basic_info'].get('email')}")
        logger.info(f"[ResumeParser] 경력: {len(result['careers'])}개, 학력: {len(result['educations'])}개, 스킬: {len(result['skills'])}개")
        
        return result
        
    except Exception as e:
        logger.error(f"[ResumeParser] 이력서 구조화 파싱 실패: {e}")
        # 실패 시 기본 구조 반환
        return {
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

