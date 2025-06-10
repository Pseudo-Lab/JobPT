"""
ATS 분석기에서 사용하는 모든 LLM 프롬프트와 HTML 템플릿을 관리하는 모듈입니다.
이 파일은 직접 실행하는 것이 아니라, ats_analyzer_improved.py에서 라이브러리처럼 가져와 사용합니다.
"""
from datetime import datetime

def get_jd_analysis_prompt(jd_text):
    """채용 공고 분석을 위한 프롬프트를 반환합니다."""
    return f"""
    Perform a detailed analysis of this job description to extract all information that would be used by an ATS system.

    JOB DESCRIPTION:
    {jd_text}

    Please provide a comprehensive analysis with the following components:

    1. REQUIRED QUALIFICATIONS: All explicitly stated required qualifications (education, experience, certifications, etc.)
    2. PREFERRED QUALIFICATIONS: All preferred or desired qualifications that are not strictly required
    3. KEY RESPONSIBILITIES: The main job duties and responsibilities
    4. TECHNICAL SKILLS: All technical skills, tools, languages, frameworks, etc. mentioned
    5. SOFT SKILLS: All soft skills, personal qualities, and character traits mentioned
    6. INDUSTRY KNOWLEDGE: Required industry-specific knowledge or experience
    7. COMPANY VALUES: Any company values or culture fit indicators mentioned

    Format your response as a valid JSON object with these categories as keys, and arrays of strings as values.
    Also include a "keywords" array with all important keywords from the job description, each with an importance score from 1-10 and a category.

    The JSON must be properly formatted with no errors. Make sure all quotes are properly escaped and all arrays and objects are properly closed.

    Example format:
    ```json
    {{
      "required_qualifications": ["Bachelor's degree in Computer Science", "5+ years of experience"],
      "preferred_qualifications": ["Master's degree", "Experience with cloud platforms"],
      "key_responsibilities": ["Develop software applications", "Debug and troubleshoot issues"],
      "technical_skills": ["Python", "JavaScript", "AWS"],
      "soft_skills": ["Communication", "Teamwork"],
      "industry_knowledge": ["Financial services", "Regulatory compliance"],
      "company_values": ["Innovation", "Customer focus"],
      "keywords": [
        {{"keyword": "Python", "importance": 9, "category": "Technical Skill"}},
        {{"keyword": "Bachelor's degree", "importance": 8, "category": "Education"}}
      ]
    }}
    ```

    Return ONLY the JSON object wrapped in a markdown code block (```json ... ```) with no additional text before or after.
    """

def get_keyword_analysis_prompt(jd_analysis, jd_keywords, resume_text):
    """키워드 분석을 위한 프롬프트를 반환합니다."""
    jd_analysis_str = "\n".join([
        "REQUIRED QUALIFICATIONS:\n- " + "\n- ".join(jd_analysis.get('required_qualifications', [])),
        "PREFERRED QUALIFICATIONS:\n- " + "\n- ".join(jd_analysis.get('preferred_qualifications', [])),
        "TECHNICAL SKILLS:\n- " + "\n- ".join(jd_analysis.get('technical_skills', [])),
        "SOFT SKILLS:\n- " + "\n- ".join(jd_analysis.get('soft_skills', [])),
        "INDUSTRY KNOWLEDGE:\n- " + "\n- ".join(jd_analysis.get('industry_knowledge', []))
    ])
    top_keywords = sorted(jd_keywords, key=lambda x: x.get('importance', 0), reverse=True)[:20]
    keywords_str = "\n".join([f"- {kw.get('keyword')} (Importance: {kw.get('importance')}/10, Category: {kw.get('category')})"
                               for kw in top_keywords])

    return f"""
    Analyze how well this resume matches the key requirements and keywords from the job description.

    JOB DESCRIPTION ANALYSIS:
    {jd_analysis_str}

    TOP KEYWORDS FROM JOB DESCRIPTION:
    {keywords_str}

    RESUME:
    {resume_text}

    Please provide a detailed analysis with the following:

    1. TECHNICAL SKILLS MATCH: Evaluate how well the resume matches the required technical skills.
    2. QUALIFICATIONS MATCH: Evaluate how well the resume matches required and preferred qualifications.
    3. SOFT SKILLS MATCH: Evaluate how well the resume demonstrates the required soft skills.
    4. EXPERIENCE MATCH: Evaluate how well the resume satisfies experience requirements.
    5. KEYWORD ANALYSIS: Create a table showing matched and missing keywords, with their importance.

    For each category, provide specific examples from both the job description and resume.
    Calculate a match percentage for each category, and provide an overall keyword match score.

    End your analysis with "Score: XX points" where XX is a score from 0-100 representing how well the resume matches the job description's keywords and requirements.
    The response should be in well-formatted Markdown.
    """

def get_experience_analysis_prompt(jd_text, resume_text):
    """경력 및 자격 분석을 위한 프롬프트를 반환합니다."""
    return f"""
    Evaluate how well the candidate's experience and qualifications match the job requirements:

    JOB DESCRIPTION:
    {jd_text}

    RESUME:
    {resume_text}

    Please provide a detailed analysis of:
    1. Required years of experience vs. candidate's experience.
    2. Required education level vs. candidate's education.
    3. Required industry experience vs. candidate's industry background.
    4. Required responsibilities vs. candidate's demonstrated capabilities.
    5. Required achievements vs. candidate's accomplishments.

    For each area, indicate whether the candidate exceeds, meets, or falls short of requirements.
    Provide specific examples from both the job description and resume.

    End your analysis with "Score: XX points" where XX is a score from 0-100 representing how well the candidate's experience and qualifications match the job requirements.
    The response should be in well-formatted Markdown.
    """

def get_format_analysis_prompt(resume_text):
    """이력서 형식 분석을 위한 프롬프트를 반환합니다."""
    return f"""
    Evaluate the format, structure, and readability of the following resume:

    RESUME:
    {resume_text}

    Please analyze:
    1. Overall organization and structure.
    2. Readability and clarity.
    3. Use of bullet points, sections, and white space.
    4. Consistency in formatting (dates, job titles, etc.).
    5. Grammar, spelling, and punctuation.
    6. ATS-friendliness of the format.

    Provide specific examples of strengths and weaknesses in the format.
    Suggest specific improvements to make the resume more ATS-friendly and readable.

    End your analysis with "Score: XX points" where XX is a score from 0-100 representing the quality of the resume's format and readability.
    The response should be in well-formatted Markdown.
    """

def get_content_quality_prompt(resume_text):
    """콘텐츠 품질 분석을 위한 프롬프트를 반환합니다."""
    return f"""
    Evaluate the quality of content in the following resume:

    RESUME:
    {resume_text}

    Please analyze:
    1. Use of strong action verbs and achievement-oriented language.
    2. Quantification of achievements (metrics, percentages, numbers).
    3. Specificity vs. vagueness in descriptions.
    4. Relevance of included information.
    5. Balance between technical details and high-level accomplishments.
    6. Presence of clichés or generic statements vs. unique value propositions.

    Provide specific examples from the resume for each point.
    Suggest specific improvements to strengthen the content quality.

    End your analysis with "Score: XX points" where XX is a score from 0-100 representing the quality of the resume's content.
    The response should be in well-formatted Markdown.
    """

def get_error_check_prompt(resume_text):
    """오류 및 일관성 검사를 위한 프롬프트를 반환합니다."""
    return f"""
    Analyze the following resume for errors, inconsistencies, and potential red flags:

    RESUME:
    {resume_text}

    Please identify and explain:
    1. Spelling and grammar errors.
    2. Inconsistencies in dates, job titles, or other information.
    3. Unexplained employment gaps.
    4. Formatting inconsistencies.
    5. Potential red flags that might concern employers.

    For each issue found, provide the specific text from the resume and suggest a correction.
    If no issues are found in a category, explicitly state that.

    End your analysis with "Score: XX points" where XX is a score from 0-100 representing how error-free and consistent the resume is (100 = perfect, no issues).
    The response should be in well-formatted Markdown.
    """

def get_industry_identification_prompt(jd_text):
    """산업 및 직무 식별을 위한 프롬프트를 반환합니다."""
    return f"""
    Based on the following job description, identify the specific industry and job role.

    JOB DESCRIPTION:
    {jd_text}

    Format your response as a JSON object with this structure:
    ```json
    {{"industry": "Technology", "job_role": "Software Engineer"}}
    ```

    Be specific about both the industry and job role. Return ONLY the JSON object.
    """

def get_industry_specific_analysis_prompt(job_role, industry, jd_text, resume_text):
    """산업별 분석을 위한 프롬프트를 반환합니다."""
    return f"""
    Analyze this resume for a {job_role} position in the {industry} industry.

    JOB DESCRIPTION:
    {jd_text}

    RESUME:
    {resume_text}

    Please provide an industry-specific analysis considering:
    1. Industry-specific terminology and keywords in the resume.
    2. Relevant industry experience and understanding.
    3. Industry-specific certifications and education.
    4. Industry trends awareness.
    5. Industry-specific achievements and metrics.

    For each point, evaluate how well the resume demonstrates industry alignment.
    Provide specific recommendations for improving industry relevance.

    End your analysis with "Score: XX points" where XX is a score from 0-100 representing how well the resume aligns with this specific industry and role.
    The response should be in well-formatted Markdown.
    """

def get_improvement_suggestion_prompt(jd_text, resume_text, scores):
    """이력서 개선 제안을 위한 프롬프트를 반환합니다."""
    return f"""
    Based on the comprehensive analysis of this resume against the job description, provide specific, actionable improvements.

    JOB DESCRIPTION:
    {jd_text}

    RESUME:
    {resume_text}

    ANALYSIS SCORES:
    Keywords Analysis: {scores.get('keywords', 'N/A')}/100
    Experience Match: {scores.get('experience', 'N/A')}/100
    Format & Readability: {scores.get('format', 'N/A')}/100
    Content Quality: {scores.get('content', 'N/A')}/100
    Errors & Consistency: {scores.get('errors', 'N/A')}/100
    ATS Simulation: {scores.get('ats_simulation', 'N/A')}/100
    Industry Alignment: {scores.get('industry_specific', 'N/A')}/100

    Please provide specific, actionable improvements in these categories, in well-formatted Markdown:

    1. CRITICAL ADDITIONS: Keywords and qualifications that must be added.
    2. CONTENT ENHANCEMENTS: How to strengthen existing content.
    3. FORMAT IMPROVEMENTS: Structural changes to improve ATS compatibility.
    4. REMOVAL SUGGESTIONS: Content that should be removed or de-emphasized.
    5. SECTION-BY-SECTION RECOMMENDATIONS: Specific improvements for each resume section.

    For each suggestion, provide a clear before/after example where possible.
    Focus on the most impactful changes that will significantly improve ATS performance and human readability.
    """

def get_competitive_analysis_prompt(jd_text, resume_text):
    """경쟁력 분석을 위한 프롬프트를 반환합니다."""
    return f"""
    Analyze how competitive this resume would be in the current job market for this position.

    JOB DESCRIPTION:
    {jd_text}

    RESUME:
    {resume_text}

    Please provide a competitive analysis including:

    1. MARKET COMPARISON: How this resume compares to typical candidates for this role.
    2. STANDOUT STRENGTHS: The most impressive qualifications compared to the average candidate.
    3. COMPETITIVE WEAKNESSES: Areas where the candidate may fall behind competitors.
    4. DIFFERENTIATION FACTORS: Unique elements that set this resume apart (positively or negatively).
    5. HIRING PROBABILITY: Assessment of the likelihood of getting an interview (Low/Medium/High).

    Base your analysis on current job market trends and typical qualifications for this role and industry.
    Be honest but constructive in your assessment.

    End with a "Competitive Score: XX/100" representing how well this resume would compete against other candidates.
    The response should be in well-formatted Markdown.
    """

def get_resume_optimization_prompt(jd_text, resume_text):
    """이력서 최적화를 위한 프롬프트를 반환합니다."""
    return f"""
    Create an optimized version of this resume specifically tailored for the job description.

    JOB DESCRIPTION:
    {jd_text}

    CURRENT RESUME:
    {resume_text}

    Please rewrite the resume to:
    1. Incorporate all relevant keywords from the job description.
    2. Highlight the most relevant experience and qualifications.
    3. Use ATS-friendly formatting and structure.
    4. Quantify achievements where possible.
    5. Remove or downplay irrelevant information.

    The optimized resume should maintain truthfulness while presenting the candidate in the best possible light for this specific position.
    Use standard resume formatting with clear section headers. The entire output should be the resume text, nothing else.
    """

def get_final_report_prompt(jd_analysis, scores, final_score):
    """최종 보고서 생성을 위한 프롬프트를 반환합니다."""
    jd_summary = ""
    if jd_analysis:
        jd_summary = "JOB DESCRIPTION ANALYSIS:\n"
        if jd_analysis.get('required_qualifications'):
            jd_summary += "Required Qualifications: " + ", ".join(jd_analysis.get('required_qualifications')[:5]) + "\n"
        if jd_analysis.get('technical_skills'):
            jd_summary += "Technical Skills: " + ", ".join(jd_analysis.get('technical_skills')[:5]) + "\n"
        if jd_analysis.get('key_responsibilities'):
            jd_summary += "Key Responsibilities: " + ", ".join(jd_analysis.get('key_responsibilities')[:3]) + "\n"

    return f"""
    Based on the comprehensive analysis of this resume against the job description, provide a final assessment and recommendations.

    {jd_summary}

    RESUME ANALYSIS SCORES:
    ATS Simulation Score: {scores.get('ats_simulation', 'N/A')}/100 (30% of final score)
    Keywords Match: {scores.get('keywords', 'N/A')}/100 (25% of final score)
    Experience Match: {scores.get('experience', 'N/A')}/100 (20% of final score)
    Industry Alignment: {scores.get('industry_specific', 'N/A')}/100 (15% of final score)
    Content Quality: {scores.get('content', 'N/A')}/100 (5% of final score)
    Format & Readability: {scores.get('format', 'N/A')}/100 (3% of final score)
    Errors & Consistency: {scores.get('errors', 'N/A')}/100 (2% of final score)

    FINAL WEIGHTED SCORE: {final_score:.1f}/100

    Please provide a detailed final assessment in well-formatted Markdown with:

    1. EXECUTIVE SUMMARY: A concise summary of how well this resume matches this specific job description.
    2. STRENGTHS: The top 3 strengths of this resume for this specific job.
    3. CRITICAL IMPROVEMENTS: The top 3 most critical improvements needed to better match this job description.
    4. ATS ASSESSMENT: An assessment of the resume's likelihood of passing ATS filters for this specific job.
    5. INTERVIEW POTENTIAL: An assessment of whether this resume would likely lead to an interview.
    6. FINAL RECOMMENDATION: A clear verdict on whether the candidate should:
       a) Apply with this resume as is
       b) Make minor improvements before applying
       c) Make major improvements before applying

    Be specific about which improvements would have the biggest impact on ATS performance for this particular job.
    """

def get_html_report_template(final_score, chart_image, final_report_md, ats_simulation_md, improvements_md, scores, analysis_results, md_to_html_func):
    """HTML 보고서 템플릿을 반환합니다."""
    
    def get_progress_bar_html(score_key):
        score_val = scores.get(score_key, 0)
        color_class = 'good' if score_val >= 80 else 'medium' if score_val >= 60 else 'poor'
        return f"""
        <div class="progress-container">
            <div class="progress-bar {color_class}" style="width: {score_val}%"></div>
        </div>
        """

    sections_html = ""
    section_map = {
        'keywords': ('Keywords Match', 'keywords'),
        'experience': ('Experience & Qualifications', 'experience'),
        'format': ('Format & Readability', 'format'),
        'content': ('Content Quality', 'content'),
        'errors': ('Errors & Consistency', 'errors'),
        'industry_specific': ('Industry Alignment', 'industry_specific')
    }

    for key, (title, score_key) in section_map.items():
        score_val = scores.get(score_key, 0)
        analysis_content = analysis_results.get(key, 'Not available')
        sections_html += f"""
        <h3 class="category">{title} ({score_val}/100)</h3>
        {get_progress_bar_html(score_key)}
        <div class="markdown-content">{md_to_html_func(analysis_content)}</div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ATS Analysis Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 20px; color: #333; background-color: #f9f9f9; }}
            .container {{ max-width: 1000px; margin: 0 auto; background-color: #fff; padding: 20px 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
            .header h1 {{ font-size: 2.5em; color: #2c3e50; }}
            .score-card {{ background-color: #f5f5f5; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
            .score-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #555; }}
            .score-value {{ font-size: 48px; font-weight: bold; color: #2c3e50; }}
            .chart {{ text-align: center; margin: 40px 0; }}
            .chart h2 {{ font-size: 1.8em; color: #2c3e50; margin-bottom: 20px;}}
            .analysis-section {{ margin-bottom: 30px; }}
            .analysis-section h2 {{ font-size: 1.8em; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; }}
            .improvement {{ background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 5px solid #3498db; }}
            .improvement h2 {{ font-size: 1.8em; color: #2c3e50; border-bottom: none; }}
            .category {{ font-weight: bold; color: #3498db; font-size: 1.4em; margin-top: 30px;}}
            .progress-container {{ width: 100%; background-color: #e0e0e0; border-radius: 5px; margin: 10px 0; overflow: hidden; }}
            .progress-bar {{ height: 20px; border-radius: 5px; text-align: right; color: white; font-weight: bold; padding-right: 5px; line-height: 20px; transition: width 0.5s ease-in-out; }}
            .good {{ background-color: #4CAF50; }}
            .medium {{ background-color: #FFC107; }}
            .poor {{ background-color: #F44336; }}
            pre {{ white-space: pre-wrap; background-color: #f4f4f4; padding: 15px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; }}
            .markdown-content {{ line-height: 1.6; }}
            .markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4 {{ margin-top: 1.5em; margin-bottom: 0.5em; color: #2c3e50; }}
            .markdown-content ul, .markdown-content ol {{ padding-left: 2em; }}
            .markdown-content table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
            .markdown-content th, .markdown-content td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            .markdown-content th {{ background-color: #f2f2f2; font-weight: bold; }}
            .markdown-content code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: 'Courier New', Courier, monospace; }}
            .markdown-content blockquote {{ border-left: 4px solid #ddd; padding-left: 1em; margin-left: 0; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Resume ATS Analysis Report</h1>
                <p>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="score-card">
                <div class="score-title">Final ATS Score</div>
                <div class="score-value">{final_score:.1f} / 100</div>
                {get_progress_bar_html('final')}
                <p>This score represents the overall effectiveness of your resume for this specific job.</p>
            </div>

            <div class="chart">
                <h2>Score Breakdown</h2>
                <img src="data:image/png;base64,{chart_image}" alt="ATS Analysis Chart">
            </div>

            <div class="analysis-section">
                <h2>Executive Summary & Final Recommendations</h2>
                <div class="markdown-content">{final_report_md}</div>
            </div>

            <div class="analysis-section">
                <h2>ATS Simulation Results</h2>
                <div class="markdown-content">{ats_simulation_md}</div>
            </div>

            <div class="improvement">
                <h2>Recommended Improvements</h2>
                <div class="markdown-content">{improvements_md}</div>
            </div>

            <div class="analysis-section">
                <h2>Detailed Analysis</h2>
                {sections_html}
            </div>

            <div class="analysis-section">
                <h2>Competitive Analysis</h2>
                <div class="markdown-content">{md_to_html_func(analysis_results.get('competitive', 'Not available'))}</div>
            </div>
        </div>
    </body>
    </html>
    """

def get_semantic_keyword_analysis_prompt(jd_keywords, resume_text):
    """
    LLM을 사용하여 이력서와 JD 키워드 간의 의미적 일치도를 분석하기 위한 프롬프트를 반환합니다.
    """
    keywords_str = "\n".join([f"- {kw.get('keyword')} (Importance: {kw.get('importance')}, Category: {kw.get('category')})" for kw in jd_keywords])

    return f"""
    You are an expert ATS analyst. Your task is to perform a deep, context-aware analysis of the provided resume against a list of keywords from a job description.
    Do not just perform a simple text search. Instead, understand the concepts and experiences described in the resume and see if they align with the semantic meaning of the keywords.

    RESUME TEXT:
    ---
    {resume_text}
    ---

    KEYWORDS TO ANALYZE:
    ---
    {keywords_str}
    ---

    For each keyword, classify it into one of three statuses:
    1.  **matched**: The keyword (or a very close synonym) is explicitly mentioned in the resume.
    2.  **semantically_present**: The keyword itself is not present, but the resume describes a project, skill, or experience that clearly demonstrates the concept or capability behind the keyword. For example, if the keyword is "Generative AI", mentioning "developed RAG systems and LLM solutions" counts as semantically present.
    3.  **missing**: The keyword or its underlying concept is not found in the resume.

    Provide a brief `justification` for your classification for each keyword.

    Format your response as a single, valid JSON object with NO additional text before or after. The JSON object should have two keys: "semantic_analysis_summary" and "keyword_matches".

    Example format:
    ```json
    {{
      "semantic_analysis_summary": "The resume shows strong alignment with core AI concepts but could be improved by explicitly using certain enterprise-level terms to pass initial screenings.",
      "keyword_matches": [
        {{
          "keyword": "Generative AI",
          "status": "semantically_present",
          "justification": "Resume details experience with RAG, LLM solutions, and agentic frameworks, which are core to Generative AI.",
          "importance": 10,
          "category": "Technical Skill"
        }},
        {{
          "keyword": "OpenAI API",
          "status": "matched",
          "justification": "The 'JobPT' project explicitly states usage of the OpenAI API.",
          "importance": 9,
          "category": "Technical Skill"
        }},
        {{
          "keyword": "Enterprise architecture",
          "status": "missing",
          "justification": "The resume focuses on model development and specific systems, but does not mention designing broader enterprise-level architectures.",
          "importance": 8,
          "category": "Technical Skill"
        }}
      ]
    }}
    ```
    """

# %% 