import json
import re
from utils import extract_score


class KeywordAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        jd_analysis_str = "\n".join([
            "REQUIRED QUALIFICATIONS:\n- " + "\n- ".join(self.analyzer.jd_analysis.get('required_qualifications', [])),
            "PREFERRED QUALIFICATIONS:\n- " + "\n- ".join(self.analyzer.jd_analysis.get('preferred_qualifications', [])),
            "TECHNICAL SKILLS:\n- " + "\n- ".join(self.analyzer.jd_analysis.get('technical_skills', [])),
            "SOFT SKILLS:\n- " + "\n- ".join(self.analyzer.jd_analysis.get('soft_skills', [])),
            "INDUSTRY KNOWLEDGE:\n- " + "\n- ".join(self.analyzer.jd_analysis.get('industry_knowledge', []))
        ])

        top_keywords = sorted(self.analyzer.jd_keywords, key=lambda x: x.get('importance', 0), reverse=True)[:20]
        keywords_str = "\n".join([f"- {kw.get('keyword')} (Importance: {kw.get('importance')}/10, Category: {kw.get('category')})"
                               for kw in top_keywords])

        score_context = self.analyzer._localized_context(
            "how well the resume matches the job description's keywords and requirements",
            "이력서가 채용 공고의 키워드와 요구 사항에 얼마나 부합하는지"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        prompt = f"""
        Analyze how well this resume matches the key requirements and keywords from the job description.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION ANALYSIS:
        {jd_analysis_str}

        TOP KEYWORDS FROM JOB DESCRIPTION:
        {keywords_str}

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please provide a detailed analysis with the following:

        1. TECHNICAL SKILLS MATCH: Evaluate how well the resume matches the required technical skills
        2. QUALIFICATIONS MATCH: Evaluate how well the resume matches required and preferred qualifications
        3. SOFT SKILLS MATCH: Evaluate how well the resume demonstrates the required soft skills
        4. EXPERIENCE MATCH: Evaluate how well the resume satisfies experience requirements
        5. KEYWORD ANALYSIS: Create a table showing matched and missing keywords, with their importance

        For each category, provide specific examples from both the job description and resume.
        Calculate a match percentage for each category, and provide an overall keyword match score.

        {score_instruction}
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        print("[DEBUG] Keywords analysis LLM response:\n", response[:300], "...")

        score = extract_score(response)
        print("[DEBUG] Keywords score:", score)

        self.analyzer.analysis_results['keywords'] = response
        self.analyzer.scores['keywords'] = score


class ExperienceAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        """Analyze how well the resume's experience and qualifications match the job requirements"""
        score_context = self.analyzer._localized_context(
            "how well the candidate's experience and qualifications match the job requirements",
            "후보자의 경력과 자격이 채용 공고의 요구 사항과 얼마나 일치하는지"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        prompt = f"""
        Evaluate how well the candidate's experience and qualifications match the job requirements:
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION:
        {self.analyzer.jd_text}

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please provide a detailed analysis of:
        1. Required years of experience vs. candidate's experience
        2. Required education level vs. candidate's education
        3. Required industry experience vs. candidate's industry background
        4. Required responsibilities vs. candidate's demonstrated capabilities
        5. Required achievements vs. candidate's accomplishments


        For each area, indicate whether the candidate exceeds, meets, or falls short of requirements.
        Provide specific examples from both the job description and resume.


        {score_instruction}
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        print("[DEBUG] Experience analysis LLM response:\n", response[:300], "...")

        score = extract_score(response)
        print("[DEBUG] Experience score:", score)

        self.analyzer.analysis_results['experience'] = response
        self.analyzer.scores['experience'] = score


class FormatAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        """Analyze the resume's format, structure, and readability"""
        score_context = self.analyzer._localized_context(
            "the quality of the resume's format and readability",
            "이력서 형식과 가독성의 품질"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        prompt = f"""
        Evaluate the format, structure, and readability of the following resume:
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please analyze:
        1. Overall organization and structure
        2. Readability and clarity
        3. Use of bullet points, sections, and white space
        4. Consistency in formatting (dates, job titles, etc.)
        5. Grammar, spelling, and punctuation
        6. ATS-friendliness of the format


        Provide specific examples of strengths and weaknesses in the format.
        Suggest specific improvements to make the resume more ATS-friendly and readable.


        {score_instruction}
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        print("[DEBUG] Format analysis LLM response:\n", response[:300], "...")

        score = extract_score(response)
        print("[DEBUG] Format score:", score)

        self.analyzer.analysis_results['format'] = response
        self.analyzer.scores['format'] = score


class ContentAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        """Analyze the quality of content in the resume"""
        score_context = self.analyzer._localized_context(
            "the quality of the resume's content",
            "이력서 콘텐츠의 전반적인 품질"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        prompt = f"""
        Evaluate the quality of content in the following resume:
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please analyze:
        1. Use of strong action verbs and achievement-oriented language
        2. Quantification of achievements (metrics, percentages, numbers)
        3. Specificity vs. vagueness in descriptions
        4. Relevance of included information
        5. Balance between technical details and high-level accomplishments
        6. Presence of clichés or generic statements vs. unique value propositions


        Provide specific examples from the resume for each point.
        Suggest specific improvements to strengthen the content quality.


        {score_instruction}
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        print("[DEBUG] Content analysis LLM response:\n", response[:300], "...")

        score = extract_score(response)
        print("[DEBUG] Content score:", score)

        self.analyzer.analysis_results['content'] = response
        self.analyzer.scores['content'] = score


class ErrorAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        """Check for errors, inconsistencies, and red flags in the resume"""
        score_context = self.analyzer._localized_context(
            "how error-free and consistent the resume is (100 = perfect, no issues)",
            "이력서의 오류 및 일관성 수준(100 = 완벽, 문제 없음)"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        prompt = f"""
        Analyze the following resume for errors, inconsistencies, and potential red flags:
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please identify and explain:
        1. Spelling and grammar errors
        2. Inconsistencies in dates, job titles, or other information
        3. Unexplained employment gaps
        4. Formatting inconsistencies
        5. Potential red flags that might concern employers


        For each issue found, provide the specific text from the resume and suggest a correction.
        If no issues are found in a category, explicitly state that.


        {score_instruction}
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        print("[DEBUG] Errors analysis LLM response:\n", response[:300], "...")

        score = extract_score(response)
        print("[DEBUG] Errors score:", score)

        self.analyzer.analysis_results['errors'] = response
        self.analyzer.scores['errors'] = score


class IndustryAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        """Perform industry and job role specific analysis"""
        # First, identify the industry and job role
        industry_prompt = f"""
        Based on the following job description, identify the specific industry and job role.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION:
        {self.analyzer.jd_text}

        Format your response as a JSON object with this structure:
        {{"industry": "Technology", "job_role": "Software Engineer"}}


        Be specific about both the industry and job role.
        """

        response = self.analyzer.call_llm(industry_prompt, model=self.analyzer.model)

        try:
            json_match = re.search(r'\{\s*"industry"\s*:.+?\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            job_info = json.loads(response)
            industry = job_info.get('industry', 'General')
            job_role = job_info.get('job_role', 'General')
        except Exception as e:
            print(f"Error parsing industry JSON: {e}")
            industry = "Technology"
            job_role = "Professional"

        score_context = self.analyzer._localized_context(
            "how well the resume aligns with this specific industry and role",
            "이력서가 해당 산업과 직무에 얼마나 적합한지"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        industry_analysis_prompt = f"""
        Analyze this resume for a {job_role} position in the {industry} industry.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION:
        {self.analyzer.jd_text}

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please provide an industry-specific analysis considering:
        1. Industry-specific terminology and keywords in the resume
        2. Relevant industry experience and understanding
        3. Industry-specific certifications and education
        4. Industry trends awareness
        5. Industry-specific achievements and metrics


        For each point, evaluate how well the resume demonstrates industry alignment.
        Provide specific recommendations for improving industry relevance.


        {score_instruction}
        """

        response = self.analyzer.call_llm(industry_analysis_prompt, model=self.analyzer.model)
        score = extract_score(response)

        self.analyzer.analysis_results['industry_specific'] = response
        self.analyzer.scores['industry_specific'] = score


class CompetitiveAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze(self):
        """Analyze the competitive position of this resume in the current job market"""
        score_context = self.analyzer._localized_context(
            "how well this resume would compete against other candidates",
            "이력서가 다른 지원자와 비교했을 때 어느 정도 경쟁력을 갖는지"
        )
        score_instruction = self.analyzer._score_instruction_text(score_context)

        prompt = f"""
        Analyze how competitive this resume would be in the current job market for this position.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION:
        {self.analyzer.jd_text}

        RESUME:
        {self.analyzer.preprocessed_cv}

        Please provide a competitive analysis including:


        1. MARKET COMPARISON: How this resume compares to typical candidates for this role
        2. STANDOUT STRENGTHS: The most impressive qualifications compared to the average candidate
        3. COMPETITIVE WEAKNESSES: Areas where the candidate may fall behind competitors
        4. DIFFERENTIATION FACTORS: Unique elements that set this resume apart (positively or negatively)
        5. HIRING PROBABILITY: Assessment of the likelihood of getting an interview (Low/Medium/High)


        Base your analysis on current job market trends and typical qualifications for this role and industry.
        Be honest but constructive in your assessment.


        {score_instruction}
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        score = extract_score(response)

        self.analyzer.analysis_results['competitive'] = response
        self.analyzer.scores['competitive'] = score
        return response