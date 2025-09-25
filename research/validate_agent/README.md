# ATS Resume Analyzer

고급 AI 기반 이력서 ATS(Applicant Tracking System) 분석 도구입니다. 이력서와 채용 공고를 비교 분석하여 ATS 통과 가능성을 평가하고 개선 방안을 제시합니다.

## 주요 기능

### 핵심 분석 기능
- **키워드 매칭 분석**: 채용 공고의 핵심 키워드와 이력서 매칭 정도 평가
- **경력 적합도 분석**: 요구 경력 및 자격 요건 충족도 평가
- **형식 및 가독성 분석**: ATS 친화적 형식 및 구조 평가
- **콘텐츠 품질 분석**: 성과 중심 서술 및 정량화 수준 평가
- **산업 적합도 분석**: 해당 산업/직무에 대한 이해도 및 적합성 평가

### 고급 기능
- **다국어 지원**: 한국어/영어 자동 감지 및 분석
- **멀티 LLM 지원**: OpenAI GPT-4, Groq, Google Gemini 선택 가능
- **시각적 보고서**: 레이더 차트와 HTML 기반 상세 보고서
- **맞춤형 개선 제안**: 채용 공고별 구체적 개선 방안 제시

## 파일 구조

```
validate_agent/
├── ats_analyzer_improved.py# 메인 실행 파일
├── ats_analyzer.py         # 핵심 ATS 분석기 클래스
├── analyzers.py            # 개별 분석 모듈들
│                          # - KeywordAnalyzer: 키워드 매칭
│                          # - ExperienceAnalyzer: 경력 분석
│                          # - FormatAnalyzer: 형식 분석
│                          # - ContentAnalyzer: 콘텐츠 품질
│                          # - ErrorAnalyzer: 오류 검사
│                          # - IndustryAnalyzer: 산업 적합도
│                          # - CompetitiveAnalyzer: 경쟁력 분석
├── ats_simulation.enc      # ATS 키워드 시뮬레이션
├── report_generator.py     # HTML/텍스트 보고서 생성
├── config.py              # 설정 및 상수
│                          # - 언어별 패턴 및 템플릿
│                          # - 점수 가중치 설정
├── utils.py               # 유틸리티 함수
│                          # - 텍스트 정규화 및 언어 감지
│                          # - 마크다운 렌더링
│                          # - 폰트 설정
├── llm_handler.py         # LLM API 통합 관리
│                          # - OpenAI, Groq, Gemini 지원
├── upstage_parser.py      # 문서 파싱 (PDF/DOCX)
├── .env                   # API 키 설정 파일
└── requirements.txt       # 패키지 의존성
```

## 설치 방법

### 1. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일을 생성하고 다음 API 키를 설정합니다:

```env
# OpenAI API (GPT-4)
OPENAI_API_KEY=your_openai_api_key_here

# Groq API (선택사항)
GROQ_API_KEY=your_groq_api_key_here

# Google Gemini API (선택사항)
GEMINI_API_KEY=your_gemini_api_key_here

# Upstage Document Parser API
UPSTAGE_API_KEY=your_upstage_api_key_here
```

## 사용 방법

### 기본 실행
```python
python ats_analyzer_improved.py
```

### 커스텀 설정
`config.py`를 수정하여 설정을 변경할 수 있습니다:

```python
# Configuration
CV_PATH = "이력서.pdf"
MODEL = 1               # 1=OpenAI, 2=Groq, 3=Gemini
ADVANCED = True         # 고급 분석 수행 여부
GENERATE_HTML = True    # HTML 보고서 생성 여부

# Job description
JD_TEXT = """
채용 공고 내용...
"""
```

### 프로그래밍 방식 사용
```python
from ats_analyzer import ATSAnalyzer

# 분석기 초기화
analyzer = ATSAnalyzer(
    cv_path="이력서.pdf",
    jd_text="채용 공고 내용...",
    model=1  # 1=OpenAI, 2=Groq, 3=Gemini
)

# 분석 실행
result = analyzer.run_full_analysis(
    advanced=True,       # 고급 분석 포함
    generate_html=True   # HTML 보고서 생성
)
```

## 분석 프로세스

### 1단계: 문서 추출 및 전처리
- Upstage API를 통한 이력서 텍스트 추출
- 언어 자동 감지 (한국어/영어)
- 텍스트 정규화 및 섹션 구조화

### 2단계: 채용 공고 분석
- 필수/우대 자격 요건 추출
- 핵심 키워드 및 중요도 평가
- 기술 스택 및 소프트 스킬 파악

### 3단계: 다면적 분석 수행
- **키워드 매칭**: 정확/부분 일치 키워드 분석
- **경력 적합도**: 경력 연수, 학력, 산업 경험
- **형식 평가**: ATS 친화적 구조 및 일관성
- **콘텐츠 품질**: 정량화, 구체성, 성과 중심성
- **산업 적합도**: 산업별 용어 및 트렌드 이해도

### 4단계: 보고서 생성
- 5개 핵심 지표 레이더 차트
- 섹션별 상세 분석 결과
- 구체적 개선 권장사항
- 경쟁력 평가 및 인터뷰 가능성

## 평가 지표

| 지표 | 가중치 | 설명 |
|------|--------|------|
| 키워드 적합도 | 25% | 채용 공고 키워드와의 매칭 정도 |
| 경력 적합도 | 20% | 요구 경력 및 자격 충족도 |
| 산업 적합도 | 15% | 산업/직무 특화 역량 |
| 콘텐츠 품질 | 5% | 서술의 구체성과 설득력 |
| 형식 | 3% | ATS 친화적 구조 |

## 기술 스택

- **Python 3.8+**
- **LLM Integration**: OpenAI GPT-4.1-mini, Groq oss-120b, Google Gemini-2.5-flash
- **Document Parsing**: Upstage Document Parser API
- **Visualization**: Matplotlib
- **Reporting**: HTML/CSS, Markdown

## 언어 지원

- **한국어**: 완전 지원 (분석, 보고서, UI)
- **영어**: 완전 지원
- **자동 감지**: 이력서와 채용 공고 언어 자동 매칭

## 출력 예시

### HTML 보고서 구성
1. **분석 요약**: 핵심 강점과 개선 필요 사항
2. **레이더 차트**: 5개 핵심 지표 시각화
3. **키워드 분석**:
   - ✅ 일치한 키워드
   - ⚠️ 부분 일치 키워드
   - ❌ 누락된 키워드
4. **섹션별 상세 분석**: 각 평가 항목별 구체적 피드백
5. **개선 권장사항**: 우선순위별 구체적 개선 방안
6. **경쟁력 평가**: 시장 경쟁력 및 인터뷰 가능성