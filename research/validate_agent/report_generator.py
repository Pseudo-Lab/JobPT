import os
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
from config import LANGUAGE_CATEGORY_LABELS, LANGUAGE_HTML_LABELS, SCORE_WEIGHTS
from utils import configure_plot_fonts, restore_plot_fonts, render_markdown


class ReportGenerator:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def generate_improvement_suggestions(self):
        prompt = f"""
        Based on the comprehensive analysis of this resume against the job description, provide specific, actionable improvements.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION:
        {self.analyzer.jd_text}

        RESUME:
        {self.analyzer.preprocessed_cv}

        ANALYSIS RESULTS:
        Keywords Analysis: {self.analyzer.scores.get('keywords', 'N/A')}/100
        Experience Match: {self.analyzer.scores.get('experience', 'N/A')}/100
        Format & Readability: {self.analyzer.scores.get('format', 'N/A')}/100
        Content Quality: {self.analyzer.scores.get('content', 'N/A')}/100
        Errors & Consistency: {self.analyzer.scores.get('errors', 'N/A')}/100
        ATS Simulation: {self.analyzer.scores.get('ats_simulation', 'N/A')}/100
        Industry Alignment: {self.analyzer.scores.get('industry_specific', 'N/A')}/100


        Please provide specific, actionable improvements in these categories:


        1. CRITICAL ADDITIONS: Keywords and qualifications that must be added
        2. CONTENT ENHANCEMENTS: How to strengthen existing content
        3. FORMAT IMPROVEMENTS: Structural changes to improve ATS compatibility
        4. REMOVAL SUGGESTIONS: Content that should be removed or de-emphasized
        5. SECTION-BY-SECTION RECOMMENDATIONS: Specific improvements for each resume section


        For each suggestion, provide a clear before/after example where possible.
        Focus on the most impactful changes that will significantly improve ATS performance and human readability.
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        self.analyzer.improvement_suggestions = response
        return response

    def generate_optimized_resume(self):
        prompt = f"""
        Create an optimized version of this resume specifically tailored for the job description.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

        JOB DESCRIPTION:
        {self.analyzer.jd_text}

        CURRENT RESUME:
        {self.analyzer.preprocessed_cv}

        Please rewrite the resume to:
        1. Incorporate all relevant keywords from the job description
        2. Highlight the most relevant experience and qualifications
        3. Use ATS-friendly formatting and structure
        4. Quantify achievements where possible
        5. Remove or downplay irrelevant information


        The optimized resume should maintain truthfulness while presenting the candidate in the best possible light for this specific position.
        Use standard resume formatting with clear section headers.
        """

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        self.analyzer.optimized_resume = response
        return response

    def generate_final_score_and_recommendations(self):
        weighted_sum = 0
        used_weights_sum = 0
        category_scores = {}

        for category, weight in SCORE_WEIGHTS.items():
            if category in self.analyzer.scores:
                score = self.analyzer.scores[category]
                try:
                    score_value = float(score)
                except (TypeError, ValueError):
                    continue

                weighted_sum += score_value * weight
                used_weights_sum += weight
                category_scores[category] = score_value

        if used_weights_sum > 0:
            final_score = weighted_sum / used_weights_sum
        else:
            numeric_scores = []
            for key, value in self.analyzer.scores.items():
                if key == 'final':
                    continue
                try:
                    numeric_scores.append(float(value))
                except (TypeError, ValueError):
                    continue
            final_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0

        self.analyzer.scores['final'] = final_score

        jd_summary = ""
        if self.analyzer.jd_analysis:
            jd_summary = "JOB DESCRIPTION ANALYSIS:\n"
            if self.analyzer.jd_analysis.get('required_qualifications'):
                jd_summary += "Required Qualifications: " + ", ".join(self.analyzer.jd_analysis.get('required_qualifications')[:5]) + "\n"
            if self.analyzer.jd_analysis.get('technical_skills'):
                jd_summary += "Technical Skills: " + ", ".join(self.analyzer.jd_analysis.get('technical_skills')[:5]) + "\n"
            if self.analyzer.jd_analysis.get('key_responsibilities'):
                jd_summary += "Key Responsibilities: " + ", ".join(self.analyzer.jd_analysis.get('key_responsibilities')[:3]) + "\n"

        prompt = f"""
        Based on the comprehensive analysis of this resume against the job description, provide a final assessment and recommendations.
        **IMPORTANT: OUTPUT LANGUAGE MUST FOLLOW CV and JD LANGUAGE**

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

        response = self.analyzer.call_llm(prompt, model=self.analyzer.model)
        self.analyzer.final_report = response

    def generate_visual_report(self, output_path="ats_report.html"):
        try:
            categories = LANGUAGE_CATEGORY_LABELS.get(
                self.analyzer.language,
                LANGUAGE_CATEGORY_LABELS['en']
            ).copy()

            values = [
                self.analyzer._score_value('keywords'),
                self.analyzer._score_value('experience'),
                self.analyzer._score_value('industry_specific'),
                self.analyzer._score_value('content'),
                self.analyzer._score_value('format')
            ]

            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111, polar=True)

            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()

            values.append(values[0])
            angles.append(angles[0])
            categories.append(categories[0])

            font_settings = configure_plot_fonts(self.analyzer.language)
            _, font_prop = font_settings if font_settings else (None, None)

            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
            ax.set_ylim(0, 100)
            title_text = self.analyzer._html_label('title', 'Resume ATS Analysis Report')
            if font_prop:
                ax.set_title(title_text, fontproperties=font_prop, size=15)
            else:
                ax.set_title(title_text, size=15)

            if font_prop:
                for label in ax.get_xticklabels() + ax.get_yticklabels():
                    label.set_fontproperties(font_prop)

            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            img_str = base64.b64encode(buffer.read()).decode()
            plt.close()
            restore_plot_fonts(font_settings)

            html_content = self._generate_html_content(img_str)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return output_path

        except Exception as e:
            print(f"Error generating visual report: {e}")
            return None

    def _generate_html_content(self, img_str):
        html_title = self.analyzer._html_label('title', 'Resume ATS Analysis Report')
        analysis_date_label = self.analyzer._html_label('analysis_date', 'Analysis Date')
        score_breakdown_label = self.analyzer._html_label('score_breakdown', 'Score Breakdown')
        executive_summary_label = self.analyzer._html_label('executive_summary', 'Executive Summary')
        ats_results_label = self.analyzer._html_label('ats_results', 'ATS Simulation Results')
        improvement_label = self.analyzer._html_label('improvement', 'Recommended Improvements')
        detailed_label = self.analyzer._html_label('detailed_analysis', 'Detailed Analysis')
        keywords_label = self.analyzer._html_label('keywords_match', 'Keywords Match')
        experience_label = self.analyzer._html_label('experience_match', 'Experience & Qualifications')
        industry_label = self.analyzer._html_label('industry_alignment', 'Industry Alignment')
        content_label = self.analyzer._html_label('content_quality', 'Content Quality')
        format_label = self.analyzer._html_label('format_quality', 'Format & Readability')
        error_label = self.analyzer._html_label('error_check', 'Errors & Consistency')
        chart_alt = self.analyzer._localized_context("ATS Analysis Chart", "ATS 분석 차트")
        not_available = self.analyzer._localized_context("Not available", "제공되지 않음")

        score_values = {
            'final': self.analyzer._score_value('final'),
            'keywords': self.analyzer._score_value('keywords'),
            'experience': self.analyzer._score_value('experience'),
            'format': self.analyzer._score_value('format'),
            'content': self.analyzer._score_value('content'),
            'errors': self.analyzer._score_value('errors'),
            'industry_specific': self.analyzer._score_value('industry_specific'),
            'ats_simulation': self.analyzer._score_value('ats_simulation'),
        }

        def progress_class(value):
            return 'good' if value >= 80 else 'medium' if value >= 60 else 'poor'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{html_title}</title>
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
                    <h1>{html_title}</h1>
                    <p>{analysis_date_label}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="chart">
                    <h2>{score_breakdown_label}</h2>
                    <img src="data:image/png;base64,{img_str}" alt="{chart_alt}">
                </div>

                <div class="analysis-section">
                    <h2>{executive_summary_label}</h2>
                    <div class="markdown-content">{render_markdown(self.analyzer.final_report)}</div>
                </div>

                <div class="improvement">
                    <h2>{improvement_label}</h2>
                    <div class="markdown-content">{render_markdown(self.analyzer.improvement_suggestions)}</div>
                </div>

                <div class="analysis-section">
                    <h2>{detailed_label}</h2>

                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('ats_simulation', not_available))}</div>

                    <h3 class="category">{keywords_label} ({score_values['keywords']:.0f}/100)</h3>
                    <div class="progress-container">
                        <div class="progress-bar {progress_class(score_values['keywords'])}"
                             style="width: {score_values['keywords']:.1f}%"></div>
                    </div>
                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('keywords', not_available))}</div>

                    <h3 class="category">{experience_label} ({score_values['experience']:.0f}/100)</h3>
                    <div class="progress-container">
                        <div class="progress-bar {progress_class(score_values['experience'])}"
                             style="width: {score_values['experience']:.1f}%"></div>
                    </div>
                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('experience', not_available))}</div>

                    <h3 class="category">{format_label} ({score_values['format']:.0f}/100)</h3>
                    <div class="progress-container">
                        <div class="progress-bar {progress_class(score_values['format'])}"
                             style="width: {score_values['format']:.1f}%"></div>
                    </div>
                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('format', not_available))}</div>

                    <h3 class="category">{content_label} ({score_values['content']:.0f}/100)</h3>
                    <div class="progress-container">
                        <div class="progress-bar {progress_class(score_values['content'])}"
                             style="width: {score_values['content']:.1f}%"></div>
                    </div>
                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('content', not_available))}</div>

                    <h3 class="category">{industry_label} ({score_values['industry_specific']:.0f}/100)</h3>
                    <div class="progress-container">
                        <div class="progress-bar {progress_class(score_values['industry_specific'])}"
                             style="width: {score_values['industry_specific']:.1f}%"></div>
                    </div>
                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('industry_specific', not_available))}</div>
                </div>

                <div class="analysis-section">
                    <h2>{self.analyzer._localized_context('Competitive Analysis', '경쟁력 분석')}</h2>
                    <div class="markdown-content">{render_markdown(self.analyzer.analysis_results.get('competitive', not_available))}</div>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def generate_text_report(self):
        report = "=== ATS ANALYSIS REPORT ===\n\n"

        report += "SCORE BREAKDOWN:\n"
        report += f"- Keywords Match: {self.analyzer._score_value('keywords'):.0f}/100\n"
        report += f"- Experience Match: {self.analyzer._score_value('experience'):.0f}/100\n"
        report += f"- Format & Readability: {self.analyzer._score_value('format'):.0f}/100\n"
        report += f"- Content Quality: {self.analyzer._score_value('content'):.0f}/100\n"
        report += f"- Industry Alignment: {self.analyzer._score_value('industry_specific'):.0f}/100\n\n"

        report += "EXECUTIVE SUMMARY:\n"
        report += f"{self.analyzer.final_report}\n\n"

        report += "RECOMMENDED IMPROVEMENTS:\n"
        report += f"{self.analyzer.improvement_suggestions}\n\n"

        report += "USAGE STATISTICS:\n"
        report += f"- LLM API Calls: {self.analyzer.llm_call_count}\n"
        report += f"- Total Tokens Used: {self.analyzer.total_tokens}\n"
        report += f"- Analysis Time: {self.analyzer.total_time:.2f} seconds\n"

        return report