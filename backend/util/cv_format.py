"""
JobPT CV Format 정의 모듈

필수 category와 선택 category를 정의하고,
파싱된 CV 내용을 JobPT format에 매핑하는 기능을 제공합니다.
"""

from typing import Dict, List, Tuple, Optional
import re
from ATS_agent.config import LANGUAGE_SECTION_PATTERNS
from util.cv_models import (
    StructuredCV, RequiredCVData, OptionalCVData,
    BasicInfo, Experience, Education, AwardCertification, Language
)


# JobPT 필수 category 정의 (새로운 구조)
REQUIRED_CATEGORY_KEYS = [
    'basic_info',           # 기본정보 (이름, 연락처)
    'summary',              # 간단소개
    'experience',           # 경력
    'education',            # 학력
    'skills',               # 스킬
    'awards_certifications', # 수상/자격증/기타
    'languages',           # 언어
    'other_links'          # 기타 링크
]

# 기존 섹션 패턴 매핑 (하위 호환성)
LEGACY_SECTION_MAPPING = {
    'personal_info': 'basic_info',
    'summary': 'summary',
    'experience': 'experience',
    'education': 'education',
    'skills': 'skills',
    'certifications': 'awards_certifications',
    'awards': 'awards_certifications',
    'languages': 'languages',
    'projects': 'optional',  # 프로젝트는 선택 category
    'publications': 'optional'  # 논문은 선택 category
}


def get_section_patterns(language: str = 'ko') -> Dict[str, re.Pattern]:
    """
    언어에 맞는 섹션 패턴을 반환합니다.
    
    Args:
        language: 'ko' 또는 'en'
    
    Returns:
        Dict[str, re.Pattern]: 섹션 이름과 컴파일된 정규식 패턴
    """
    patterns = LANGUAGE_SECTION_PATTERNS.get(language, LANGUAGE_SECTION_PATTERNS['ko'])
    return {
        name: re.compile(pattern, re.IGNORECASE)
        for name, pattern in patterns.items()
    }


def extract_sections_from_text(text: str, language: str = None) -> Dict[str, str]:
    """
    텍스트에서 섹션을 추출합니다.
    
    Args:
        text: 파싱된 CV 텍스트
        language: 언어 ('ko' 또는 'en'). None이면 자동 감지
    
    Returns:
        Dict[str, str]: 섹션 이름과 해당 내용
    """
    if not text:
        return {}
    
    if language is None:
        try:
            from ATS_agent.utils import detect_language
            language = detect_language(text)
        except ImportError:
            # fallback: 기본값 'ko' 사용
            language = 'ko'
    
    patterns = get_section_patterns(language)
    sections = {}
    current_section = 'unmapped'  # 매핑되지 않은 섹션
    sections[current_section] = []
    
    lines = text.split('\n')
    for line in lines:
        matched = False
        for section_name, pattern in patterns.items():
            if pattern.search(line):
                current_section = section_name
                if current_section not in sections:
                    sections[current_section] = []
                matched = True
                break
        
        if not matched:
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(line)
    
    # 각 섹션을 문자열로 변환
    result = {}
    for section_name, lines_list in sections.items():
        content = '\n'.join(lines_list).strip()
        if content:  # 빈 섹션은 제외
            result[section_name] = content
    
    return result


def parse_with_llm(raw_text: str, language: str = 'ko') -> StructuredCV:
    """
    LLM을 사용하여 파싱된 텍스트를 구조화된 CV 형태로 변환합니다.
    
    Args:
        raw_text: 전체 파싱된 텍스트
        language: 언어 ('ko' 또는 'en')
    
    Returns:
        StructuredCV: 구조화된 CV 데이터
    """
    try:
        from configs import UPSTAGE_API_KEY
        from openai import OpenAI
        
        client = OpenAI(
            api_key=UPSTAGE_API_KEY,
            base_url="https://api.upstage.ai/v1"
        )
        
        system_prompt = """You are an expert at parsing CV/resume documents and extracting structured information.
Extract the following information from the CV text and return it as a valid JSON object.

Required structure:
{
    "basic_info": {
        "name": "이름",
        "contact": "연락처 (이메일, 전화번호 등)"
    },
    "summary": "간단소개",
    "experience": [
        {
            "company_name": "회사명",
            "period": "기간",
            "employment_type": "재직형태",
            "job": "직무",
            "achievements": [
                {
                    "period": "기간",
                    "role": "직책",
                    "job": "직무",
                    "content": "내용"
                }
            ]
        }
    ],
    "education": [
        {
            "school_name": "학교명",
            "period": "기간",
            "graduation_status": "졸업상태",
            "major_degree": "전공 및 학위",
            "content": "내용"
        }
    ],
    "skills": ["스킬1", "스킬2", ...],
    "awards_certifications": [
        {
            "activity_name": "활동명",
            "period": "기간",
            "type": "타입 (수상, 자격증, 기타 등)",
            "content": "내용"
        }
    ],
    "languages": [
        {
            "language_name": "언어명",
            "level": "수준",
            "certification": "자격증",
            "acquisition_date": "취득날짜"
        }
    ],
    "other_links": ["링크1", "링크2", ...]
}

Return ONLY valid JSON, no additional text."""
        
        user_prompt = f"""Parse the following CV text and extract structured information:

{raw_text}

Return the structured data as JSON following the required structure above."""
        
        try:
            # JSON 모드 시도 (지원되는 경우)
            response = client.chat.completions.create(
                model="solar-pro2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
        except Exception:
            # JSON 모드 미지원시 일반 응답
            response = client.chat.completions.create(
                model="solar-pro2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
            )
        
        import json
        import re
        
        content = response.choices[0].message.content.strip()
        
        # JSON 추출 (코드 블록이나 마크다운 제거)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        parsed_data = json.loads(content)
        
        # Pydantic 모델로 변환
        required_data = RequiredCVData(**parsed_data)
        
        return StructuredCV(
            raw_text=raw_text,
            required=required_data,
            optional=OptionalCVData()
        )
        
    except Exception as e:
        print(f"LLM 파싱 실패: {e}")
        # Fallback: 기본 구조 반환
        return StructuredCV(
            raw_text=raw_text,
            required=RequiredCVData(),
            optional=OptionalCVData(unmapped_content=raw_text)
        )


def map_to_jobpt_format(parsed_sections: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    파싱된 섹션을 JobPT format에 매핑합니다. (하위 호환성 유지)
    
    Args:
        parsed_sections: extract_sections_from_text()로 추출된 섹션 딕셔너리
    
    Returns:
        Dict[str, Dict[str, str]]: {
            "required": {category: content, ...},
            "optional": {category: content, ...},
            "unmapped": "매핑되지 않은 내용"
        }
    """
    required = {}
    optional = {}
    unmapped_parts = []
    
    # 각 섹션을 필수/선택으로 분류
    for section_name, content in parsed_sections.items():
        if section_name == 'unmapped':
            unmapped_parts.append(content)
        else:
            # LEGACY_SECTION_MAPPING을 통해 새로운 구조로 매핑
            mapped_key = LEGACY_SECTION_MAPPING.get(section_name, 'optional')
            if mapped_key == 'optional':
                optional[section_name] = content
            elif mapped_key in REQUIRED_CATEGORY_KEYS:
                required[mapped_key] = content
            else:
                unmapped_parts.append(content)
    
    # unmapped 내용을 하나의 문자열로 합침
    unmapped = '\n\n'.join(unmapped_parts) if unmapped_parts else ""
    
    return {
        "required": required,
        "optional": optional,
        "unmapped": unmapped
    }


def create_structured_cv(
    raw_text: str,
    elements: List[Dict] = None,
    coordinates: List[Dict] = None,
    language: str = None,
    use_llm: bool = True
) -> Dict:
    """
    파싱된 CV를 구조화된 형태로 변환합니다.
    
    Args:
        raw_text: 전체 파싱된 텍스트
        elements: Upstage API의 elements 배열 (선택)
        coordinates: 좌표 정보 (선택)
        language: 언어 ('ko' 또는 'en'). None이면 자동 감지
        use_llm: True면 LLM을 사용하여 구조화, False면 기본 파싱만 수행
    
    Returns:
        Dict: {
            "raw_text": "전체 문자열",
            "structured": StructuredCV 모델 (use_llm=True) 또는 기본 구조 (use_llm=False),
            "elements": [...],
            "coordinates": [...]
        }
    """
    if use_llm:
        # LLM을 사용한 구조화된 파싱
        if language is None:
            try:
                from ATS_agent.utils import detect_language
                language = detect_language(raw_text)
            except ImportError:
                language = 'ko'
        
        structured_cv = parse_with_llm(raw_text, language)
        
        result = {
            "raw_text": raw_text,
            "structured": structured_cv.dict(),  # Pydantic 모델을 dict로 변환
        }
    else:
        # 기본 파싱 (하위 호환성)
        parsed_sections = extract_sections_from_text(raw_text, language)
        structured = map_to_jobpt_format(parsed_sections)
        
        result = {
            "raw_text": raw_text,
            "structured": structured,
        }
    
    if elements is not None:
        result["elements"] = elements
    
    if coordinates is not None:
        result["coordinates"] = coordinates
    
    return result

