import os
from typing import Dict
from openai import OpenAI
from langgraph.graph import StateGraph, END
from config import MODEL

class VectorDB:
    def search(self, query: str) -> str:
        # vector chunk 가져오기

        return f"Searched for {query} in VectorDB."

class WebSearchTool:
    def search(self, question: str) -> str:
        # Google search, 덕덕고(?) 서치 툴을 추가해서 서치 정보 가져오기
        return f"Searched for {question} on the web."

class ModifyTool:
    def modify(self, document: str) -> str:
        return f"Modified document: {document}"

class SuggestionAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_db = VectorDB()
        self.web_search_tool = WebSearchTool()
        self.modify_tool = ModifyTool()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(Dict)
        graph.add_node("JD 검색", self.search_related_jd)
        graph.add_node("최신 정보 검색", self.search_latest_info)
        graph.add_node("문서 수정", self.modify_document)

        # 순서대로 아닐수도 있음
        graph.add_edge("JD 검색", "최신 정보 검색")
        graph.add_edge("최신 정보 검색", "문서 수정")
        graph.add_edge("문서 수정", END)
        graph.set_entry_point("JD 검색")
        return graph.compile()

    def search_related_jd(self, state: Dict) -> Dict:
        query = state.get("query", "job description")
        result = self.vector_db.search(query)
        return {"jd_info": result}

    def search_latest_info(self, state: Dict) -> Dict:
        question = state.get("question", "latest trends")
        result = self.web_search_tool.search(question)
        return {**state, "latest_info": result}

    def modify_document(self, state: Dict) -> Dict:
        document = state.get("document", "")
        result = self.modify_tool.modify(document)
        return {**state, "modified_doc": result}

    def run(self, document: str) -> Dict:
        initial_state = {"document": document}
        result = self.graph.invoke(initial_state)
        return result
