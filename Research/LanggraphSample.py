from langgraph.graph import StateGraph
from typing import Dict, TypedDict
from transformers import pipeline

# Hugging Face Pipeline 초기화
generator = pipeline("text-generation", model="distilgpt2")

# 상태 타입 정의
class State(TypedDict):
    text: str
    response: str

# 노드 함수 정의
def input_node(state: State) -> Dict:
    # 상태 업데이트
    state = state.copy()  # 상태 복사
    state["text"] = "Artificial Intelligence is transforming industries by automating tasks and enabling new possibilities."
    return state

def llm_node(state: State) -> Dict:
    # 상태 업데이트
    state = state.copy()  # 상태 복사
    prompt = f"Summarize the following text: {state['text']}"
    response = generator(prompt, max_length=50, num_return_sequences=1)
    state["response"] = response[0]['generated_text']
    return state

def output_node(state: State) -> Dict:
    print("LangGraph Agent Response:", state["response"])
    return state


# 그래프 생성 후 시각화
workflow = StateGraph(State)

# 노드 추가
workflow.add_node("input", input_node)
workflow.add_node("llm", llm_node)
workflow.add_node("output", output_node)

# 엣지 연결
workflow.set_entry_point("input")
workflow.add_edge("input", "llm")
workflow.add_edge("llm", "output")

# 그래프를 실행 가능한 함수로 컴파일
chain = workflow.compile()

# 초기 상태 설정과 함께 실행
initial_state = {
    "text": "",  # 빈 문자열로 초기화
    "response": ""  # 빈 문자열로 초기화
}

if __name__ == "__main__":
    # 실행
    chain.invoke(initial_state)