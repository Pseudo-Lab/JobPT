# %%
import os
import re
import json
import time
import numpy as np
import openai
import PyPDF2
import docx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from dotenv import load_dotenv
from configs import OPENAI_API_KEY, GROQ_API_KEY

class ATSAnalyzer:
    """
    Advanced ATS (Applicant Tracking System) Analyzer

    This class analyzes resumes against job descriptions to simulate
    how an ATS system would evaluate the resume, providing detailed feedback
    and improvement suggestions.
    """

    def __init__(self, cv_path, jd_text, model=1):
        """
        Initialize the ATS Analyzer

        Args:
            cv_path (str): Path to the resume file (PDF, DOCX, TXT) or raw text
            jd_text (str): Job description text
            model (int): Model selection (1=OpenAI, 2=Groq)
        """
        self.cv_path = cv_path
        self.jd_text = jd_text
        self.cv_text = ""
        self.preprocessed_cv = ""
        self.structured_cv = {}
        self.jd_analysis = {}  # Added: Store JD analysis results
        self.jd_requirements = []  # Added: Store extracted JD requirements
        self.jd_keywords = []  # Added: Store extracted JD keywords
        self.analysis_results = {}
        self.scores = {}
        self.final_report = ""
        self.improvement_suggestions = ""
        self.competitive_analysis = ""
        self.optimized_resume = ""
        self.llm_call_count = 0
        self.total_tokens = 0
        self.total_time = 0
        self.model = model

        # Load environment variables
        load_dotenv()

    def extract_and_preprocess(self):
        """Extract text from resume file and preprocess it"""
        ext = os.path.splitext(self.cv_path)[1].lower()
        text = ""
        try:
            if len(self.cv_path) > 270:  # Likely raw text rather than a file path
                text = self.cv_path
            elif ext == ".pdf":
                with open(self.cv_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            elif ext == ".docx":
                doc = docx.Document(self.cv_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif ext in [".txt", ".md"]:
                with open(self.cv_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                print(f"Unsupported file format: {ext}")
                text = ""
        except Exception as e:
            print(f"Error processing resume file: {e}")
            text = ""

        self.cv_text = text.strip()

        # Extract structured sections from the resume
        self.structured_cv = self.extract_resume_sections(self.cv_text)

        # Advanced preprocessing
        self.preprocessed_cv = self.advanced_preprocessing(self.cv_text)

        # Analyze the job description
        self.analyze_job_description()

        print(f"Extracted {len(self.cv_text)} characters from resume")
        print(f"Identified {len(self.structured_cv)} sections in the resume")
        print(f"Analyzed job description with {len(self.jd_keywords)} keywords extracted")

    def analyze_job_description(self):
        """
        Analyze the job description to extract requirements, keywords, and other important information
        This is a critical step to ensure the ATS analysis is specific to this particular job
        """
        # Extract key requirements and keywords from the JD
        jd_analysis_prompt = f"""
        Perform a detailed analysis of this job description to extract all information that would be used by an ATS system.

        JOB DESCRIPTION:
        {self.jd_text}

        Please provide a comprehensive analysis with the following components:

        1. REQUIRED QUALIFICATIONS: All explicitly stated required qualifications (education, experience, certifications, etc.)
        2. PREFERRED QUALIFICATIONS: All preferred or desired qualifications that are not strictly required
        3. KEY RESPONSIBILITIES: The main job duties and responsibilities
        4. TECHNICAL SKILLS: All technical skills, tools, languages, frameworks, etc. mentioned
        5. SOFT SKILLS: All soft skills, personal qualities, and character traits mentioned
        6. INDUSTRY KNOWLEDGE: Required industry-specific knowledge or experience
        7. COMPANY VALUES: Any company values or culture fit indicators mentioned

        Format your response as a valid JSON object with these categories as keys, and arrays of strings as values.
        Also include a "keywords" array with all important keywords from the job description, each with an importance score from 1-10.

        The JSON must be properly formatted with no errors. Make sure all quotes are properly escaped and all arrays and objects are properly closed.

        Example format:
        {{"required_qualifications": ["Bachelor's degree in Computer Science", "5+ years of experience"],
          "preferred_qualifications": ["Master's degree", "Experience with cloud platforms"],
          "key_responsibilities": ["Develop software applications", "Debug and troubleshoot issues"],
          "technical_skills": ["Python", "JavaScript", "AWS"],
          "soft_skills": ["Communication", "Teamwork"],
          "industry_knowledge": ["Financial services", "Regulatory compliance"],
          "company_values": ["Innovation", "Customer focus"],
          "keywords": [{{"keyword": "Python", "importance": 9, "category": "Technical Skill"}}, {{"keyword": "Bachelor's degree", "importance": 8, "category": "Education"}}]
        }}

        Return ONLY the JSON object with no additional text before or after.
        """

        response = self.call_llm(jd_analysis_prompt, model=self.model)

        # Parse the JSON response
        try:
            # Try to clean up the response to make it valid JSON
            # Remove any text before the first '{' and after the last '}'
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx >= 0 and end_idx >= 0:
                response = response[start_idx:end_idx+1]

            # Try to parse the JSON
            try:
                self.jd_analysis = json.loads(response)
            except json.JSONDecodeError as e:
                # If parsing fails, try to fix common JSON errors
                print(f"Initial JSON parsing failed: {e}")
                print("Attempting to fix JSON format...")

                # Fix common JSON errors
                # 1. Replace single quotes with double quotes
                response = response.replace("'", '"')

                # 2. Fix trailing commas in arrays and objects
                response = re.sub(r',\s*}', '}', response)
                response = re.sub(r',\s*]', ']', response)

                # Try parsing again
                self.jd_analysis = json.loads(response)

            # Extract keywords for later use
            self.jd_keywords = self.jd_analysis.get('keywords', [])

            # Compile a list of all requirements
            self.jd_requirements = (
                self.jd_analysis.get('required_qualifications', []) +
                self.jd_analysis.get('preferred_qualifications', []) +
                self.jd_analysis.get('technical_skills', []) +
                self.jd_analysis.get('soft_skills', []) +
                self.jd_analysis.get('industry_knowledge', [])
            )

            print(f"Successfully parsed JD analysis with {len(self.jd_keywords)} keywords")

        except Exception as e:
            print(f"Error parsing JD analysis JSON: {e}")
            print(f"Raw response: {response[:500]}...")

            # If all parsing attempts fail, create a default structure with dummy data
            print("Creating default JD analysis structure with dummy data")
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
                    {"keyword": "Machine Learning", "importance": 8, "category": "Technical Skill"},
                    {"keyword": "Research", "importance": 7, "category": "Experience"},
                    {"keyword": "Master's degree", "importance": 8, "category": "Education"}
                ]
            }
            self.jd_keywords = self.jd_analysis["keywords"]
            self.jd_requirements = (
                self.jd_analysis["required_qualifications"] +
                self.jd_analysis["preferred_qualifications"] +
                self.jd_analysis["technical_skills"] +
                self.jd_analysis["soft_skills"] +
                self.jd_analysis["industry_knowledge"]
            )

    def extract_resume_sections(self, text):
        """
        Extract and structure resume sections

        Args:
            text (str): Raw resume text

        Returns:
            dict: Resume sections as a structured dictionary
        """
        # Common resume section header patterns
        section_patterns = {
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

        sections = {}
        current_section = 'header'  # Text before first section is considered header
        sections[current_section] = []

        lines = text.split('\n')
        for line in lines:
            matched = False
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section_name
                    sections[current_section] = []
                    matched = True
                    break

            if not matched:
                sections[current_section].append(line)

        # Combine lines in each section into text
        for section in sections:
            sections[section] = '\n'.join(sections[section]).strip()

        return sections

    def advanced_preprocessing(self, text):
        """
        Advanced text preprocessing for resume analysis

        Args:
            text (str): Raw resume text

        Returns:
            str: Preprocessed text
        """
        # Preserve important formatting like emails, URLs, phone numbers
        # Replace excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Clean up unnecessary line breaks while preserving paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def analyze_keywords(self):
        """
        Analyze how well the resume matches key terms in the job description
        Uses the pre-analyzed JD to ensure accuracy
        """
        # Prepare JD analysis for the prompt
        jd_analysis_str = "\n".join([
            "REQUIRED QUALIFICATIONS:\n- " + "\n- ".join(self.jd_analysis.get('required_qualifications', [])),
            "PREFERRED QUALIFICATIONS:\n- " + "\n- ".join(self.jd_analysis.get('preferred_qualifications', [])),
            "TECHNICAL SKILLS:\n- " + "\n- ".join(self.jd_analysis.get('technical_skills', [])),
            "SOFT SKILLS:\n- " + "\n- ".join(self.jd_analysis.get('soft_skills', [])),
            "INDUSTRY KNOWLEDGE:\n- " + "\n- ".join(self.jd_analysis.get('industry_knowledge', []))
        ])

        # Extract top keywords by importance
        top_keywords = sorted(self.jd_keywords, key=lambda x: x.get('importance', 0), reverse=True)[:20]
        keywords_str = "\n".join([f"- {kw.get('keyword')} (Importance: {kw.get('importance')}/10, Category: {kw.get('category')})"
                               for kw in top_keywords])

        prompt = f"""
        Analyze how well this resume matches the key requirements and keywords from the job description.

        JOB DESCRIPTION ANALYSIS:
        {jd_analysis_str}

        TOP KEYWORDS FROM JOB DESCRIPTION:
        {keywords_str}

        RESUME:
        {self.preprocessed_cv}

        Please provide a detailed analysis with the following:

        1. TECHNICAL SKILLS MATCH: Evaluate how well the resume matches the required technical skills
        2. QUALIFICATIONS MATCH: Evaluate how well the resume matches required and preferred qualifications
        3. SOFT SKILLS MATCH: Evaluate how well the resume demonstrates the required soft skills
        4. EXPERIENCE MATCH: Evaluate how well the resume satisfies experience requirements
        5. KEYWORD ANALYSIS: Create a table showing matched and missing keywords, with their importance

        For each category, provide specific examples from both the job description and resume.
        Calculate a match percentage for each category, and provide an overall keyword match score.

        End your analysis with "Score: XX points" where XX is a score from 0-100 representing how well the resume matches the job description's keywords and requirements.
        """

        response = self.call_llm(prompt, model=self.model)
        print("[DEBUG] Keywords analysis LLM response:\n", response[:300], "...")

        score = self.extract_score(response)
        print("[DEBUG] Keywords score:", score)

        self.analysis_results['keywords'] = response
        self.scores['keywords'] = score

    def analyze_experience_and_qualifications(self):
        """
        Analyze how well the resume's experience and qualifications match the job requirements
        """
        prompt = f"""
        Evaluate how well the candidate's experience and qualifications match the job requirements:

        JOB DESCRIPTION:
        {self.jd_text}

        RESUME:
        {self.preprocessed_cv}

        Please provide a detailed analysis of:
        1. Required years of experience vs. candidate's experience
        2. Required education level vs. candidate's education
        3. Required industry experience vs. candidate's industry background
        4. Required responsibilities vs. candidate's demonstrated capabilities
        5. Required achievements vs. candidate's accomplishments


        For each area, indicate whether the candidate exceeds, meets, or falls short of requirements.
        Provide specific examples from both the job description and resume.


        End your analysis with "Score: XX points" where XX is a score from 0-100 representing how well the candidate's experience and qualifications match the job requirements.
        """

        response = self.call_llm(prompt, model=self.model)
        print("[DEBUG] Experience analysis LLM response:\n", response[:300], "...")

        score = self.extract_score(response)
        print("[DEBUG] Experience score:", score)

        self.analysis_results['experience'] = response
        self.scores['experience'] = score

    def analyze_format_and_readability(self):
        """
        Analyze the resume's format, structure, and readability
        """
        prompt = f"""
        Evaluate the format, structure, and readability of the following resume:

        RESUME:
        {self.preprocessed_cv}

        Please analyze:
        1. Overall organization and structure
        2. Readability and clarity
        3. Use of bullet points, sections, and white space
        4. Consistency in formatting (dates, job titles, etc.)
        5. Grammar, spelling, and punctuation
        6. ATS-friendliness of the format


        Provide specific examples of strengths and weaknesses in the format.
        Suggest specific improvements to make the resume more ATS-friendly and readable.


        End your analysis with "Score: XX points" where XX is a score from 0-100 representing the quality of the resume's format and readability.
        """

        response = self.call_llm(prompt, model=self.model)
        print("[DEBUG] Format analysis LLM response:\n", response[:300], "...")

        score = self.extract_score(response)
        print("[DEBUG] Format score:", score)

        self.analysis_results['format'] = response
        self.scores['format'] = score

    def analyze_content_quality(self):
        """
        Analyze the quality of content in the resume
        """
        prompt = f"""
        Evaluate the quality of content in the following resume:

        RESUME:
        {self.preprocessed_cv}

        Please analyze:
        1. Use of strong action verbs and achievement-oriented language
        2. Quantification of achievements (metrics, percentages, numbers)
        3. Specificity vs. vagueness in descriptions
        4. Relevance of included information
        5. Balance between technical details and high-level accomplishments
        6. Presence of clichés or generic statements vs. unique value propositions


        Provide specific examples from the resume for each point.
        Suggest specific improvements to strengthen the content quality.


        End your analysis with "Score: XX points" where XX is a score from 0-100 representing the quality of the resume's content.
        """

        response = self.call_llm(prompt, model=self.model)
        print("[DEBUG] Content analysis LLM response:\n", response[:300], "...")

        score = self.extract_score(response)
        print("[DEBUG] Content score:", score)

        self.analysis_results['content'] = response
        self.scores['content'] = score

    def check_errors_and_consistency(self):
        """
        Check for errors, inconsistencies, and red flags in the resume
        """
        prompt = f"""
        Analyze the following resume for errors, inconsistencies, and potential red flags:

        RESUME:
        {self.preprocessed_cv}

        Please identify and explain:
        1. Spelling and grammar errors
        2. Inconsistencies in dates, job titles, or other information
        3. Unexplained employment gaps
        4. Formatting inconsistencies
        5. Potential red flags that might concern employers


        For each issue found, provide the specific text from the resume and suggest a correction.
        If no issues are found in a category, explicitly state that.


        End your analysis with "Score: XX points" where XX is a score from 0-100 representing how error-free and consistent the resume is (100 = perfect, no issues).
        """

        response = self.call_llm(prompt, model=self.model)
        print("[DEBUG] Errors analysis LLM response:\n", response[:300], "...")

        score = self.extract_score(response)
        print("[DEBUG] Errors score:", score)

        self.analysis_results['errors'] = response
        self.scores['errors'] = score

    def simulate_ats_filtering(self):
        """
        Simulate how an actual ATS system would evaluate this resume
        Uses the pre-analyzed JD keywords for more accurate simulation
        """
        # Use the keywords already extracted from JD analysis
        if not self.jd_keywords:
            print("No keywords available from JD analysis, running JD analysis first")
            self.analyze_job_description()

        # Use the keywords from JD analysis
        keywords = self.jd_keywords

        if not keywords:
            print("Warning: No keywords found in JD analysis")
            self.analysis_results['ats_simulation'] = "Error in ATS simulation: No keywords found in job description"
            self.scores['ats_simulation'] = 50  # Default middle score
            return

        # Calculate keyword matching score with more sophisticated matching
        total_importance = sum(kw.get('importance', 5) for kw in keywords)
        matched_importance = 0
        matched_keywords = []
        missing_keywords = []
        partial_matches = []

        for kw in keywords:
            keyword = kw.get('keyword', '')
            importance = kw.get('importance', 5)
            category = kw.get('category', 'Uncategorized')

            # Check for exact matches (case insensitive)
            if re.search(r'\b' + re.escape(keyword) + r'\b', self.preprocessed_cv, re.IGNORECASE):
                matched_importance += importance
                matched_keywords.append({"keyword": keyword, "importance": importance, "category": category, "match_type": "exact"})

            # Check for partial matches (for multi-word keywords)
            elif len(keyword.split()) > 1:
                # For multi-word keywords, check if at least 70% of the words are present
                words = keyword.lower().split()
                matches = 0
                for word in words:
                    if re.search(r'\b' + re.escape(word) + r'\b', self.preprocessed_cv.lower()):
                        matches += 1

                match_percentage = matches / len(words)
                if match_percentage >= 0.7:  # At least 70% of words match
                    partial_value = importance * match_percentage
                    matched_importance += partial_value
                    partial_matches.append({"keyword": keyword, "importance": importance,
                                          "category": category, "match_type": "partial",
                                          "match_percentage": f"{match_percentage:.0%}"})
                else:
                    missing_keywords.append({"keyword": keyword, "importance": importance, "category": category})
            else:
                missing_keywords.append({"keyword": keyword, "importance": importance, "category": category})

        # Calculate ATS score (0-100)
        if total_importance > 0:
            ats_score = (matched_importance / total_importance) * 100
        else:
            ats_score = 0

        # Group keywords by category for better reporting
        matched_by_category = {}
        partial_by_category = {}
        missing_by_category = {}

        for kw in matched_keywords:
            category = kw['category']
            if category not in matched_by_category:
                matched_by_category[category] = []
            matched_by_category[category].append(kw)

        for kw in partial_matches:
            category = kw['category']
            if category not in partial_by_category:
                partial_by_category[category] = []
            partial_by_category[category].append(kw)

        for kw in missing_keywords:
            category = kw['category']
            if category not in missing_by_category:
                missing_by_category[category] = []
            missing_by_category[category].append(kw)

        # Generate detailed report
        report = f"""## ATS Simulation Results

### Overall ATS Score: {ats_score:.1f}/100

"""

        # Add matched keywords section
        report += "### Exact Keyword Matches\n\n"
        for category, keywords in matched_by_category.items():
            report += f"**{category}**:\n"
            for kw in sorted(keywords, key=lambda x: x['importance'], reverse=True):
                report += f"- {kw['keyword']} (Importance: {kw['importance']}/10)\n"
            report += "\n"

        # Add partial matches section
        if partial_matches:
            report += "### Partial Keyword Matches\n\n"
            for category, keywords in partial_by_category.items():
                report += f"**{category}**:\n"
                for kw in sorted(keywords, key=lambda x: x['importance'], reverse=True):
                    report += f"- {kw['keyword']} (Importance: {kw['importance']}/10, Match: {kw['match_percentage']})\n"
                report += "\n"

        # Add missing keywords section
        report += "### Missing Keywords\n\n"
        for category, keywords in missing_by_category.items():
            report += f"**{category}**:\n"
            for kw in sorted(keywords, key=lambda x: x['importance'], reverse=True):
                report += f"- {kw['keyword']} (Importance: {kw['importance']}/10)\n"
            report += "\n"

        # Add ATS passage likelihood with more detailed assessment
        if ats_score >= 85:
            passage = "Very high likelihood of passing ATS filters - Resume is extremely well-matched to this job"
        elif ats_score >= 70:
            passage = "High likelihood of passing ATS filters - Resume is well-matched to this job"
        elif ats_score >= 55:
            passage = "Moderate likelihood of passing ATS filters - Resume has adequate matching but could be improved"
        elif ats_score >= 40:
            passage = "Low likelihood of passing ATS filters - Resume needs significant improvements for this job"
        else:
            passage = "Very low likelihood of passing ATS filters - Resume is not well-matched to this job"

        report += f"### ATS Passage Assessment\n\n{passage}\n\n"

        # Add specific recommendations based on missing keywords
        report += "### Key Recommendations\n\n"

        # Get top 5 missing keywords by importance
        top_missing = sorted(missing_keywords, key=lambda x: x.get('importance', 0), reverse=True)[:5]
        if top_missing:
            report += "Consider adding these high-importance missing keywords to your resume:\n"
            for kw in top_missing:
                report += f"- {kw['keyword']} (Importance: {kw['importance']}/10, Category: {kw['category']})\n"

        report += f"\nScore: {int(ats_score)} points"

        self.analysis_results['ats_simulation'] = report
        self.scores['ats_simulation'] = min(100, ats_score)

    def analyze_industry_specific(self):
        """
        Perform industry and job role specific analysis
        """
        # First, identify the industry and job role
        industry_prompt = f"""
        Based on the following job description, identify the specific industry and job role.

        JOB DESCRIPTION:
        {self.jd_text}

        Format your response as a JSON object with this structure:
        {{"industry": "Technology", "job_role": "Software Engineer"}}


        Be specific about both the industry and job role.
        """

        response = self.call_llm(industry_prompt, model=self.model)

        # Parse the JSON response
        try:
            # Find JSON in the response
            json_match = re.search(r'\{\s*"industry"\s*:.+?\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

            job_info = json.loads(response)
            industry = job_info.get('industry', 'General')
            job_role = job_info.get('job_role', 'General')
        except Exception as e:
            print(f"Error parsing industry JSON: {e}")
            industry = "Technology"  # Default fallback
            job_role = "Professional"  # Default fallback

        # Now perform industry-specific analysis
        industry_analysis_prompt = f"""
        Analyze this resume for a {job_role} position in the {industry} industry.

        JOB DESCRIPTION:
        {self.jd_text}

        RESUME:
        {self.preprocessed_cv}

        Please provide an industry-specific analysis considering:
        1. Industry-specific terminology and keywords in the resume
        2. Relevant industry experience and understanding
        3. Industry-specific certifications and education
        4. Industry trends awareness
        5. Industry-specific achievements and metrics


        For each point, evaluate how well the resume demonstrates industry alignment.
        Provide specific recommendations for improving industry relevance.


        End your analysis with "Score: XX points" where XX is a score from 0-100 representing how well the resume aligns with this specific industry and role.
        """

        response = self.call_llm(industry_analysis_prompt, model=self.model)
        score = self.extract_score(response)

        self.analysis_results['industry_specific'] = response
        self.scores['industry_specific'] = score

    def suggest_resume_improvements(self):
        """
        Generate specific suggestions to improve the resume for this job
        """
        prompt = f"""
        Based on the comprehensive analysis of this resume against the job description, provide specific, actionable improvements.

        JOB DESCRIPTION:
        {self.jd_text}

        RESUME:
        {self.preprocessed_cv}

        ANALYSIS RESULTS:
        Keywords Analysis: {self.scores.get('keywords', 'N/A')}/100
        Experience Match: {self.scores.get('experience', 'N/A')}/100
        Format & Readability: {self.scores.get('format', 'N/A')}/100
        Content Quality: {self.scores.get('content', 'N/A')}/100
        Errors & Consistency: {self.scores.get('errors', 'N/A')}/100
        ATS Simulation: {self.scores.get('ats_simulation', 'N/A')}/100
        Industry Alignment: {self.scores.get('industry_specific', 'N/A')}/100


        Please provide specific, actionable improvements in these categories:


        1. CRITICAL ADDITIONS: Keywords and qualifications that must be added
        2. CONTENT ENHANCEMENTS: How to strengthen existing content
        3. FORMAT IMPROVEMENTS: Structural changes to improve ATS compatibility
        4. REMOVAL SUGGESTIONS: Content that should be removed or de-emphasized
        5. SECTION-BY-SECTION RECOMMENDATIONS: Specific improvements for each resume section


        For each suggestion, provide a clear before/after example where possible.
        Focus on the most impactful changes that will significantly improve ATS performance and human readability.
        """

        response = self.call_llm(prompt, model=self.model)
        self.improvement_suggestions = response
        return response

    def analyze_competitive_position(self):
        """
        Analyze the competitive position of this resume in the current job market
        """
        prompt = f"""
        Analyze how competitive this resume would be in the current job market for this position.

        JOB DESCRIPTION:
        {self.jd_text}

        RESUME:
        {self.preprocessed_cv}

        Please provide a competitive analysis including:


        1. MARKET COMPARISON: How this resume compares to typical candidates for this role
        2. STANDOUT STRENGTHS: The most impressive qualifications compared to the average candidate
        3. COMPETITIVE WEAKNESSES: Areas where the candidate may fall behind competitors
        4. DIFFERENTIATION FACTORS: Unique elements that set this resume apart (positively or negatively)
        5. HIRING PROBABILITY: Assessment of the likelihood of getting an interview (Low/Medium/High)


        Base your analysis on current job market trends and typical qualifications for this role and industry.
        Be honest but constructive in your assessment.


        End with a competitive score from 0-100 representing how well this resume would compete against other candidates.
        """

        response = self.call_llm(prompt, model=self.model)
        score = self.extract_score(response)

        self.analysis_results['competitive'] = response
        self.scores['competitive'] = score
        return response

    def generate_optimized_resume(self):
        """
        Generate an optimized version of the resume tailored to the job description
        """
        prompt = f"""
        Create an optimized version of this resume specifically tailored for the job description.

        JOB DESCRIPTION:
        {self.jd_text}

        CURRENT RESUME:
        {self.preprocessed_cv}

        Please rewrite the resume to:
        1. Incorporate all relevant keywords from the job description
        2. Highlight the most relevant experience and qualifications
        3. Use ATS-friendly formatting and structure
        4. Quantify achievements where possible
        5. Remove or downplay irrelevant information


        The optimized resume should maintain truthfulness while presenting the candidate in the best possible light for this specific position.
        Use standard resume formatting with clear section headers.
        """

        response = self.call_llm(prompt, model=self.model)
        self.optimized_resume = response
        return response

    def generate_final_score_and_recommendations(self):
        """
        Generate final score with weighted categories and overall recommendations
        Adjusted to give more weight to JD-specific factors
        """
        # Define weights for different categories with higher emphasis on JD-specific factors
        weights = {
            'ats_simulation': 0.30,    # Direct ATS simulation is most important
            'keywords': 0.25,         # Keywords are critical for ATS
            'experience': 0.20,       # Experience match is very important
            'industry_specific': 0.15, # Industry relevance
            'content': 0.05,          # Content quality
            'format': 0.03,           # Format and readability
            'errors': 0.02,           # Errors and consistency
        }

        # Calculate weighted score
        weighted_sum = 0
        used_weights_sum = 0
        category_scores = {}

        for category, weight in weights.items():
            if category in self.scores:
                score = self.scores[category]
                weighted_sum += score * weight
                used_weights_sum += weight
                category_scores[category] = score

        # Calculate final score
        if used_weights_sum > 0:
            final_score = weighted_sum / used_weights_sum
        else:
            final_score = 0

        self.scores['final'] = final_score

        # Prepare JD analysis summary for the prompt
        jd_summary = ""
        if self.jd_analysis:
            jd_summary = "JOB DESCRIPTION ANALYSIS:\n"
            if self.jd_analysis.get('required_qualifications'):
                jd_summary += "Required Qualifications: " + ", ".join(self.jd_analysis.get('required_qualifications')[:5]) + "\n"
            if self.jd_analysis.get('technical_skills'):
                jd_summary += "Technical Skills: " + ", ".join(self.jd_analysis.get('technical_skills')[:5]) + "\n"
            if self.jd_analysis.get('key_responsibilities'):
                jd_summary += "Key Responsibilities: " + ", ".join(self.jd_analysis.get('key_responsibilities')[:3]) + "\n"

        # Generate final recommendations
        prompt = f"""
        Based on the comprehensive analysis of this resume against the job description, provide a final assessment and recommendations.

        {jd_summary}

        RESUME ANALYSIS SCORES:
        ATS Simulation Score: {category_scores.get('ats_simulation', 'N/A')}/100 (30% of final score)
        Keywords Match: {category_scores.get('keywords', 'N/A')}/100 (25% of final score)
        Experience Match: {category_scores.get('experience', 'N/A')}/100 (20% of final score)
        Industry Alignment: {category_scores.get('industry_specific', 'N/A')}/100 (15% of final score)
        Content Quality: {category_scores.get('content', 'N/A')}/100 (5% of final score)
        Format & Readability: {category_scores.get('format', 'N/A')}/100 (3% of final score)
        Errors & Consistency: {category_scores.get('errors', 'N/A')}/100 (2% of final score)

        FINAL WEIGHTED SCORE: {final_score:.1f}/100

        Please provide a detailed final assessment with:

        1. EXECUTIVE SUMMARY: A concise summary of how well this resume matches this specific job description

        2. STRENGTHS: The top 3 strengths of this resume for this specific job

        3. CRITICAL IMPROVEMENTS: The top 3 most critical improvements needed to better match this job description

        4. ATS ASSESSMENT: An assessment of the resume's likelihood of passing ATS filters for this specific job

        5. INTERVIEW POTENTIAL: An assessment of whether this resume would likely lead to an interview

        6. FINAL RECOMMENDATION: A clear verdict on whether the candidate should:
           a) Apply with this resume as is
           b) Make minor improvements before applying
           c) Make major improvements before applying

        Be specific about which improvements would have the biggest impact on ATS performance for this particular job.
        """

        response = self.call_llm(prompt, model=self.model)
        self.final_report = f"Final ATS Score for This Job: {final_score:.1f}/100\n\n{response}"

    def generate_visual_report(self, output_path="html/ats_report.html"):
        """
        Generate a visual HTML report with charts and formatted analysis

        Args:
            output_path (str): Path to save the HTML report

        Returns:
            str: Path to the generated report
        """
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # Create radar chart for scores
            categories = [
                'Keywords', 'Experience', 'ATS Simulation',
                'Industry Fit', 'Content Quality', 'Format', 'Errors'
            ]

            values = [
                self.scores.get('keywords', 0),
                self.scores.get('experience', 0),
                self.scores.get('ats_simulation', 0),
                self.scores.get('industry_specific', 0),
                self.scores.get('content', 0),
                self.scores.get('format', 0),
                self.scores.get('errors', 0)
            ]

            # Create radar chart
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111, polar=True)

            # Calculate angles for each category
            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()

            # Close the plot
            values.append(values[0])
            angles.append(angles[0])
            categories.append(categories[0])

            # Plot data
            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
            ax.set_ylim(0, 100)
            plt.title('Resume ATS Analysis Results', size=15)

            # Convert plot to base64 for embedding in HTML
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode()
            plt.close()

            # Import markdown to HTML converter
            try:
                import markdown
                markdown_available = True
            except ImportError:
                print("Warning: markdown package not installed. Markdown formatting will not be rendered.")
                print("Install with: pip install markdown")
                markdown_available = False

            # Function to convert markdown to HTML
            def md_to_html(text):
                if markdown_available:
                    # Convert markdown to HTML
                    try:
                        return markdown.markdown(text)
                    except:
                        return f"<pre>{text}</pre>"
                else:
                    return f"<pre>{text}</pre>"

            # Create HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ATS Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
                    .container {{ max-width: 1000px; margin: 0 auto; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .score-card {{ background-color: #f5f5f5; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                    .score-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                    .score-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                    .chart {{ text-align: center; margin: 30px 0; }}
                    .analysis-section {{ margin-bottom: 30px; }}
                    .improvement {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                    .category {{ font-weight: bold; color: #3498db; }}
                    .highlight {{ background-color: #ffffcc; padding: 2px 5px; }}
                    .progress-container {{ width: 100%; background-color: #e0e0e0; border-radius: 5px; margin: 5px 0; }}
                    .progress-bar {{ height: 20px; border-radius: 5px; }}
                    .good {{ background-color: #4CAF50; }}
                    .medium {{ background-color: #FFC107; }}
                    .poor {{ background-color: #F44336; }}
                    pre {{ white-space: pre-wrap; }}
                    .markdown-content {{ line-height: 1.6; }}
                    .markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4 {{ margin-top: 1.5em; margin-bottom: 0.5em; color: #2c3e50; }}
                    .markdown-content ul, .markdown-content ol {{ padding-left: 2em; }}
                    .markdown-content table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
                    .markdown-content th, .markdown-content td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .markdown-content th {{ background-color: #f2f2f2; }}
                    .markdown-content code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
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
                        <div class="score-value">{self.scores.get('final', 0):.1f}/100</div>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('final', 0) >= 80 else 'medium' if self.scores.get('final', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('final', 0)}%"></div>
                        </div>
                        <p>This score represents the overall effectiveness of your resume for this specific job.</p>
                    </div>

                    <div class="chart">
                        <h2>Score Breakdown</h2>
                        <img src="data:image/png;base64,{img_str}" alt="ATS Analysis Chart">
                    </div>

                    <div class="analysis-section">
                        <h2>Executive Summary</h2>
                        <div class="markdown-content">{md_to_html(self.final_report)}</div>
                    </div>

                    <div class="analysis-section">
                        <h2>ATS Simulation Results</h2>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('ats_simulation', 'Not available'))}</div>
                    </div>

                    <div class="improvement">
                        <h2>Recommended Improvements</h2>
                        <div class="markdown-content">{md_to_html(self.improvement_suggestions)}</div>
                    </div>

                    <div class="analysis-section">
                        <h2>Detailed Analysis</h2>

                        <h3 class="category">Keywords Match ({self.scores.get('keywords', 0)}/100)</h3>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('keywords', 0) >= 80 else 'medium' if self.scores.get('keywords', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('keywords', 0)}%"></div>
                        </div>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('keywords', 'Not available'))}</div>

                        <h3 class="category">Experience & Qualifications ({self.scores.get('experience', 0)}/100)</h3>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('experience', 0) >= 80 else 'medium' if self.scores.get('experience', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('experience', 0)}%"></div>
                        </div>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('experience', 'Not available'))}</div>

                        <h3 class="category">Format & Readability ({self.scores.get('format', 0)}/100)</h3>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('format', 0) >= 80 else 'medium' if self.scores.get('format', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('format', 0)}%"></div>
                        </div>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('format', 'Not available'))}</div>

                        <h3 class="category">Content Quality ({self.scores.get('content', 0)}/100)</h3>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('content', 0) >= 80 else 'medium' if self.scores.get('content', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('content', 0)}%"></div>
                        </div>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('content', 'Not available'))}</div>

                        <h3 class="category">Errors & Consistency ({self.scores.get('errors', 0)}/100)</h3>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('errors', 0) >= 80 else 'medium' if self.scores.get('errors', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('errors', 0)}%"></div>
                        </div>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('errors', 'Not available'))}</div>

                        <h3 class="category">Industry Alignment ({self.scores.get('industry_specific', 0)}/100)</h3>
                        <div class="progress-container">
                            <div class="progress-bar {'good' if self.scores.get('industry_specific', 0) >= 80 else 'medium' if self.scores.get('industry_specific', 0) >= 60 else 'poor'}"
                                 style="width: {self.scores.get('industry_specific', 0)}%"></div>
                        </div>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('industry_specific', 'Not available'))}</div>
                    </div>

                    <div class="analysis-section">
                        <h2>Competitive Analysis</h2>
                        <div class="markdown-content">{md_to_html(self.analysis_results.get('competitive', 'Not available'))}</div>
                    </div>

                    <div class="analysis-section">
                        <h2>Usage Statistics</h2>
                        <p>LLM API Calls: {self.llm_call_count}</p>
                        <p>Total Tokens Used: {self.total_tokens}</p>
                        <p>Analysis Time: {self.total_time:.2f} seconds</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Write HTML to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return output_path

        except Exception as e:
            print(f"Error generating visual report: {e}")
            return None

    def generate_text_report(self):
        """
        Generate a text-based report of the analysis

        Returns:
            str: Formatted text report
        """
        report = "=== ATS ANALYSIS REPORT ===\n\n"

        # Add final score
        report += f"FINAL SCORE: {self.scores.get('final', 0):.1f}/100\n\n"

        # Add individual scores
        report += "SCORE BREAKDOWN:\n"
        report += f"- Keywords Match: {self.scores.get('keywords', 0)}/100\n"
        report += f"- Experience Match: {self.scores.get('experience', 0)}/100\n"
        report += f"- ATS Simulation: {self.scores.get('ats_simulation', 0)}/100\n"
        report += f"- Format & Readability: {self.scores.get('format', 0)}/100\n"
        report += f"- Content Quality: {self.scores.get('content', 0)}/100\n"
        report += f"- Errors & Consistency: {self.scores.get('errors', 0)}/100\n"
        report += f"- Industry Alignment: {self.scores.get('industry_specific', 0)}/100\n\n"

        # Add final report
        report += "EXECUTIVE SUMMARY:\n"
        report += f"{self.final_report}\n\n"

        # Add improvement suggestions
        report += "RECOMMENDED IMPROVEMENTS:\n"
        report += f"{self.improvement_suggestions}\n\n"

        # Add usage statistics
        report += "USAGE STATISTICS:\n"
        report += f"- LLM API Calls: {self.llm_call_count}\n"
        report += f"- Total Tokens Used: {self.total_tokens}\n"
        report += f"- Analysis Time: {self.total_time:.2f} seconds\n"

        return report

    def call_llm(self, prompt, model=1):
        """
        Call the LLM API with the given prompt

        Args:
            prompt (str): The prompt to send to the LLM
            model (int): Model selection (1=OpenAI, 2=Groq)

        Returns:
            str: The LLM response
        """
        try:
            # Check if .env file exists and load it
            env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            if not os.path.exists(env_file_path):
                print(f"Warning: .env file not found at {env_file_path}")
                print("Creating a default .env file with placeholders for API keys")
                with open(env_file_path, 'w') as f:
                    f.write("# API Keys for ATS Analyzer\n")
                    f.write("# Replace with your actual API keys\n\n")
                    f.write("# OpenAI API Key\n")
                    f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
                    f.write("# Groq API Key (optional, only needed if using model=2)\n")
                    f.write("GROQ_API_KEY=your_groq_api_key_here\n")
                print(f"Please edit {env_file_path} and add your API keys")

                # Fallback to dummy response if no API keys are available
                return self._generate_dummy_response(prompt)

            # Reload environment variables
            from dotenv import load_dotenv
            load_dotenv(env_file_path)

            if model == 1:
                # Get OpenAI API key from environment variables
                openai_api_key = OPENAI_API_KEY
                if not openai_api_key or openai_api_key == "your_openai_api_key_here":
                    print("Error: OpenAI API key not found or not set in .env file")
                    print(f"Please edit {env_file_path} and add your OpenAI API key")
                    # Fallback to model 2 if OpenAI API key is not available
                    if model == 1:
                        print("Attempting to use Groq API instead...")
                        return self.call_llm(prompt, model=2)
                    else:
                        return self._generate_dummy_response(prompt)

                client = openai.OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # Can be configured as a parameter
                    messages=[
                        {"role": "system", "content": "You are an expert resume analyst and ATS specialist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )

                self.llm_call_count += 1
                self.total_tokens += response.usage.total_tokens
                return response.choices[0].message.content.strip()

            elif model == 2:
                try:
                    from groq import Groq
                except ImportError:
                    print("Error: Groq package not installed. Please install it with 'pip install groq'")
                    print("Falling back to OpenAI API...")
                    return self.call_llm(prompt, model=1)

                # Get Groq API key from environment variables
                groq_api_key = GROQ_API_KEY
                if not groq_api_key or groq_api_key == "your_groq_api_key_here":
                    print("Error: Groq API key not found or not set in .env file")
                    print(f"Please edit {env_file_path} and add your Groq API key")
                    print("Falling back to OpenAI API...")
                    return self.call_llm(prompt, model=1)

                client = Groq(api_key=groq_api_key)
                completion = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert resume analyst and ATS specialist."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_completion_tokens=1500,
                    top_p=1,
                    stream=False,
                    stop=None,
                )

                self.llm_call_count += 1
                self.total_tokens += completion.usage.total_tokens
                return completion.choices[0].message.content.strip()

            else:
                return "Error: Invalid model selection"

        except Exception as e:
            print(f"Error calling LLM API: {e}")
            # If there's an error with the API call, generate a dummy response
            return self._generate_dummy_response(prompt)

    def _generate_dummy_response(self, prompt):
        """
        Generate a dummy response when API calls fail
        This is used for testing or when API keys are not available

        Args:
            prompt (str): The original prompt

        Returns:
            str: A dummy response
        """
        print("Generating dummy response for testing purposes...")

        # Check what kind of analysis is being requested
        if "keywords" in prompt.lower():
            return "This is a dummy keywords analysis.\n\nThe resume contains some keywords that match the job description, but could be improved by adding more specific technical skills and qualifications.\n\nScore: 65 points"
        elif "experience" in prompt.lower():
            return "This is a dummy experience analysis.\n\nThe candidate's experience partially matches the job requirements. Some areas could be strengthened to better align with the position.\n\nScore: 70 points"
        elif "format" in prompt.lower():
            return "This is a dummy format analysis.\n\nThe resume has a clean format but could be improved with better section organization and more consistent formatting.\n\nScore: 75 points"
        elif "content" in prompt.lower():
            return "This is a dummy content quality analysis.\n\nThe content is generally good but could use more quantifiable achievements and specific examples.\n\nScore: 68 points"
        elif "errors" in prompt.lower():
            return "This is a dummy errors analysis.\n\nThe resume has few grammatical errors but some inconsistencies in formatting and punctuation.\n\nScore: 80 points"
        elif "industry" in prompt.lower():
            return "This is a dummy industry analysis.\n\nThe resume shows good industry alignment but could benefit from more industry-specific terminology.\n\nScore: 72 points"
        elif "competitive" in prompt.lower():
            return "This is a dummy competitive analysis.\n\nThe resume is competitive but could be strengthened in areas of technical expertise and project outcomes.\n\nScore: 70 points"
        elif "improvements" in prompt.lower():
            return "This is a dummy improvement suggestions.\n\n1. Add more technical keywords from the job description\n2. Quantify achievements with specific metrics\n3. Improve formatting for better ATS readability"
        elif "final assessment" in prompt.lower():
            return "This is a dummy final assessment.\n\nThe resume is generally well-aligned with the job description but has room for improvement in keyword matching and experience presentation.\n\nFinal recommendation: Make minor improvements before applying."
        else:
            return "This is a dummy response for testing purposes. In a real scenario, this would contain a detailed analysis based on your prompt.\n\nScore: 70 points"

    def extract_score(self, response_text):
        """
        Extract score from LLM response

        Args:
            response_text (str): LLM response text

        Returns:
            int: Extracted score (0-100)
        """
        import re

        # Look for score in format "Score: XX points" or similar patterns
        patterns = [
            r'Score:\s*(\d+)\s*points',
            r'Score:\s*(\d+)',
            r'score of\s*(\d+)',
            r'rated at\s*(\d+)',
            r'(\d+)/100',
            r'(\d+)\s*out of\s*100'
        ]

        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                # Ensure score is in range 0-100
                return max(0, min(100, score))

        # Default score if no match found
        return 50

    def run_full_analysis(self, advanced=True, generate_html=True):
        """
        Run the complete resume analysis

        Args:
            advanced (bool): Whether to run advanced analyses
            generate_html (bool): Whether to generate HTML report

        Returns:
            str: Path to the report or text report
        """
        start_time = time.time()

        print("Starting ATS analysis for this specific job description...")

        # Extract and preprocess resume text (this also analyzes the JD)
        self.extract_and_preprocess()

        print(f"Analyzing resume against {len(self.jd_keywords)} job-specific keywords...")

        # Run basic analyses
        self.analyze_keywords()
        self.analyze_experience_and_qualifications()
        self.analyze_format_and_readability()
        self.analyze_content_quality()
        self.check_errors_and_consistency()

        # Run advanced analyses if requested
        if advanced:
            print("Running advanced ATS simulation...")
            self.simulate_ats_filtering()
            self.analyze_industry_specific()
            self.analyze_competitive_position()

        # Generate improvement suggestions
        print("Generating job-specific improvement suggestions...")
        self.suggest_resume_improvements()

        # Generate final score and report
        print("Calculating final ATS score for this job...")
        self.generate_final_score_and_recommendations()

        # Record total time
        self.total_time = time.time() - start_time
        print(f"Analysis completed in {self.total_time:.1f} seconds")

        # Print usage statistics to console
        self.print_usage_statistics()

        # Generate and return report
        if generate_html:
            print("Generating visual HTML report...")
            report_path = self.generate_visual_report()
            print(f"HTML report generated: {report_path}")
            return report_path
        else:
            return self.generate_text_report()

    def print_usage_statistics(self):
        """
        Print usage statistics to console
        """
        print("\n===== USAGE STATISTICS =====")
        print(f"LLM API Calls: {self.llm_call_count}")
        print(f"Total Tokens Used: {self.total_tokens}")
        print(f"Analysis Time: {self.total_time:.2f} seconds")

        print("\n===== SCORE BREAKDOWN =====")
        print(f"Final ATS Score: {self.scores.get('final', 0):.1f}/100")
        print(f"Keywords Match: {self.scores.get('keywords', 0)}/100")
        print(f"Experience Match: {self.scores.get('experience', 0)}/100")
        print(f"ATS Simulation: {self.scores.get('ats_simulation', 0)}/100")
        print(f"Format & Readability: {self.scores.get('format', 0)}/100")
        print(f"Content Quality: {self.scores.get('content', 0)}/100")
        print(f"Errors & Consistency: {self.scores.get('errors', 0)}/100")
        print(f"Industry Alignment: {self.scores.get('industry_specific', 0)}/100")
        print("============================\n")


# if __name__ == "__main__":
#     cv_path = "../JobPT_Test/pdf/Minwoo.pdf" 
#     model = 1  # 1=OpenAI, 2=Groq
#     advanced = False 
#     generate_html = True  

#     jd_text = """
# Responsibilities:

# Shape Zoom AI's future via groundbreaking research. Incubate AI models, algorithms, and techniques for next generation business applications by collaborating with experienced researchers and engineers;
# Join AI projects, work with diverse teams, and achieve exciting results;
# The AI incubation team is dedicated to Incubate AI breakthroughs, including foundational AI techniques and AI native applications that will largely improve people's work productivity;
# Incubate foundation techniques for AGI, including new model structure, optimization techniques and distributed learning algorithms;
# Incubate game-changing AI applications which will create huge potential business impact;
# Collaborate with cross-functional teams to solve unique product problem;
# Communicate technical concepts clearly in team discussions and presentations for technical and nontechnical audiences;
# Foster growth in the AI research community by contributing to research papers for conferences and journals; and
# Receive mentorship and providing insights drive innovation with experienced researchers and team members.




# What we're looking for:

# Requires a Master's degree in Computer Science, Intelligent Information Systems, a related field, or a foreign degree equivalent;
# Must have 1 year of experience in job offered or related occupation;
# Must have 1 year of experience in experience in AI research or engineering practice in large scale distributed systems;
# Must have 1 year of experience in developing distributed deep learning training system;
# Must have 1 year of experience in optimizing efficiency of distributed training system;
# Must have 1 year of experience in optimizing robustness of distributed training system;
# Must have 1 year of experience in one of the programming languages: Python/C/C++/CUDA, and deep learning frameworks, such as PyTorch, Transformers and Deepspeed;
# Must have 1 year of experience in Python Coding;
# Must have 1 year of experience in developing new deep learning model to solve product problems;
# Must have 1 year of experience in optimizing model parameters for better accuracy; and
# Must have 1 year of experience in building AI solutions with deep learning models.
# Salary Range or On Target Earnings:

# Minimum:

# $180,000.00
# Maximum:

# $255,400.00
# In addition to the base salary and/or OTE listed Zoom has a Total Direct Compensation philosophy that takes into consideration; base salary, bonus and equity value.

# Note: Starting pay will be based on a number of factors and commensurate with qualifications & experience.

# We also have a location based compensation structure;  there may be a different range for candidates in this and other locations.

# Ways of Working
# Our structured hybrid approach is centered around our offices and remote work environments. The work style of each role, Hybrid, Remote, or In-Person is indicated in the job description/posting.

# Benefits
# As part of our award-winning workplace culture and commitment to delivering happiness, our benefits program offers a variety of perks, benefits, and options to help employees maintain their physical, mental, emotional, and financial health; support work-life balance; and contribute to their community in meaningful ways. Click Learn for more information.

# About Us
# Zoomies help people stay connected so they can get more done together. We set out to build the best collaboration platform for the enterprise, and today help people communicate better with products like Zoom Contact Center, Zoom Phone, Zoom Events, Zoom Apps, Zoom Rooms, and Zoom Webinars.
# We're problem-solvers, working at a fast pace to design solutions with our customers and users in mind. Here, you'll work across teams to deliver impactful projects that are changing the way people communicate and enjoy opportunities to advance your career in a diverse, inclusive environment.


# Our Commitment​
# We believe that the unique contributions of all Zoomies is the driver of our success. To make sure that our products and culture continue to incorporate everyone's perspectives and experience we never discriminate on the basis of race, religion, national origin, gender identity or expression, sexual orientation, age, or marital, veteran, or disability status. Zoom is proud to be an equal opportunity workplace and is an affirmative action employer. All your information will be kept confidential according to EEO guidelines.

# We welcome people of different backgrounds, experiences, abilities and perspectives including qualified applicants with arrest and conviction records and any qualified applicants requiring reasonable accommodations in accordance with the law.

# If you need assistance navigating the interview process due to a medical disability, please submit an Accommodations Request Form and someone from our team will reach out soon. This form is solely for applicants who require an accommodation due to a qualifying medical disability. Non-accommodation-related requests, such as application follow-ups or technical issues, will not be addressed.

# Think of this opportunity as a marathon, not a sprint! We're building a strong team at Zoom, and we're looking for talented individuals to join us for the long haul. No need to rush your application – take your time to ensure it's a good fit for your career goals. We continuously review applications, so submit yours whenever you're ready to take the next step.

#     """

#     analyzer = ATSAnalyzer(cv_path, jd_text, model=model)
#     result = analyzer.run_full_analysis(advanced=advanced, generate_html=generate_html)

#     if not generate_html:
#         print(result)
#     else:
#         print(f"\n분석 완료! 보고서가 저장된 경로: {result}")
#         print("웹 브라우저에서 HTML 파일을 열어 전체 보고서를 확인하세요.")

# # %%
