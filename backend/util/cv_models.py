"""
JobPT CV Format 데이터 모델

Pydantic 모델을 사용하여 구조화된 CV 데이터를 정의합니다.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# 기본정보
class BasicInfo(BaseModel):
    name: Optional[str] = Field(None, description="이름")
    contact: Optional[str] = Field(None, description="연락처 (이메일, 전화번호 등)")


# 경력 - 주요성과
class Achievement(BaseModel):
    period: Optional[str] = Field(None, description="기간")
    role: Optional[str] = Field(None, description="직책")
    job: Optional[str] = Field(None, description="직무")
    content: Optional[str] = Field(None, description="내용")


# 경력 - 회사별 정보
class Experience(BaseModel):
    company_name: str = Field(..., description="회사명")
    period: Optional[str] = Field(None, description="기간")
    employment_type: Optional[str] = Field(None, description="재직형태 (정규직, 계약직, 인턴 등)")
    job: Optional[str] = Field(None, description="직무")
    achievements: List[Achievement] = Field(default_factory=list, description="주요성과 목록")


# 학력 - 학교별 정보
class Education(BaseModel):
    school_name: str = Field(..., description="학교명")
    period: Optional[str] = Field(None, description="기간")
    graduation_status: Optional[str] = Field(None, description="졸업상태 (졸업, 재학, 중퇴 등)")
    major_degree: Optional[str] = Field(None, description="전공 및 학위")
    content: Optional[str] = Field(None, description="내용")


# 수상/자격증/기타 - 활동별 정보
class AwardCertification(BaseModel):
    activity_name: str = Field(..., description="활동명")
    period: Optional[str] = Field(None, description="기간")
    type: Optional[str] = Field(None, description="타입 (수상, 자격증, 기타 등)")
    content: Optional[str] = Field(None, description="내용")


# 언어 - 언어별 정보
class Language(BaseModel):
    language_name: str = Field(..., description="언어명")
    level: Optional[str] = Field(None, description="수준")
    certification: Optional[str] = Field(None, description="자격증")
    acquisition_date: Optional[str] = Field(None, description="취득날짜")


# 필수 Category 구조
class RequiredCVData(BaseModel):
    basic_info: Optional[BasicInfo] = Field(None, description="기본정보")
    summary: Optional[str] = Field(None, description="간단소개")
    experience: List[Experience] = Field(default_factory=list, description="경력 목록")
    education: List[Education] = Field(default_factory=list, description="학력 목록")
    skills: List[str] = Field(default_factory=list, description="스킬 목록")
    awards_certifications: List[AwardCertification] = Field(default_factory=list, description="수상/자격증/기타 목록")
    languages: List[Language] = Field(default_factory=list, description="언어 목록")
    other_links: List[str] = Field(default_factory=list, description="기타 링크 목록")


# 선택 Category 구조 (필수에 포함되지 않은 나머지)
class OptionalCVData(BaseModel):
    unmapped_content: Optional[str] = Field(None, description="매핑되지 않은 나머지 내용")
    additional_sections: dict = Field(default_factory=dict, description="추가 섹션들")


# 전체 구조화된 CV
class StructuredCV(BaseModel):
    raw_text: str = Field(..., description="전체 파싱된 텍스트")
    required: RequiredCVData = Field(..., description="필수 category")
    optional: OptionalCVData = Field(default_factory=OptionalCVData, description="선택 category")

