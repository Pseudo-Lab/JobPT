import os
from typing import Dict
from openai import OpenAI
from langgraph.graph import StateGraph, END
from config import MODEL

class ReviewLLM:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(Dict)
        graph.add_node("문법 검사", self.check_grammar)
        graph.add_node("ATS 분석", self.analyze_ats_optimization)
        graph.add_node("JD 리포트", self.provide_jd_report)
        graph.add_edge("문법 검사", "ATS 분석")
        graph.add_edge("ATS 분석", "JD 리포트")
        graph.add_edge("JD 리포트", END)
        graph.set_entry_point("문법 검사")
        return graph.compile()

    def check_grammar(self, state: Dict) -> Dict:
        # 문법 API 같은걸로 해보기
        document = state.get("document", "")
        result = "Grammar check completed."
        return {"grammar_report": result}

    def analyze_ats_optimization(self, state: Dict) -> Dict:

        document = state.get("document", "")
        result = "ATS optimization analysis completed."
        return {**state, "ats_analysis": result}

    def provide_jd_report(self, state: Dict) -> Dict:
        document = state.get("document", "")
        is_review_complete = self._evaluate_completion(document)
        result = "JD requirement report provided."
        if is_review_complete:
            result += " <finish>"
        return {**state, "jd_report": result}

    def _evaluate_completion(self, document: str) -> bool:
        prompt = f"""
        Analyze the following document and determine if the review process is complete.
        Document: {document}
        
        Is the review complete? Answer with yes or no.
        """
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an assistant that helps determine if a document review is complete."},
                {"role": "user", "content": prompt},
            ],
        )
        response_text = response.choices[0].message.content.lower()
        return "yes" in response_text

    def run(self, document: str) -> Dict:
        initial_state = {"document": document}
        result = self.graph.invoke(initial_state)
        return result
