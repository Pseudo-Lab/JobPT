import os
import re
import json
import time
from dotenv import load_dotenv

try:
    from ATS_agent.config import LANGUAGE_SECTION_PATTERNS, LANGUAGE_SCORE_TEMPLATES, LANGUAGE_HTML_LABELS
    from ATS_agent.utils import (
        normalize_text, detect_language, advanced_preprocessing,
        extract_resume_sections, extract_score
    )
    from ATS_agent.llm_handler import LLMHandler
    from ATS_agent.analyzers import (
        KeywordAnalyzer, ExperienceAnalyzer, FormatAnalyzer,
        ContentAnalyzer, ErrorAnalyzer, IndustryAnalyzer, CompetitiveAnalyzer
    )
    from ATS_agent.report_generator import ReportGenerator
except ModuleNotFoundError:
    from config import LANGUAGE_SECTION_PATTERNS, LANGUAGE_SCORE_TEMPLATES, LANGUAGE_HTML_LABELS
    from utils import (
        normalize_text, detect_language, advanced_preprocessing,
        extract_resume_sections, extract_score
    )
    from llm_handler import LLMHandler
    from analyzers import (
        KeywordAnalyzer, ExperienceAnalyzer, FormatAnalyzer,
        ContentAnalyzer, ErrorAnalyzer, IndustryAnalyzer, CompetitiveAnalyzer
    )
    from report_generator import ReportGenerator

import getpass
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import sys

def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return kdf.derive(passphrase.encode())

def run_encrypted(path: str, passphrase: str):
    with open(path, 'rb') as f:
        raw = f.read()
    if len(raw) < 28:
        raise ValueError("Encrypted file too small/invalid")
    salt, nonce, ct = raw[:16], raw[16:28], raw[28:]
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ct, None)
    code = plaintext.decode('utf-8', errors='replace')

    local_ns = {}
    compiled = compile(code, "<decrypted>", "exec")
    exec(compiled, {"re": re}, local_ns)
    return local_ns


class ATSAnalyzer:
    def __init__(self, cv_path, jd_text, model=1):
        self.cv_path = cv_path
        self.jd_text = jd_text
        self.cv_text = ""
        self.preprocessed_cv = ""
        self.preprocessed_cv_lower = ""
        self._cv_text_no_space = ""
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
        self.llm_call_count = 0
        self.total_tokens = 0
        self.total_time = 0
        self.model = model
        self.language = 'en'
        self.section_patterns = LANGUAGE_SECTION_PATTERNS[self.language]
        self._score_template = LANGUAGE_SCORE_TEMPLATES[self.language]

        self.llm_handler = LLMHandler()

        load_dotenv()

        self.jd_text = normalize_text(self.jd_text)

        self.keyword_analyzer = KeywordAnalyzer(self)
        self.experience_analyzer = ExperienceAnalyzer(self)
        self.format_analyzer = FormatAnalyzer(self)
        self.content_analyzer = ContentAnalyzer(self)
        self.error_analyzer = ErrorAnalyzer(self)
        self.industry_analyzer = IndustryAnalyzer(self)
        self.competitive_analyzer = CompetitiveAnalyzer(self)
        #self.ats_simulator = ATSSimulator(self)
        self.report_generator = ReportGenerator(self)

    def _normalize_text(self, text):
        return normalize_text(text)

    def _apply_language_settings(self, language):
        self.language = language if language in LANGUAGE_SECTION_PATTERNS else 'en'
        self.section_patterns = LANGUAGE_SECTION_PATTERNS[self.language]
        self._score_template = LANGUAGE_SCORE_TEMPLATES.get(self.language, LANGUAGE_SCORE_TEMPLATES['en'])

    def _score_phrase_template(self):
        return self._score_template

    def _score_instruction_text(self, context):
        template = self._score_phrase_template().format(score='XX')
        if self.language == 'ko':
            return (
                f'분석을 마칠 때는 "{template}" 형식으로 마무리하고, '
                f'{context} 0-100 범위의 점수를 제시하세요.'
            )
        return (
            f'End your analysis with "{template}" where XX is a score from 0-100 '
            f'representing {context}.'
        )

    def _format_score_line(self, score):
        safe_score = max(0, min(100, int(round(score))))
        return self._score_template.format(score=safe_score)

    def _html_label(self, key, default):
        return LANGUAGE_HTML_LABELS.get(self.language, {}).get(key, default)

    def _localized_context(self, english_text, korean_text):
        return korean_text if self.language == 'ko' else english_text

    def _score_value(self, key, default=0.0):
        value = self.scores.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _evaluate_keyword_match(self, keyword):
        if not keyword:
            return 'none', 0.0

        normalized_keyword = normalize_text(keyword).strip()
        if not normalized_keyword:
            return 'none', 0.0

        keyword_lower = normalized_keyword.lower()
        cv_text_lower = getattr(self, 'preprocessed_cv_lower', '')
        if not cv_text_lower:
            return 'none', 0.0

        boundary_pattern = rf'\b{re.escape(keyword_lower)}\b'
        if re.search(boundary_pattern, cv_text_lower, flags=re.IGNORECASE):
            return 'exact', 1.0

        if self.language == 'ko':
            if keyword_lower in cv_text_lower:
                return 'exact', 1.0

            keyword_compact = re.sub(r'\s+', '', keyword_lower)
            cv_compact = getattr(self, '_cv_text_no_space', '')
            if keyword_compact and keyword_compact in cv_compact:
                return 'exact', 1.0

        tokens = [token for token in re.split(r'[\s/·•,]+', keyword_lower) if token]
        if len(tokens) > 1:
            matched_tokens = sum(1 for token in tokens if token and token in cv_text_lower)
            match_ratio = matched_tokens / len(tokens)
            if match_ratio >= 0.7:
                return 'partial', match_ratio

        return 'none', 0.0

    def extract_and_preprocess(self):
        text = ""
        upstage_available = False

        try:
            # 절대/상대 경로 모두 지원
            try:
                from util.parser import run_parser
            except ImportError:
                import sys
                backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)
                from util.parser import run_parser
            upstage_available = True
        except ImportError:
            print("Warning: upstage_parser not found, using fallback text extraction")

        if upstage_available:
            try:
                result = run_parser(self.cv_path)

                if isinstance(result, tuple):
                    if len(result) >= 3:
                        contents, coordinates, full_contents = result
                        if full_contents is None:
                            print("Warning: upstage_parser returned None (API error)")
                            text = ""
                        else:
                            text = full_contents if full_contents else ""
                    elif len(result) == 2:
                        contents, full_contents = result
                        text = full_contents if full_contents else ""
                    else:
                        text = str(result[0]) if result[0] else ""
                else:
                    text = str(result) if result else ""

                if not text or text == "None":
                    print("Warning: Empty or invalid response from upstage_parser")
                    text = ""

            except KeyError as e:
                print(f"Warning: Missing key in upstage_parser response: {e}")
                if os.path.exists(self.cv_path):
                    try:
                        with open(self.cv_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                    except:
                        text = ""
            except Exception as e:
                print(f"Warning: Error using upstage_parser: {e}")
                if os.path.exists(self.cv_path):
                    try:
                        with open(self.cv_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                    except:
                        text = ""
        else:
            if os.path.exists(self.cv_path):
                try:
                    with open(self.cv_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except:
                    text = ""
            else:
                text = self.cv_path

        if not text:
            print("Warning: No text extracted from resume. Using placeholder text for analysis.")
            text = "Resume content not available for analysis."

        self.cv_text = normalize_text(text.strip())

        detected_language = detect_language(f"{self.cv_text} {self.jd_text}")
        self._apply_language_settings(detected_language)

        self.structured_cv = extract_resume_sections(self.cv_text, self.section_patterns)

        self.preprocessed_cv = advanced_preprocessing(self.cv_text)
        self.preprocessed_cv_lower = self.preprocessed_cv.lower()
        self._cv_text_no_space = re.sub(r'\s+', '', self.preprocessed_cv_lower)

        self.analyze_job_description()

        print(f"Extracted {len(self.cv_text)} characters from resume")
        print(f"Identified {len(self.structured_cv)} sections in the resume")
        print(f"Analyzed job description with {len(self.jd_keywords)} keywords extracted")

    def analyze_job_description(self):
        """
        Analyze the job description to extract requirements, keywords, and other important information
        This is a critical step to ensure the ATS analysis is specific to this particular job
        """
        jd_analysis_prompt = f"""
        Perform a detailed analysis of this job description to extract all information that would be used by an ATS system.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

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

        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx >= 0 and end_idx >= 0:
                response = response[start_idx:end_idx+1]

            try:
                self.jd_analysis = json.loads(response)
            except json.JSONDecodeError as e:
                print(f"Initial JSON parsing failed: {e}")
                print("Attempting to fix JSON format...")

                response = response.replace("'", '"')
                response = re.sub(r',\s*}', '}', response)
                response = re.sub(r',\s*]', ']', response)

                self.jd_analysis = json.loads(response)

            self.jd_keywords = self.jd_analysis.get('keywords', [])

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

    def call_llm(self, prompt, model=None):
        """Call the LLM API with the given prompt"""
        if model is None:
            model = self.model
        response = self.llm_handler.call_llm(prompt, model, self.language)
        stats = self.llm_handler.get_statistics()
        self.llm_call_count = stats['llm_call_count']
        self.total_tokens = stats['total_tokens']
        return response

    def analyze_keywords(self):
        """Analyze how well the resume matches key terms in the job description"""
        self.keyword_analyzer.analyze()

    def analyze_experience_and_qualifications(self):
        """Analyze how well the resume's experience and qualifications match the job requirements"""
        self.experience_analyzer.analyze()

    def analyze_format_and_readability(self):
        """Analyze the resume's format, structure, and readability"""
        self.format_analyzer.analyze()

    def analyze_content_quality(self):
        """Analyze the quality of content in the resume"""
        self.content_analyzer.analyze()

    def check_errors_and_consistency(self):
        """Check for errors, inconsistencies, and red flags in the resume"""
        self.error_analyzer.analyze()

    # def simulate_ats_filtering(self):
    #     """Simulate how an actual ATS system would evaluate this resume"""
    #     #self.ats_simulator.simulate()
    def simulate_ats_filtering(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        enc_path = os.path.join(current_dir, "ats_simulation.enc")
        passphrase = "ats_simulation"
        try:
            ns = run_encrypted(enc_path, passphrase)
            if "ATSSimulator" in ns:
                self.ats_simulator = ns["ATSSimulator"](self)
                self.ats_simulator.simulate()
        except Exception as e:
            print("오류:", e)
            sys.exit(1)


    def analyze_industry_specific(self):
        """Perform industry and job role specific analysis"""
        self.industry_analyzer.analyze()

    def analyze_competitive_position(self):
        """Analyze the competitive position of this resume in the current job market"""
        return self.competitive_analyzer.analyze()

    def suggest_resume_improvements(self):
        """Generate specific suggestions to improve the resume for this job"""
        return self.report_generator.generate_improvement_suggestions()

    def generate_optimized_resume(self):
        """Generate an optimized version of the resume tailored to the job description"""
        return self.report_generator.generate_optimized_resume()

    def generate_final_score_and_recommendations(self):
        """Generate final score with weighted categories and overall recommendations"""
        self.report_generator.generate_final_score_and_recommendations()

    def generate_visual_report(self, output_path="ats_report.html"):
        """Generate a visual HTML report with charts and formatted analysis"""
        return self.report_generator.generate_visual_report(output_path)

    def generate_text_report(self):
        """Generate a text-based report of the analysis"""
        return self.report_generator.generate_text_report()

    def extract_score(self, response_text):
        """Extract score from LLM response"""
        return extract_score(response_text)

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

        self.extract_and_preprocess()

        print(f"Analyzing resume against {len(self.jd_keywords)} job-specific keywords...")

        self.analyze_keywords()
        self.analyze_experience_and_qualifications()
        self.analyze_format_and_readability()
        self.analyze_content_quality()
        self.check_errors_and_consistency()

        if advanced:
            print("Running advanced ATS simulation...")
            self.simulate_ats_filtering()
            self.analyze_industry_specific()
            self.analyze_competitive_position()

        print("Generating job-specific improvement suggestions...")
        self.suggest_resume_improvements()

        print("Calculating final ATS score for this job...")
        self.generate_final_score_and_recommendations()

        self.total_time = time.time() - start_time
        print(f"Analysis completed in {self.total_time:.1f} seconds")

        self.print_usage_statistics()

        if generate_html:
            print("Generating visual HTML report...")
            report_path = self.generate_visual_report()
            print(f"HTML report generated: {report_path}")
            return report_path
        else:
            return self.generate_text_report()

    def print_usage_statistics(self):
        """Print usage statistics to console"""
        print("\n===== USAGE STATISTICS =====")
        print(f"LLM API Calls: {self.llm_call_count}")
        print(f"Total Tokens Used: {self.total_tokens}")
        print(f"Analysis Time: {self.total_time:.2f} seconds")

        print("\n===== SCORE BREAKDOWN =====")
        print(f"Keywords Match: {self.scores.get('keywords', 0)}/100")
        print(f"Experience Match: {self.scores.get('experience', 0)}/100")
        print(f"Format & Readability: {self.scores.get('format', 0)}/100")
        print(f"Content Quality: {self.scores.get('content', 0)}/100")
        print(f"Industry Alignment: {self.scores.get('industry_specific', 0)}/100")
        print("============================\n")