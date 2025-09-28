CV_PATH = "최재강_이력서.pdf"
MODEL = 1  # 1=OpenAI, 2=Groq, 3=Gemini
ADVANCED = True
GENERATE_HTML = True

# Job description
JD_TEXT = """
AI Lab을 소개해요.음악, 스토리 등 다양한 콘텐츠의 추천과 검색을 위해 고객의 행동과 데이터를 분석하고 이를 바탕으로 AI 모델과 추천 시스템을 설계·학습·운영하는 일을 하고 있어요. 특히 엔터테인먼트 산업에 특화된 AI 기술을 개발하며, 이렇게 만든 모델을 실제 서비스에 적용해 사용자 경험을 높이고 비즈니스 효율을 극대화하는 것이 목표예요. ‍함께 할 업무를 알려드려요.LLM, 생성형 AI, 멀티에이전트 시스템 등 다양한 AI 모델을 연구하고 개발하는 업무를 경험해요. 음악, 스토리 등 콘텐츠 추천 모델을 함께 연구하고 만들어요. ‍텍스트, 오디오, 비디오 등 다양한 데이터를 활용해 모델을 설계하고 학습 시키며 성능을 개선해요. 연구한 모델을 실제 서비스에 적용하고, 안정적으로 운영될 수 있도록 관리해요. 앞으로 성장하며 경험할 수 있는 업무예요.생성형 AI, LLM 등 AI 모델을 직접 연구하고 개발하면서 AI 분야의 전문가로 성장할 수 있어요. 직접 연구한 모델을 기반으로 AI 기반 서비스 기획이나 전략을 수립하며 비즈니스와 기술을 연결하는 역할을 수행할 수 있어요.이런 분이면 더 좋을 것 같아요. 다양한 콘텐츠와 K-pop, 엔터테인먼트 산업에 관심이 많고 이해도가 있으신 분이면 좋아요.특히 직접 웹툰, 웹소설, 영상, 음악 등 디지털 콘텐츠를 즐기고 경험해본 분이면 좋을 것 같아요. 학회나 컨퍼런스에서 논문을 발표하거나 출판해본 경험이 있는 분이면 많은 도움이 될 것 같아요. 원활한 커뮤니케이션과 논리적인 사고로 문제를 해결하는 것을 좋아하시는 분을 환영해요. 영어 또는 다른 외국어 사용에 능숙하시거나 완벽하지 않더라도 두려움이 없으신 분이면 좋을 것 같아요.
인터넷·IT·통신·모바일·게임>빅데이터·AI(인공지능)>인공지능(AI)|인터넷·IT·통신·모바일·게임>응용프로그래머>인공지능(AI)|인터넷·IT·통신·모바일·게임>ERP·시스템분석·설계>인공지능(AI)서비스기획
"""

DEFAULT_SECTION_PATTERNS = {
    'personal_info': r'(Personal\s*Information|Contact|Profile)',
    'summary': r'(Summary|Professional\s*Summary|Profile|Objective)',
    'education': r'(Education|Academic|Qualifications|Degrees)',
    'experience': r'(Experience|Work\s*Experience|Employment|Career\s*History)',
    'skills': r'(Skills|Technical\s*Skills|Competencies|Expertise)',
    'projects': r'(Projects|Key\s*Projects|Professional\s*Projects)',
    'certifications': r'(Certifications|Certificates|Accreditations)',
    'languages': r'(Languages|Language\s*Proficiency)',
    'publications': r'(Publications|Research|Papers)',
    'awards': r'(Awards|Honors|Achievements|Recognitions)'
}

KOREAN_SECTION_PATTERNS = {
    'personal_info': r'(개인\s*정보|인적\s*사항|연락처|프로필)',
    'summary': r'(요약|소개|경력\s*요약|프로필|지원\s*동기)',
    'education': r'(학력|교육|학위|교육\s*사항)',
    'experience': r'(경력|경력\s*사항|직무\s*경험|근무\s*경력|프로젝트\s*경험)',
    'skills': r'(기술|보유\s*기술|핵심\s*역량|스킬|기술\s*역량)',
    'projects': r'(프로젝트|주요\s*프로젝트|연구\s*과제)',
    'certifications': r'(자격증|자격|인증|어학|어학\s*성적)',
    'languages': r'(언어|어학|언어\s*능력|외국어)',
    'publications': r'(논문|발표|출판|연구)',
    'awards': r'(수상|수상\s*경력|수상\s*내역|상훈)'
}

LANGUAGE_SECTION_PATTERNS = {
    'en': DEFAULT_SECTION_PATTERNS,
    'ko': {
        **DEFAULT_SECTION_PATTERNS,
        **KOREAN_SECTION_PATTERNS
    }
}

LANGUAGE_SCORE_TEMPLATES = {
    'en': "Score: {score} points",
    'ko': "점수: {score}점"
}

LANGUAGE_CATEGORY_LABELS = {
    'en': [
        'Keywords', 'Experience', 'Industry Fit', 'Content Quality', 'Format'
    ],
    'ko': [
        '키워드 적합도', '경력 적합도', '산업 적합도', '콘텐츠 품질', '형식'
    ]
}

LANGUAGE_HTML_LABELS = {
    'en': {
        'title': 'Resume ATS Analysis Report',
        'analysis_date': 'Analysis Date',
        'score_breakdown': 'Score Breakdown',
        'executive_summary': 'Executive Summary',
        'ats_results': 'ATS Simulation Results',
        'improvement': 'Recommended Improvements',
        'detailed_analysis': 'Detailed Analysis',
        'keywords_match': 'Keywords Match',
        'experience_match': 'Experience & Qualifications',
        'ats_simulation': 'ATS Simulation',
        'industry_alignment': 'Industry Alignment',
        'content_quality': 'Content Quality',
        'format_quality': 'Format & Readability',
        'error_check': 'Errors & Consistency'
    },
    'ko': {
        'title': '이력서 ATS 분석 보고서',
        'analysis_date': '분석 일시',
        'score_breakdown': '세부 점수 현황',
        'executive_summary': '요약 평가',
        'ats_results': 'ATS 시뮬레이션 결과',
        'improvement': '개선 권장 사항',
        'detailed_analysis': '세부 분석',
        'keywords_match': '키워드 적합도',
        'experience_match': '경력 및 자격 적합도',
        'ats_simulation': 'ATS 시뮬레이션',
        'industry_alignment': '산업 적합도',
        'content_quality': '콘텐츠 품질',
        'format_quality': '형식 및 가독성',
        'error_check': '오류 및 일관성'
    }
}


SCORE_WEIGHTS = {
    'ats_simulation': 0.30,
    'keywords': 0.25,
    'experience': 0.20,
    'industry_specific': 0.15,
    'content': 0.05,
    'format': 0.03,
    'errors': 0.02,
}