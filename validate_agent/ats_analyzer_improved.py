# %%
import os
import re
import json
import time
import asyncio
import numpy as np
import openai
from groq import Groq
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from dotenv import load_dotenv
import markdown

# 내부 모듈 임포트
from ..system.parser import run_parser
from . import prompts


class ATSAnalyzer:
    """
    Advanced ATS (Applicant Tracking System) Analyzer
    이 클래스는 이력서와 채용 공고를 분석하여 ATS 시스템이 이력서를 어떻게 평가하는지 시뮬레이션하고,
    상세한 피드백과 개선 제안을 제공합니다.
    """

    def __init__(self, cv_path, jd_text, model=1):
        """
        ATS 분석기 초기화

        Args:
            cv_path (str): 이력서 파일 경로 (PDF, DOCX, TXT) 또는 원시 텍스트
            jd_text (str): 채용 공고 텍스트
            model (int): 모델 선택 (1=OpenAI, 2=Groq, 3=Gemini)
        """
        self.cv_path = cv_path
        self.jd_text = jd_text
        self.model = model
        
        # 분석 과정 및 결과를 저장할 변수들
        self.cv_text = ""
        self.preprocessed_cv = ""
        self.structured_cv = {}
        self.jd_analysis = {}
        self.jd_requirements = []
        self.jd_keywords = []
        
        self.analysis_results = {}
        self.scores = {}
        self.final_report = ""
        self.improvement_suggestions = ""
        self.competitive_analysis = ""
        self.optimized_resume = ""
        
        # 성능 및 사용량 추적 변수
        self.llm_call_count = 0
        self.total_tokens = 0
        self.total_time = 0

        # .env 파일에서 API 키 로드 및 LLM 클라이언트 초기화
        load_dotenv()
        self._initialize_llm_clients()

    def _initialize_llm_clients(self):
        """환경 변수에서 API 키를 읽어 LLM 클라이언트를 초기화합니다."""
        self.openai_client = None
        self.groq_client = None
        self.gemini_client = None

        # OpenAI 클라이언트 초기화
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key and openai_api_key != "your_openai_api_key_here":
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        else:
            print("경고: OpenAI API 키가 .env 파일에 없거나 유효하지 않습니다.")

        # Groq 클라이언트 초기화
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key and groq_api_key != "your_groq_api_key_here":
            try:
                # Groq SDK는 현재 동기 방식만 공식 지원하므로,
                # 비동기 호출을 위해 동기 클라이언트를 생성합니다.
                self.groq_client = Groq(api_key=groq_api_key)
            except ImportError:
                print("경고: 'groq' 패키지가 설치되지 않았습니다. `pip install groq`로 설치해주세요.")
            except Exception as e:
                print(f"Groq 클라이언트 초기화 실패: {e}")
        else:
            print("경고: Groq API 키가 .env 파일에 없거나 유효하지 않습니다.")

        # Gemini 클라이언트 초기화 (OpenAI 호환 엔드포인트 사용)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key and gemini_api_key != "your_gemini_api_key_here":
            try:
                # Gemini API를 OpenAI 라이브러리 형식으로 사용하기 위한 설정
                self.gemini_client = openai.AsyncOpenAI(api_key=gemini_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            except Exception as e:
                print(f"Gemini 클라이언트 초기화 실패: {e}")
        else:
            print("경고: Gemini API 키가 .env 파일에 없거나 유효하지 않습니다.")


    async def extract_and_preprocess(self):
        """이력서 파일에서 텍스트를 추출하고 전처리합니다."""
        try:
            # upstage-parser를 사용하여 이력서 내용 추출
            _, _, full_contents = run_parser(self.cv_path)
            text = full_contents
        except Exception as e:
            print(f"이력서 파일 처리 중 오류 발생: {e}")
            text = ""

        self.cv_text = text.strip()
        self.structured_cv = self._extract_resume_sections(self.cv_text)
        self.preprocessed_cv = self._advanced_preprocessing(self.cv_text)
        
        # 채용 공고 분석은 다른 분석의 선행 작업이므로 await로 완료를 기다립니다.
        await self.analyze_job_description()

        print(f"이력서에서 {len(self.cv_text)}자 추출 완료")
        print(f"이력서에서 {len(self.structured_cv)}개의 섹션 식별 완료")
        print(f"채용 공고 분석 완료, {len(self.jd_keywords)}개의 키워드 추출 완료")

    async def analyze_job_description(self):
        """
        채용 공고를 분석하여 요구사항, 키워드 및 기타 중요한 정보를 추출합니다.
        이 단계는 ATS 분석을 특정 직무에 맞게 조정하는 데 매우 중요합니다.
        """
        jd_analysis_prompt = prompts.get_jd_analysis_prompt(self.jd_text)
        
        max_retries = 2
        for attempt in range(max_retries):
            response = await self.call_llm(jd_analysis_prompt)
            
            try:
                self.jd_analysis = self._parse_json_from_llm(response)
                
                # 분석된 JD에서 키워드 및 요구사항 목록 추출
                self.jd_keywords = self.jd_analysis.get('keywords', [])
                self.jd_requirements = (
                    self.jd_analysis.get('required_qualifications', []) +
                    self.jd_analysis.get('preferred_qualifications', []) +
                    self.jd_analysis.get('technical_skills', []) +
                    self.jd_analysis.get('soft_skills', []) +
                    self.jd_analysis.get('industry_knowledge', [])
                )
                print(f"JD 분석 JSON 파싱 성공, {len(self.jd_keywords)}개 키워드 추출")
                return # 성공 시 함수 종료
            except (json.JSONDecodeError, SyntaxError) as e:
                print(f"JD 분석 JSON 파싱 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print("최대 재시도 횟수 초과. 대체용 기본 JD 분석 구조를 생성합니다.")
                    self._create_default_jd_analysis()

    def _create_default_jd_analysis(self):
        """JD 분석 실패 시 기본 더미 데이터를 생성합니다."""
        self.jd_analysis = {
            "required_qualifications": ["Master's degree", "1+ years of experience"],
            "preferred_qualifications": ["PhD", "Industry experience"],
            "key_responsibilities": ["Research", "Development", "Collaboration"],
            "technical_skills": ["Python", "Machine Learning", "Deep Learning"],
            "soft_skills": ["Communication", "Teamwork"],
            "industry_knowledge": ["AI Research", "Software Development"],
            "company_values": ["Innovation", "Collaboration"],
            "keywords": [
                {"keyword": "Python", "importance": 9, "category": "Technical Skill"},
                {"keyword": "Machine Learning", "importance": 8, "category": "Technical Skill"}
            ]
        }
        self.jd_keywords = self.jd_analysis["keywords"]
        self.jd_requirements = (
            self.jd_analysis["required_qualifications"] +
            self.jd_analysis["preferred_qualifications"]
        )

    def _parse_json_from_llm(self, response_text: str):
        """
        LLM 응답에서 JSON 객체를 더 안정적으로 추출하고 파싱합니다.
        - 마크다운 코드 블록(```json ... ```) 제거
        - 불필요한 접두/접미사 제거
        - 흔한 JSON 오류 자동 수정
        """
        # LLM 응답에서 코드 블록(```json ... ```)을 찾아 내용만 추출
        match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if match:
            response_text = match.group(1)
        
        # 첫 '{'와 마지막 '}' 사이의 텍스트를 추출하여 불필요한 접두/접미사 제거
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx+1]

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 1차 시도 실패: {e}. 자동 수정을 시도합니다.")
            # 후행 쉼표(trailing comma)와 같은 흔한 오류 수정
            text = re.sub(r',\s*([}\]])', r'\1', response_text)
            
            try:
                return json.loads(text)
            except json.JSONDecodeError as final_e:
                print(f"JSON 자동 수정 후 파싱 최종 실패: {final_e}")
                # 오류 정보를 포함하여 예외 발생
                raise SyntaxError("LLM으로부터 유효한 JSON을 파싱하는 데 실패했습니다.") from final_e


    def _extract_resume_sections(self, text: str) -> dict:
        """정규식을 사용하여 이력서 텍스트를 구조화된 섹션으로 추출합니다."""
        # 이력서의 일반적인 섹션 제목 패턴
        section_patterns = {
            'personal_info': r'^(Personal\s*Information|Contact|Profile)$',
            'summary': r'^(Summary|Professional\s*Summary|Profile|Objective)$',
            'education': r'^(Education|Academic|Qualifications|Degrees)$',
            'experience': r'^(Experience|Work\s*Experience|Employment|Career\s*History)$',
            'skills': r'^(Skills|Technical\s*Skills|Competencies|Expertise)$',
            'projects': r'^(Projects|Key\s*Projects|Professional\s*Projects)$',
            'certifications': r'^(Certifications|Certificates|Accreditations)$',
            'languages': r'^(Languages|Language\s*Proficiency)$',
            'publications': r'^(Publications|Research|Papers)$',
            'awards': r'^(Awards|Honors|Achievements|Recognitions)$'
        }
        
        sections = {}
        current_section = 'header'  # 첫 섹션 제목이 나오기 전까지의 내용은 헤더로 간주
        sections[current_section] = []

        lines = text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            matched = False
            for section_name, pattern in section_patterns.items():
                # 섹션 제목은 보통 한 줄을 다 차지하므로, 라인 전체가 패턴과 일치하는지 확인
                if re.fullmatch(pattern, line_stripped, re.IGNORECASE):
                    current_section = section_name
                    if current_section not in sections:
                        sections[current_section] = []
                    matched = True
                    break
            
            if not matched:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(line)
        
        # 각 섹션의 라인들을 하나의 텍스트 블록으로 합침
        for section, section_lines in sections.items():
            sections[section] = '\n'.join(section_lines).strip()
            
        return sections

    def _advanced_preprocessing(self, text: str) -> str:
        """이력서 분석을 위한 고급 텍스트 전처리. 불필요한 공백과 줄바꿈을 정리합니다."""
        text = re.sub(r'[ \t]+', ' ', text)  # 여러 공백/탭을 하나의 공백으로
        text = re.sub(r'\n{3,}', '\n\n', text) # 과도한 줄바꿈을 두개로 제한
        return text.strip()

    async def analyze_keywords(self):
        """이력서가 채용 공고의 핵심 용어와 얼마나 일치하는지 분석합니다."""
        prompt = prompts.get_keyword_analysis_prompt(
            jd_analysis=self.jd_analysis,
            jd_keywords=self.jd_keywords,
            resume_text=self.preprocessed_cv
        )
        response = await self.call_llm(prompt)
        print("[DEBUG] 키워드 분석 LLM 응답:\n", response[:200], "...")
        score = self._extract_score(response)
        print("[DEBUG] 키워드 점수:", score)
        self.analysis_results['keywords'] = response
        self.scores['keywords'] = score

    async def analyze_experience_and_qualifications(self):
        """이력서의 경력 및 자격이 직무 요구사항과 얼마나 일치하는지 분석합니다."""
        prompt = prompts.get_experience_analysis_prompt(self.jd_text, self.preprocessed_cv)
        response = await self.call_llm(prompt)
        print("[DEBUG] 경력 분석 LLM 응답:\n", response[:200], "...")
        score = self._extract_score(response)
        print("[DEBUG] 경력 점수:", score)
        self.analysis_results['experience'] = response
        self.scores['experience'] = score

    async def analyze_format_and_readability(self):
        """이력서의 형식, 구조, 가독성을 분석합니다."""
        prompt = prompts.get_format_analysis_prompt(self.preprocessed_cv)
        response = await self.call_llm(prompt)
        print("[DEBUG] 형식 분석 LLM 응답:\n", response[:200], "...")
        score = self._extract_score(response)
        print("[DEBUG] 형식 점수:", score)
        self.analysis_results['format'] = response
        self.scores['format'] = score

    async def analyze_content_quality(self):
        """이력서 내용의 품질을 분석합니다."""
        prompt = prompts.get_content_quality_prompt(self.preprocessed_cv)
        response = await self.call_llm(prompt)
        print("[DEBUG] 내용 품질 분석 LLM 응답:\n", response[:200], "...")
        score = self._extract_score(response)
        print("[DEBUG] 내용 품질 점수:", score)
        self.analysis_results['content'] = response
        self.scores['content'] = score

    async def check_errors_and_consistency(self):
        """이력서의 오류, 불일치, 위험 신호를 확인합니다."""
        prompt = prompts.get_error_check_prompt(self.preprocessed_cv)
        response = await self.call_llm(prompt)
        print("[DEBUG] 오류 분석 LLM 응답:\n", response[:200], "...")
        score = self._extract_score(response)
        print("[DEBUG] 오류 점수:", score)
        self.analysis_results['errors'] = response
        self.scores['errors'] = score

    async def analyze_semantic_keyword_match(self):
        """
        LLM을 사용하여 키워드의 의미적 일치도를 분석하고 점수를 매깁니다.
        기존의 단순 텍스트 매칭 방식인 simulate_ats_filtering을 대체합니다.
        """
        if not self.jd_keywords:
            print("JD 분석에서 키워드를 찾을 수 없어 의미론적 키워드 분석을 건너뛰습니다.")
            self.analysis_results['ats_simulation'] = "JD 분석에서 키워드를 찾을 수 없어 분석에 실패했습니다."
            self.scores['ats_simulation'] = 0
            return

        prompt = prompts.get_semantic_keyword_analysis_prompt(self.jd_keywords, self.preprocessed_cv)
        
        try:
            response_str = await self.call_llm(prompt)
            analysis_data = self._parse_json_from_llm(response_str)

            keyword_matches = analysis_data.get("keyword_matches", [])
            summary = analysis_data.get("semantic_analysis_summary", "요약 정보 없음.")
            
            if not keyword_matches:
                raise ValueError("LLM 응답에서 키워드 매칭 정보를 찾을 수 없습니다.")

            total_importance = sum(kw.get('importance', 5) for kw in keyword_matches)
            if total_importance == 0:
                self.scores['ats_simulation'] = 0
                self.analysis_results['ats_simulation'] = "분석된 키워드의 중요도 점수가 없어 점수를 계산할 수 없습니다."
                return

            matched_score = 0
            status_weights = {'matched': 1.0, 'semantically_present': 0.75, 'missing': 0.0}

            for match in keyword_matches:
                status = match.get('status', 'missing')
                importance = match.get('importance', 5)
                weight = status_weights.get(status, 0.0)
                matched_score += importance * weight
            
            final_score = (matched_score / total_importance) * 100

            # 보고서 생성
            report_parts = [
                f"## ATS Semantic Analysis Results\n",
                f"### Overall Semantic Score: {final_score:.1f}/100\n",
                f"**요약:** {summary}\n",
                "| Keyword | Status | Justification | Importance | Category |",
                "|---|---|---|---|---|"
            ]
            
            status_map = {
                'matched': '✅ Matched',
                'semantically_present': '💡 Semantically Present',
                'missing': '❌ Missing'
            }
            
            for item in sorted(keyword_matches, key=lambda x: x.get('importance', 0), reverse=True):
                status_display = status_map.get(item['status'], item['status'])
                report_parts.append(
                    f"| {item['keyword']} | **{status_display}** | {item['justification']} | {item['importance']}/10 | {item['category']} |"
                )

            self.analysis_results['ats_simulation'] = "\n".join(report_parts)
            self.scores['ats_simulation'] = final_score

        except (json.JSONDecodeError, SyntaxError, ValueError) as e:
            print(f"의미론적 키워드 분석 실패: {e}. 이전 방식으로 대체합니다.")
            self.analysis_results['ats_simulation'] = "의미론적 키워드 분석 중 오류가 발생했습니다."
            self.scores['ats_simulation'] = 20 # 실패 시 기본 점수


    async def analyze_industry_specific(self):
        """산업 및 직무별 특화 분석을 수행합니다."""
        # 1. LLM을 사용하여 산업 및 직무 역할 식별
        industry_prompt = prompts.get_industry_identification_prompt(self.jd_text)
        response = await self.call_llm(industry_prompt)
        
        try:
            job_info = self._parse_json_from_llm(response)
            industry = job_info.get('industry', 'General')
            job_role = job_info.get('job_role', 'General')
        except (json.JSONDecodeError, SyntaxError) as e:
            print(f"산업 정보 JSON 파싱 오류: {e}. 기본값으로 대체합니다.")
            industry, job_role = "Technology", "Professional"

        # 2. 식별된 정보를 바탕으로 산업별 분석 수행
        industry_analysis_prompt = prompts.get_industry_specific_analysis_prompt(
            job_role=job_role,
            industry=industry,
            jd_text=self.jd_text,
            resume_text=self.preprocessed_cv
        )
        response = await self.call_llm(industry_analysis_prompt)
        score = self._extract_score(response)

        self.analysis_results['industry_specific'] = response
        self.scores['industry_specific'] = score

    async def suggest_resume_improvements(self):
        """분석 결과를 바탕으로 이력서 개선을 위한 구체적인 제안을 생성합니다."""
        prompt = prompts.get_improvement_suggestion_prompt(
            jd_text=self.jd_text,
            resume_text=self.preprocessed_cv,
            scores=self.scores
        )
        response = await self.call_llm(prompt)
        self.improvement_suggestions = response
        return response

    async def analyze_competitive_position(self):
        """현재 채용 시장에서 이력서의 경쟁력을 분석합니다."""
        prompt = prompts.get_competitive_analysis_prompt(
            jd_text=self.jd_text,
            resume_text=self.preprocessed_cv
        )
        response = await self.call_llm(prompt)
        # 경쟁력 점수는 다른 점수 형식과 다를 수 있으므로 별도 처리
        score_match = re.search(r'Competitive Score:\s*(\d+)/100', response, re.IGNORECASE)
        if score_match:
            score = int(score_match.group(1))
        else:
            score = self._extract_score(response)
        
        self.analysis_results['competitive'] = response
        self.scores['competitive'] = score
        return response

    async def generate_optimized_resume(self):
        """채용 공고에 맞춰 최적화된 이력서 버전을 생성합니다."""
        prompt = prompts.get_resume_optimization_prompt(
            jd_text=self.jd_text,
            resume_text=self.preprocessed_cv
        )
        response = await self.call_llm(prompt)
        self.optimized_resume = response
        return response

    async def generate_final_score_and_recommendations(self):
        """가중치를 적용한 최종 점수와 전반적인 권장 사항을 생성합니다."""
        # 각 분석 항목에 대한 가중치 정의
        weights = {
            'ats_simulation': 0.30,    # ATS 시뮬레이션이 가장 중요
            'keywords': 0.25,         # 키워드 일치도
            'experience': 0.20,       # 경력 부합도
            'industry_specific': 0.15, # 산업 전문성
            'content': 0.05,          # 내용 품질
            'format': 0.03,           # 형식 및 가독성
            'errors': 0.02,           # 오류 및 일관성
        }
        
        # 가중 평균 점수 계산
        weighted_sum = sum(self.scores.get(cat, 0) * w for cat, w in weights.items() if cat in self.scores)
        used_weights_sum = sum(w for cat, w in weights.items() if cat in self.scores)
        final_score = weighted_sum / used_weights_sum if used_weights_sum > 0 else 0
        self.scores['final'] = final_score

        # 최종 보고서 생성을 위한 프롬프트 호출
        prompt = prompts.get_final_report_prompt(
            jd_analysis=self.jd_analysis,
            scores=self.scores,
            final_score=final_score
        )
        response = await self.call_llm(prompt)
        self.final_report = f"## OVERALL ATS ANALYSIS SCORE: {final_score:.1f}/100\n\n{response}"

    def generate_visual_report(self, output_path="ats_report.html"):
        """차트와 서식이 지정된 분석을 포함하는 시각적인 HTML 보고서를 생성합니다."""
        try:
            # 점수 시각화를 위한 레이더 차트 생성
            chart_base64 = self._create_radar_chart()
            
            # 마크다운을 HTML로 변환하는 헬퍼 함수
            def md_to_html(text: str) -> str:
                if not text:
                    return "<p>내용 없음</p>"
                try:
                    # fenced_code: 코드 블록 지원, tables: 표 지원
                    # nl2br 확장 기능은 표 렌더링과 충돌할 수 있으므로 제거합니다.
                    return markdown.markdown(text, extensions=['fenced_code', 'tables'])
                except Exception as e:
                    print(f"마크다운 변환 오류: {e}")
                    # 오류 발생 시 원본 텍스트를 <pre> 태그로 감싸서 안전하게 표시
                    return f"<pre>{text}</pre>"

            # prompts 모듈의 템플릿을 사용하여 HTML 컨텐츠 생성
            html_content = prompts.get_html_report_template(
                final_score=self.scores.get('final', 0),
                chart_image=chart_base64,
                final_report_md=md_to_html(self.final_report),
                ats_simulation_md=md_to_html(self.analysis_results.get('ats_simulation', '분석 정보 없음')),
                improvements_md=md_to_html(self.improvement_suggestions),
                scores=self.scores,
                analysis_results=self.analysis_results,
                md_to_html_func=md_to_html
            )
            
            # 생성된 HTML을 파일에 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path

        except Exception as e:
            print(f"시각적 보고서 생성 중 오류 발생: {e}")
            return None

    def _create_radar_chart(self) -> str:
        """점수 레이더 차트를 생성하고 base64로 인코딩된 이미지 문자열을 반환합니다."""
        categories = ['Keywords', 'Experience', 'ATS Sim', 'Industry Fit', 'Content', 'Format', 'Errors']
        score_keys = ['keywords', 'experience', 'ats_simulation', 'industry_specific', 'content', 'format', 'errors']
        values = [self.scores.get(key, 0) for key in score_keys]
        
        if len(values) != len(categories):
             print("경고: 차트 생성에 필요한 점수가 부족합니다.")
             return ""

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # 각도 계산 및 플롯 닫기
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        # 플롯 스타일 설정
        ax.plot(angles, values, 'o-', linewidth=2, color='blue')
        ax.fill(angles, values, 'skyblue', alpha=0.25)
        ax.set_thetagrids(np.degrees(angles[:-1]), categories)
        ax.set_ylim(0, 100)
        ax.set_rlabel_position(22.5)
        ax.grid(True)
        plt.title('Resume ATS Analysis Results', size=16, color='blue', y=1.1)

        # 이미지를 메모리 버퍼에 저장하여 base64로 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return img_str

    def generate_text_report(self):
        """분석에 대한 텍스트 기반 보고서를 생성합니다."""
        report = "=== ATS ANALYSIS REPORT ===\n\n"
        report += f"FINAL SCORE: {self.scores.get('final', 0):.1f}/100\n\n"
        report += "SCORE BREAKDOWN:\n"
        for cat in ['keywords', 'experience', 'ats_simulation', 'format', 'content', 'errors', 'industry_specific']:
            report += f"- {cat.replace('_', ' ').title()}: {self.scores.get(cat, 'N/A')}/100\n"
        report += "\nEXECUTIVE SUMMARY:\n"
        # 최종 보고서는 마크다운 형식일 수 있으므로 간단한 텍스트로 변환
        summary_text = re.sub(r'##.*?\n', '', self.final_report)
        report += f"{summary_text}\n\n"
        report += "RECOMMENDED IMPROVEMENTS:\n"
        report += f"{self.improvement_suggestions}\n\n"
        report += "USAGE STATISTICS:\n"
        report += f"- LLM API Calls: {self.llm_call_count}\n"
        report += f"- Total Tokens Used: {self.total_tokens}\n"
        report += f"- Analysis Time: {self.total_time:.2f} seconds\n"
        return report

    async def call_llm(self, prompt: str, model: int = None) -> str:
        """
        선택된 모델에 따라 LLM API를 비동기적으로 호출하고,
        호출 시간, 횟수, 토큰 사용량을 추적합니다.
        """
        if model is None:
            model = self.model
        
        call_start_time = time.time()
        
        try:
            response_content = ""
            if model == 1:
                response_content = await self._call_openai(prompt)
            elif model == 2:
                response_content = await self._call_groq(prompt)
            elif model == 3:
                 response_content = await self._call_gemini(prompt)
            else:
                print(f"오류: 잘못된 모델 선택({model})")
                return self._generate_dummy_response(prompt)
            
            return response_content

        except Exception as e:
            print(f"LLM API 호출 중 심각한 오류 발생 (모델 {model}): {e}")
            return await self._fallback_llm_call(prompt)
        finally:
            # 개별 LLM 호출 시간은 전체 분석 시간에 합산
            pass

    async def _call_openai(self, prompt: str) -> str:
        """OpenAI API를 비동기적으로 호출합니다."""
        if not self.openai_client:
            raise ValueError("OpenAI 클라이언트가 설정되지 않았습니다.")
        
        model="gpt-4.1-nano-2025-04-14"
        print(f"OpenAI model: {model}")
        response = await self.openai_client.chat.completions.create(
            model=model, # 최신 및 더 강력한 모델로 변경
            messages=[
                {"role": "system", "content": "You are an expert resume analyst and ATS specialist. Respond in well-formatted Markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3000 # 더 긴 응답을 위해 토큰 수 증가
        )
        self.llm_call_count += 1
        if response.usage:
            self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content.strip()

    async def _call_groq(self, prompt: str) -> str:
        """Groq API를 호출합니다. (비동기 처리를 위해 asyncio.to_thread 사용)"""
        if not self.groq_client:
            raise ValueError("Groq 클라이언트가 설정되지 않았습니다.")

        model="meta-llama/llama-4-maverick-17b-128e-instruct"
        print(f"Groq model: {model}")
        # Groq의 동기 SDK를 비동기 이벤트 루프에서 블로킹 없이 실행
        def sync_groq_call():
            return self.groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert resume analyst and ATS specialist. Respond in well-formatted Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000,
                top_p=1,
                stream=False
            )
        
        completion = await asyncio.to_thread(sync_groq_call)

        self.llm_call_count += 1
        if completion.usage:
            self.total_tokens += completion.usage.total_tokens
        return completion.choices[0].message.content.strip()
        
    async def _call_gemini(self, prompt: str) -> str:
        """Gemini API를 비동기적으로 호출합니다. (OpenAI 호환)"""
        if not self.gemini_client:
            raise ValueError("Gemini 클라이언트가 설정되지 않았습니다.")
        model="gemini-2.5-flash-preview-05-20"
        print(f"Gemini model: {model}")
        response = await self.gemini_client.chat.completions.create(
            model=model, # 모델명은 실제 Gemini 모델에 맞게 확인 필요
            messages=[
                {"role": "system", "content": "You are an expert resume analyst and ATS specialist. Respond in well-formatted Markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        self.llm_call_count += 1
        if hasattr(response, 'usage') and response.usage:
            self.total_tokens += response.usage.total_tokens
        
        # Gemini API가 안전 필터 등에 의해 비어있는 응답을 보낼 경우를 대비한 방어 코드
        choice = response.choices[0]
        if choice.message.content is None:
            finish_reason = getattr(choice, 'finish_reason', 'N/A')
            print(f"경고: Gemini API가 비어 있는 콘텐츠를 반환했습니다. 종료 사유: {finish_reason}")
            # 안전 설정 등으로 인해 콘텐츠가 반환되지 않은 경우, 사용자에게 정보를 제공하고 비어 있는 문자열을 반환합니다.
            return f"Gemini API가 콘텐츠를 반환하지 않았습니다. 종료 사유: {finish_reason}"
        
        return choice.message.content.strip()

    async def _fallback_llm_call(self, prompt: str) -> str:
        """주 LLM 호출 실패 시 대체 가능한 다른 LLM을 순서대로 호출합니다."""
        print("주요 LLM 호출 실패. 대체 모델을 시도합니다...")
        
        # 시도해볼 모델 목록 (현재 모델 제외)
        fallback_models = {
            1: self._call_openai,
            2: self._call_groq,
            3: self._call_gemini,
        }
        
        for model_num, call_func in fallback_models.items():
            if model_num == self.model:
                continue
            
            try:
                print(f"{model_num}번 모델로 대체 호출을 시도합니다...")
                return await call_func(prompt)
            except Exception as e:
                print(f"{model_num}번 모델 호출 실패: {e}")
                continue

        print("사용 가능한 모든 LLM 클라이언트 호출에 실패했습니다. 더미 응답을 생성합니다.")
        return self._generate_dummy_response(prompt)

    def _generate_dummy_response(self, prompt: str) -> str:
        """API 호출 실패 또는 API 키 부재 시 테스트용 더미 응답을 생성합니다."""
        print("경고: 더미 응답을 생성합니다. 실제 분석 결과가 아닙니다.")
        
        # JSON 응답을 기대하는 프롬프트인지 확인
        if "json" in prompt.lower():
            return '```json\n{"message": "This is a dummy JSON response.", "score": 50}\n```'
        
        return "This is a dummy response for testing purposes. In a real scenario, this would contain a detailed analysis based on your prompt.\n\nScore: 50 points"

    def _extract_score(self, response_text: str) -> int:
        """LLM 응답 텍스트에서 점수를 지능적으로 추출합니다."""
        # 다양한 점수 형식 패턴 정의 (가장 구체적인 것부터)
        patterns = [
            r'Score:\s*(\d{1,3})\s*points',
            r'Score:\s*(\d{1,3})',
            r'score of\s*(\d{1,3})',
            r'rated at\s*(\d{1,3})',
            r'(\d{1,3})\s*/\s*100',
            r'(\d{1,3})\s*out of\s*100'
        ]

        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                return max(0, min(100, score)) # 점수를 0-100 사이로 보정

        # 텍스트에서 점수 추출 실패 시, JSON 파싱 시도
        try:
            data = self._parse_json_from_llm(response_text)
            if 'overall_score' in data and isinstance(data['overall_score'], int):
                return max(0, min(100, data['overall_score']))
            if 'score' in data and isinstance(data['score'], int):
                return max(0, min(100, data['score']))
        except (SyntaxError, json.JSONDecodeError, TypeError, KeyError):
            pass # JSON 파싱에 실패하면 무시하고 계속 진행

        print(f"경고: 응답에서 점수를 추출하지 못했습니다. 기본값 50을 사용합니다. 응답: '{response_text[:100]}...'")
        return 50

    async def run_full_analysis(self, advanced=True, generate_html=True):
        """
        전체 이력서 분석을 비동기적으로 실행하여 성능을 최적화합니다.

        Args:
            advanced (bool): 고급 분석(ATS 시뮬레이션, 경쟁력 분석 등) 실행 여부
            generate_html (bool): HTML 보고서 생성 여부

        Returns:
            str: 생성된 보고서의 경로 또는 텍스트 보고서 내용
        """
        analysis_start_time = time.time()
        print("ATS 분석을 시작합니다...")

        # 1. 전처리 및 JD 분석 (순차 실행 필요)
        await self.extract_and_preprocess()
        print(f"채용 공고별 특화된 {len(self.jd_keywords)}개의 키워드를 바탕으로 분석을 진행합니다...")

        # 2. 병렬 실행할 분석 작업 목록 생성
        # LLM을 호출하는 비동기 작업들
        llm_tasks = [
            self.analyze_keywords(),
            self.analyze_experience_and_qualifications(),
            self.analyze_format_and_readability(),
            self.analyze_content_quality(),
            self.check_errors_and_consistency(),
        ]
        if advanced:
            print("고급 분석을 병렬로 실행합니다...")
            llm_tasks.extend([
                self.analyze_industry_specific(),
                self.analyze_competitive_position(),
                self.analyze_semantic_keyword_match(),
            ])
        
        # 3. asyncio.gather를 사용하여 LLM 호출을 병렬로 실행
        await asyncio.gather(*llm_tasks)
        
        # 4. LLM 호출이 없는 순수 계산 작업 실행 (병렬 처리 후)
        # if advanced:
        #     await self.simulate_ats_filtering() # 이 함수는 이제 analyze_semantic_keyword_match로 대체됨

        # 5. 후속 작업 (순차 실행)
        print("개선 제안 사항을 생성합니다...")
        await self.suggest_resume_improvements()
        
        print("최적화된 이력서를 생성합니다...")
        await self.generate_optimized_resume()

        print("최종 점수 및 보고서를 생성합니다...")
        await self.generate_final_score_and_recommendations()

        self.total_time = time.time() - analysis_start_time
        print(f"분석 완료. 총 소요 시간: {self.total_time:.1f}초")
        self.print_usage_statistics()

        # 6. 최종 보고서 생성
        if generate_html:
            print("시각적인 HTML 보고서를 생성합니다...")
            report_path = self.generate_visual_report()
            print(f"HTML 보고서 생성 완료: {report_path}")
            return report_path
        else:
            return self.generate_text_report()

    def print_usage_statistics(self):
        """콘솔에 사용 통계를 출력합니다."""
        print("\n===== USAGE STATISTICS =====")
        print(f"LLM API Calls: {self.llm_call_count}")
        print(f"Total Tokens Used: {self.total_tokens}")
        print(f"Analysis Time: {self.total_time:.2f} seconds")

        print("\n===== SCORE BREAKDOWN =====")
        print(f"Final ATS Score: {self.scores.get('final', 0):.1f}/100")
        print(f"Keywords Match: {self.scores.get('keywords', 0)}/100")
        print(f"Experience Match: {self.scores.get('experience', 0)}/100")
        print(f"ATS Simulation (Semantic): {self.scores.get('ats_simulation', 0):.1f}/100")
        print(f"Format & Readability: {self.scores.get('format', 0)}/100")
        print(f"Content Quality: {self.scores.get('content', 0)}/100")
        print(f"Errors & Consistency: {self.scores.get('errors', 0)}/100")
        print(f"Industry Alignment: {self.scores.get('industry_specific', 0)}/100")
        print("============================\n")


async def main():
    """
    ATS 분석기 실행을 위한 메인 함수.
    사용자는 이 함수 내의 설정값만 수정하면 됩니다.
    """
    # 1. 분석할 이력서 파일의 경로를 지정하세요.
    # 파일의 절대경로를 입력하세요.
    cv_path = "GJS/JobPT/validate_agent/OpenAI_Solutions_Architect,_Digital_Natives_segment_CV.pdf" 
    
    # 2. 사용할 AI 모델을 선택하세요. (1: OpenAI, 2: Groq, 3: Gemini)
    # .env 파일에 해당 모델의 API 키가 설정되어 있어야 합니다.
    # 2번의 Groq의 경우 무료 tier는 병렬 처리 시 문제가 발생하므로 paid tier로 업그레이드 후 사용 가능능
    model = 1
    
    # 3. 고급 분석(경쟁력, 산업 적합도 등)을 실행할지 여부를 선택하세요.
    advanced = True 
    
    # 4. 최종 리포트를 HTML 파일로 생성할지 여부를 선택하세요.
    # False로 설정하면, 콘솔에 텍스트 요약본만 출력됩니다.
    generate_html = True  

    # 5. 아래에 분석할 채용 공고(Job Description) 전문을 복사하여 붙여넣으세요.
    jd_text = """
About the team

The Solutions Architecture team is responsible for ensuring the safe and effective deployment of Generative AI applications for developers and enterprises. We act as a trusted advisor and thought partner for our customers, working to build an effective backlog of GenAI use cases for their industry and drive them to production through strong technical guidance. As a Solutions Architect in the Digital Natives segment, you'll help large and highly technical companies transform their business through solutions such as customer service, automated content generation, contextual search, personalization, and novel applications that make use of our newest, most exciting models.

About the role

We are looking for a driven solutions leader with a product mindset to partner with our customers and ensure they achieve tangible business value with GenAI. You will pair with senior customer leaders to establish a GenAI strategy and identify the highest value applications. You'll then partner with their engineering and product teams to move from prototype through production. You'll take a holistic view of their needs and design an enterprise architecture using OpenAI API and other services to maximize customer value. You will collaborate closely with Sales, Solutions Engineering, Applied Research, and Product teams.

This role is based in Seoul, South Korea. We use a hybrid work model of 3 days in the office per week and offer relocation assistance to new employees.

In this role, you will:

Deeply embed with our most sophisticated and technical platform customers as the technical lead, serving as their technical thought partner to ideate and build novel applications on our API.

Work with senior customer stakeholders to identify the best applications of GenAI in their industry and to build/qualify a comprehensive backlog to support their AI roadmap.

Intervene directly to accelerate customer time to value through building hands-on prototypes and/or by delivering impactful strategic guidance.

Forge and manage relationships with our customers' leadership and stakeholders to ensure the successful deployment and scale of their applications.

Contribute to our open-source developer and enterprise resources.

Scale the Solutions Architect function through sharing knowledge, codifying best practices, and publishing notebooks to our internal and external repositories.

Validate, synthesize, and deliver high-signal feedback to the Product, Engineering, and Research teams.

You'll thrive in this role if you:

Have 5+ years of technical consulting (or equivalent) experience, bridging technical teams and senior business stakeholders.

Are an effective and polished communicator who can translate business and technical topics to all audiences.

Are proficient in both Korean and English. This is essential to effectively perform key responsibilities such as partnering with customers, driving the sales cycle, managing accounts, collaborating with cross-functional teams, and communicating with headquarters

Have led complex implementations of Generative AI/traditional ML solutions and have knowledge of network/cloud architecture.

Have industry experience in programming languages like Python or Javascript.

Own problems end-to-end and are willing to pick up whatever knowledge you're missing to get the job done.

Have a humble attitude, an eagerness to help your colleagues, and a desire to do whatever it takes to make the team succeed.

Are an effective, high throughput operator who can drive multiple concurrent projects and prioritize ruthlessly. 

About OpenAI

OpenAI is an AI research and deployment company dedicated to ensuring that general-purpose artificial intelligence benefits all of humanity. We push the boundaries of the capabilities of AI systems and seek to safely deploy them to the world through our products. AI is an extremely powerful tool that must be created with safety and human needs at its core, and to achieve our mission, we must encompass and value the many different perspectives, voices, and experiences that form the full spectrum of humanity. 

We are an equal opportunity employer, and we do not discriminate on the basis of race, religion, color, national origin, sex, sexual orientation, age, veteran status, disability, genetic information, or other applicable legally protected characteristic.

For additional information, please see OpenAI's Affirmative Action and Equal Employment Opportunity Policy Statement.

Qualified applicants with arrest or conviction records will be considered for employment in accordance with applicable law, including the San Francisco Fair Chance Ordinance, the Los Angeles County Fair Chance Ordinance for Employers, and the California Fair Chance Act. For unincorporated Los Angeles County workers: we reasonably believe that criminal history may have a direct, adverse and negative relationship with the following job duties, potentially resulting in the withdrawal of a conditional offer of employment: protect computer hardware entrusted to you from theft, loss or damage; return all computer hardware in your possession (including the data contained therein) upon termination of employment or end of assignment; and maintain the confidentiality of proprietary, confidential, and non-public information. In addition, job duties require access to secure and protected information technology systems and related data security obligations.

We are committed to providing reasonable accommodations to applicants with disabilities, and requests can be made via this link.

OpenAI Global Applicant Privacy Policy

At OpenAI, we believe artificial intelligence has the potential to help people solve immense global challenges, and we want the upside of AI to be widely shared. Join us in shaping the future of technology.
"""

    analyzer = ATSAnalyzer(cv_path, jd_text, model=model)
    result = await analyzer.run_full_analysis(advanced=advanced, generate_html=generate_html)

    if not generate_html:
        print("\n=== TEXT REPORT ===")
        print(result)
    else:
        print(f"\n분석 완료! 보고서가 저장된 경로: {result}")
        print("웹 브라우저에서 HTML 파일을 열어 전체 보고서를 확인하세요.")

if __name__ == "__main__":
    import time
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"\n총 구동 시간: {end_time - start_time:.2f}초")


# %%
