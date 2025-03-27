from langchain_core.runnables.graph import Graph, Node, Edge, MermaidDrawMethod
from IPython.display import Image, display

# Define nodes with proper metadata for the integrated workflow
nodes = {
    # Suggestion Agent Process (First Turn)
    "Suggestion Process": Node(
        id="Suggestion Process", 
        name="Suggestion Process", 
        data={"description": "문서 개선 제안 프로세스"}, 
        metadata={"type": "process"}
    ),
    
    # Review LLM Process
    "Review Process": Node(
        id="Review Process", 
        name="Review Process", 
        data={"description": "문서 검토 프로세스"}, 
        metadata={"type": "review"}
    ),
    
    # Decision Node
    "Decision": Node(
        id="Decision", 
        name="Decision", 
        data={"description": "검토 완료 여부 결정"}, 
        metadata={"type": "decision"}
    ),
    
    # End Node
    "End": Node(
        id="End", 
        name="End", 
        data={"description": "프로세스 종료"}, 
        metadata={"type": "end"}
    ),
}

# Define edges to correctly represent the multi-turn flow
edges = [
    # Initial flow
    Edge(source="Suggestion Process", target="Review Process", 
         data={"description": "제안된 문서를 검토 프로세스로 전달"}),
    
    # Review to Decision
    Edge(source="Review Process", target="Decision", 
         data={"description": "검토 결과에 따라 결정"}),
    
    # Decision outcomes
    Edge(source="Decision", target="Suggestion Process", 
         data={"description": "추가 개선 필요 (피드백 제공)", "condition": "refine"}),
    Edge(source="Decision", target="End", 
         data={"description": "검토 완료", "condition": "complete"}),
]

# Create the graph
def create_integrated_graph():
    # Graph 객체 생성
    app = Graph(nodes=nodes, edges=edges)
    
    # 그래프 시각화 (Jupyter Notebook에서 실행 시)
    try:
        return app.draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    except:
        return "Graph visualization created. Run in Jupyter notebook to see the visualization."

# For detailed view, also create a graph showing the internal components
def create_detailed_graph():
    # Define detailed nodes
    detailed_nodes = {
        # Suggestion Agent Nodes
        "JD 검색": Node(
            id="JD 검색", 
            name="JD 검색", 
            data={"description": "Job Description 관련 정보를 검색"}, 
            metadata={"type": "suggestion"}
        ),
        "최신 정보 검색": Node(
            id="최신 정보 검색", 
            name="최신 정보 검색", 
            data={"description": "최신 트렌드 정보를 검색"}, 
            metadata={"type": "suggestion"}
        ),
        "문서 수정": Node(
            id="문서 수정", 
            name="문서 수정", 
            data={"description": "문서를 수정"}, 
            metadata={"type": "suggestion"}
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
        
        # Decision and End Nodes
        "검토 완료 여부": Node(
            id="검토 완료 여부", 
            name="검토 완료 여부", 
            data={"description": "검토 완료 여부 결정"}, 
            metadata={"type": "decision"}
        ),
        "종료": Node(
            id="종료", 
            name="종료", 
            data={"description": "프로세스 종료"}, 
            metadata={"type": "end"}
        ),
        "피드백 제공": Node(
            id="피드백 제공", 
            name="피드백 제공", 
            data={"description": "개선을 위한 피드백 제공"}, 
            metadata={"type": "feedback"}
        ),
    }
    
    # Define detailed edges
    detailed_edges = [
        # Suggestion Agent Flow
        Edge(source="JD 검색", target="최신 정보 검색", data={"description": "JD 검색 후 최신 정보 검색"}),
        Edge(source="최신 정보 검색", target="문서 수정", data={"description": "최신 정보 반영하여 문서 수정"}),
        
        # Connection to Review LLM
        Edge(source="문서 수정", target="문법 검사", data={"description": "수정된 문서를 검토 LLM에 전달"}),
        
        # Review LLM Flow
        Edge(source="문법 검사", target="ATS 분석", data={"description": "문법 검사 후 ATS 분석"}),
        Edge(source="ATS 분석", target="JD 리포트", data={"description": "ATS 분석 결과 리포트"}),
        Edge(source="JD 리포트", target="검토 완료 여부", data={"description": "검토 결과에 따라 결정"}),
        
        # Decision outcomes
        Edge(source="검토 완료 여부", target="종료", data={"description": "검토 완료", "condition": "complete"}),
        Edge(source="검토 완료 여부", target="피드백 제공", data={"description": "추가 개선 필요", "condition": "refine"}),
        
        # Feedback back to Suggestion Agent
        Edge(source="피드백 제공", target="JD 검색", data={"description": "피드백을 바탕으로 재검색 및 수정"}),
    ]
    
    # Create the detailed graph
    app = Graph(nodes=detailed_nodes, edges=detailed_edges)
    
    # 그래프 시각화 (Jupyter Notebook에서 실행 시)
    try:
        return app.draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    except:
        return "Detailed graph visualization created. Run in Jupyter notebook to see the visualization."

if __name__ == "__main__":
    # This will only work in a Jupyter environment
    print("Graph created. Import and run create_integrated_graph() or create_detailed_graph() in your Jupyter notebook to visualize.")
