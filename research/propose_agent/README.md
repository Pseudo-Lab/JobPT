# 간단한 LangGraph 에이전트

LangGraph를 활용한 간단한 문서 분석 및 개선 제안 에이전트입니다.

## 기능

- 문서 분석: 입력된 문서의 주요 내용을 분석합니다.
- 개선 제안: 문서 개선을 위한 구체적인 제안을 생성합니다.
- 제안 평가: 생성된 제안의 품질과 적용 가능성을 평가합니다.

## 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

1. `.env` 파일에 OpenAI API 키를 설정합니다:

```
OPENAI_API_KEY=your_api_key_here
```

2. 예제 실행:

```bash
python simple_example.py
```

## 코드 구조

- `modules/simple_agent.py`: LangGraph 기반 에이전트 구현
- `simple_example.py`: 에이전트 사용 예제

## 상태 그래프

```
[분석] -> [제안] -> [평가] -> [종료]
