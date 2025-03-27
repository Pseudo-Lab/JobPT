from langchain_core.runnables.graph import Graph, Node, Edge, MermaidDrawMethod
from IPython.display import Image, display

# Define nodes with proper metadata
nodes = {
    # Suggestion Agent Nodes
    "JD 검색": Node(
        id="JD 검색", 
        name="JD 검색", 
        data={"description": "Job Description 관련 정보를 검색"}, 
        metadata={"type": "process"}
    ),
    "최신 정보 검색": Node(
        id="최신 정보 검색", 
        name="최신 정보 검색", 
        data={"description": "최신 트렌드 정보를 검색"}, 
        metadata={"type": "process"}
    ),
    "문서 수정": Node(
        id="문서 수정", 
        name="문서 수정", 
        data={"description": "문서를 수정"}, 
        metadata={"type": "process"}
    ),
    
    # Review LLM Nodes
    "문법 검사": Node(
        id="문법 검사", 
        name="문법 검사", 
        data={"description": "문법 오류를 검사"}, 
        metadata={"type": "review"}
    ),
    "ATS 분석": Node(
        id="ATS 분석", 
        name="ATS 분석", 
        data={"description": "ATS 최적화 분석"}, 
        metadata={"type": "review"}
    ),
    "JD 리포트": Node(
        id="JD 리포트", 
        name="JD 리포트", 
        data={"description": "JD 요구사항 리포트 제공"}, 
        metadata={"type": "review"}
    ),
}

# Define edges to correctly represent the multi-turn flow
edges = [
    # Suggestion Agent Flow
    Edge(source="JD 검색", target="최신 정보 검색", data={"description": "JD 검색 후 최신 정보 검색"}),
    Edge(source="최신 정보 검색", target="문서 수정", data={"description": "최신 정보 반영하여 문서 수정"}),
    
    # Connection between Suggestion Agent and Review LLM
    Edge(source="문서 수정", target="문법 검사", data={"description": "수정된 문서를 검토 LLM에 전달"}),
    
    # Review LLM Flow
    Edge(source="문법 검사", target="ATS 분석", data={"description": "문법 검사 후 ATS 분석"}),
    Edge(source="ATS 분석", target="JD 리포트", data={"description": "ATS 분석 결과 리포트"}),
]

# Create the graph
def create_graph():
    # Graph 객체 생성
    app = Graph(nodes=nodes, edges=edges)
    
    # 그래프 시각화 (Jupyter Notebook에서 실행 시)
    try:
        return app.draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    except:
        return "Graph visualization created. Run in Jupyter notebook to see the visualization."

if __name__ == "__main__":
    # This will only work in a Jupyter environment
    result = create_graph()
    print("Graph created. Import and run create_graph() in your Jupyter notebook to visualize.")
