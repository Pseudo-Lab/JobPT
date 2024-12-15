# JobPT

## 서비스 개요

현대 사회에서 취업 준비는 반복적이고 시간 소모적인 과정으로, 구직자가 자신의 역량을 효과적으로 어필하지 못해 기회를 놓치는 경우가 많습니다. 이를 해결하기 위해, JobPT는 **직무 공고 필터링, 회사 정보 요약 제공, 이력서 분석 및 맞춤형 피드백** 기능을 갖춘 지능형 취업 지원 서비스를 제공합니다.

## 주요 기능
1.	**LLM 기반 개인 맞춤형 매칭**
    * JobPT는 구직자가 업로드한 이력서를 각 회사의 채용 공고와 의미론적 유사도를 기반으로 RAG를 활용해 적합한 회사를 추천합니다. 
2.	**회사 관련 정보 요약 제공**
    * 구직자가 원하는 회사 또는 추천된 JD의 회사와 관련된 최신 정보를 요약 제공해 줍니다. 
3.	**이력서 평가 및 개선 기능**
    * 구직자가 업로드한 이력서를 점수화하여 현재 상태를 진단합니다. 해당 점수는 기술 적합성, 핵심 역량 등 세부 항목으로 나뉘어 평가됩니다.
    * 점수화 이후, LLM의 분석 결과를 활용해 이력서를 개선합니다. 높은 점수를 받은 항목은 이력서에서 더욱 강조할 수 있도록 개선합니다. 반대로, 점수가 낮은 부분에 대해서는 부족한 역량이나 경험을 보완할 수 있는 내용을 제안합니다.
4.	**AI 기반 평가 및 개선의 유기적 연계**
    * JobPT는 평가-개선-재평가 프로세스를 통해 이력서를 반복적으로 최적화할 수 있습니다. JD의 주요 요구사항과 일치하지 않는 영역을 사용자와 상호작용하며 수정할 수 있으며 개선 후 점수를 업데이트하여 사용자가 즉각적인 피드백을 받을 수 있도록 제공합니다. 

## 시스템 전체 구조도

![pipeline](./assets/system_pipeline.png)

## DB 구조도

![vectordb](./assets/inserting_data.png)

## 서비스 데모 영상

-   https://www.youtube.com/watch?v=m6EhfmpShCg

## 시스템 구동 방법

OmniParser 폴더 압축 해제

-   system 폴더안에 사전 제공된 OmniParser_v1.zip 파일을 압축해제
-   반드시 OmniParser_v1 폴더명이여야 함

프로젝트 패키지 설치

```
pip install -r requirements.txt
```

OPENAI_API_KEY 등록

```
export OPENAI_API_KEY=<your_openai_key>
```

Chroma DB 세팅

```
cd system
python insert_chunks.py
```

API 실행

```
python system/main.py
```

Gradio 앱 실행

```
python gradioapp.py
```

API 호출 예시 (api_test.py 참조)

```
import requests

# POST 요청 함수
def send_post_request(resume_path):
    url = "http://localhost:8000/matching"  # 실제 API 엔드포인트로 변경하세요.
    data = {"resume_path": resume_path}

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # 상태 코드가 200번대가 아니면 예외 발생
        print("POST 요청 성공:", response.json())
    except requests.exceptions.RequestException as e:
        print("POST 요청 중 오류 발생:", e)


# 함수 호출 예시
send_post_request("data/joannadrummond-cv.pdf")
```
