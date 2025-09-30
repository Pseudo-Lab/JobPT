import os
import sys

try:
    from ATS_agent.ats_analyzer import ATSAnalyzer
    from ATS_agent.config import CV_PATH, MODEL, ADVANCED, GENERATE_HTML, JD_TEXT
except (ModuleNotFoundError, ImportError) as e:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    from ats_analyzer import ATSAnalyzer
    from config import CV_PATH, MODEL, ADVANCED, GENERATE_HTML, JD_TEXT


def main():
    cv_path = CV_PATH
    model = MODEL
    advanced = ADVANCED
    generate_html = GENERATE_HTML

    # Job description
    jd_text = JD_TEXT

    if not os.path.exists(cv_path):
        print(f"Warning: Resume file '{cv_path}' not found.")
        print("Please provide a valid resume file path.")
        print("\nUsage: python main.py")
        print("Edit the cv_path variable in main.py to point to your resume file.")
        return

    try:
        print("Initializing ATS Analyzer...")
        analyzer = ATSAnalyzer(cv_path, jd_text, model=model)

        print("Starting analysis...")
        result = analyzer.run_full_analysis(advanced=advanced, generate_html=generate_html)

        if not generate_html:
            print(result)
        else:
            print(f"\n분석 완료! 보고서가 저장된 경로: {result}")
            print("웹 브라우저에서 HTML 파일을 열어 전체 보고서를 확인하세요.")

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()