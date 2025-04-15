import os
import json
from typing import Dict, List, Any, Optional

class SimulatedSearchTool:
    """
    시뮬레이션된 검색 결과를 제공하는 도구
    """
    def __init__(self):
        print("검색 도구 초기화 (시뮬레이션 모드)")
    
    def search(self, query: str) -> List[Dict]:
        """
        시뮬레이션된 검색 결과 반환
        
        Args:
            query: 검색 쿼리
            
        Returns:
            검색 결과 목록 (제목, 내용, URL 포함)
        """
        print(f"검색 쿼리: {query}")
        
        # 시뮬레이션된 검색 결과
        return [
            {
                "title": f"'{query}'에 관한 최신 트렌드",
                "snippet": f"{query}에 관한 최신 정보와 트렌드입니다. 이 분야는 최근 급속도로 발전하고 있습니다.",
                "url": "https://example.com/trends",
            },
            {
                "title": f"{query} 관련 직무 요구사항",
                "snippet": f"{query} 관련 직무에서는 최신 기술과 도구에 대한 이해가 필요합니다.",
                "url": "https://example.com/job-requirements",
            },
            {
                "title": f"{query}에 대한 전문가 의견",
                "snippet": f"전문가들은 {query}에 대해 다양한 의견을 제시합니다. 주요 관점은...",
                "url": "https://example.com/expert-opinions",
            },
        ]

def format_results(results: Dict) -> str:
    """
    결과를 읽기 쉬운 형식으로 변환
    
    Args:
        results: 결과 딕셔너리
        
    Returns:
        형식화된 결과 문자열
    """
    formatted = "===== 결과 요약 =====\n\n"
    
    # 분석 결과
    if "analysis" in results:
        formatted += "📊 분석 결과:\n"
        analysis = results["analysis"]
        for key, value in analysis.items():
            formatted += f"  - {key}: {value}\n"
        formatted += "\n"
    
    # 제안 사항
    if "suggestions" in results:
        formatted += "💡 개선 제안:\n"
        for i, suggestion in enumerate(results["suggestions"], 1):
            formatted += f"  {i}. {suggestion}\n"
        formatted += "\n"
    
    # 평가
    if "evaluation" in results:
        formatted += "⭐ 평가:\n"
        evaluation = results["evaluation"]
        for key, value in evaluation.items():
            formatted += f"  - {key}: {value}\n"
    
    return formatted

def save_results(results: Dict, filename: str = "results.json") -> None:
    """
    결과를 JSON 파일로 저장
    
    Args:
        results: 저장할 결과 딕셔너리
        filename: 저장할 파일 이름
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"결과가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"결과 저장 중 오류 발생: {str(e)}")

# 테스트 코드
if __name__ == "__main__":
    # 검색 도구 테스트
    search_tool = SimulatedSearchTool()
    results = search_tool.search("AI 개발자")
    
    print("\n===== 검색 결과 =====")
    for i, result in enumerate(results, 1):
        print(f"\n결과 {i}:")
        print(f"제목: {result.get('title', 'N/A')}")
        print(f"내용: {result.get('snippet', 'N/A')}")
        print(f"URL: {result.get('url', 'N/A')}")
    
    # 결과 형식화 테스트
    test_results = {
        "analysis": {"word_count": 150, "topic": "이력서"},
        "suggestions": ["경험 강조", "기술 스택 추가"],
        "evaluation": {"quality": "높음", "relevance": "관련성 높음"}
    }
    
    formatted = format_results(test_results)
    print("\n" + formatted)
    
    # 결과 저장 테스트
    save_results(test_results, "test_results.json")
