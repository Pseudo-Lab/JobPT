# Advanced Job-Specific ATS Resume Analyzer

This tool analyzes resumes against specific job descriptions to simulate how an Applicant Tracking System (ATS) would evaluate them. It provides detailed feedback and improvement suggestions to help optimize resumes for specific job applications. The analyzer is designed to be highly job-specific, analyzing each job description in detail to provide the most accurate assessment of how well a resume matches that particular job.

## Features

- **Job Description Analysis**: Thoroughly analyzes each job description to extract requirements, skills, and keywords
- **Job-Specific Evaluation**: Evaluates the resume specifically against the analyzed job description
- **Comprehensive Analysis**: Evaluates keywords, experience, format, content quality, errors, and industry alignment
- **Advanced ATS Simulation**: Simulates actual ATS filtering with weighted keyword matching specific to the job
- **Partial Keyword Matching**: Detects partial matches for multi-word keywords and phrases
- **Industry-Specific Analysis**: Tailors analysis to specific industries and job roles
- **Visual Reports**: Generates interactive HTML reports with charts and detailed feedback
- **Job-Specific Improvement Suggestions**: Provides actionable recommendations to improve ATS compatibility for the specific job
- **Competitive Analysis**: Evaluates how the resume compares to typical candidates for this specific position
- **Optimized Resume Generation**: Creates an optimized version of the resume tailored to the specific job

## Setup

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up API keys in the `.env` file:
   ```
   # Replace with your actual API keys
   OPENAI_API_KEY=your_openai_api_key_here
   GROQ_API_KEY=your_groq_api_key_here  # Optional
   ```

## Usage

### Basic Usage

```python
from ats_analyzer_improved import ATSAnalyzer

# Initialize analyzer with resume path and job description
analyzer = ATSAnalyzer("path/to/resume.pdf", "Job description text here")

# Run analysis and generate HTML report
report_path = analyzer.run_full_analysis()
print(f"Report generated at: {report_path}")
```

### Command Line Usage

```bash
# Basic analysis with default settings
python ats_analyzer_improved.py

# Specify resume path
python ats_analyzer_improved.py --cv path/to/resume.pdf

# Use Groq API instead of OpenAI
python ats_analyzer_improved.py --model 2

# Run only basic analysis (faster)
python ats_analyzer_improved.py --basic

# Generate text report instead of HTML
python ats_analyzer_improved.py --text
```

## Output

The analyzer generates either:
- An HTML report with interactive charts and detailed analysis
- A text report with scores and recommendations

## Advanced Configuration

You can customize the analysis by modifying the weights in the `generate_final_score_and_recommendations` method:

```python
weights = {
    'keywords': 0.25,         # Keywords are critical for ATS
    'experience': 0.20,       # Experience match is very important
    'ats_simulation': 0.20,   # Direct ATS simulation
    'industry_specific': 0.15, # Industry relevance
    'content': 0.10,          # Content quality
    'format': 0.05,           # Format and readability
    'errors': 0.05,           # Errors and consistency
}
```

## Limitations

- Requires valid API keys for OpenAI or Groq
- Analysis quality depends on the LLM model used
- HTML report generation requires matplotlib
- PDF parsing may not be perfect for all resume formats
