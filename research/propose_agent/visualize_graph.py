from langchain_core.runnables.graph import Graph, Node, Edge, MermaidDrawMethod
from IPython.display import Image, display

# 노드와 엣지 정의
nodes = {
    "JD 검색": Node(id="JD 검색", name="JD 검색", data={"key": "value"}, metadata={"key": "value"}),
    "최신 정보 검색": Node(id="최신 정보 검색", name="최신 정보 검색", data={"key": "value"}, metadata={"key": "value"}),
    "문서 수정": Node(id="문서 수정", name="문서 수정", data={"key": "value"}, metadata={"key": "value"}),
    "문법 검사": Node(id="문법 검사", name="문법 검사", data={"key": "value"}, metadata={"key": "value"}),
    "ATS 분석": Node(id="ATS 분석", name="ATS 분석", data={"key": "value"}, metadata={"key": "value"}),
    "JD 리포트": Node(id="JD 리포트", name="JD 리포트", data={"key": "value"}, metadata={"key": "value"})
}

edges = [
    Edge(source="JD 검색", target="최신 정보 검색"),
    Edge(source="최신 정보 검색", target="문서 수정"),
    Edge(source="문서 수정", target="문법 검사"),
    Edge(source="문법 검사", target="ATS 분석"),
    Edge(source="ATS 분석", target="JD 리포트")
]

# Graph 객체 생성
app = Graph(nodes=nodes, edges=edges)

# 그래프 시각화
display(
    Image(
        app.draw_mermaid_png(
            draw_method=MermaidDrawMethod.API,
        )
    )
)
