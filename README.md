# JobPT

## 서비스 개요

현대 사회에서 취업 준비는 반복적이고 시간 소모적인 과정으로, 구직자가 자신의 역량을 효과적으로 어필하지 못해 기회를 놓치는 경우가 많습니다. 이를 해결하기 위해, **직무 공고 필터링, 회사 정보 요약 제공, 이력서 분석 및 맞춤형 피드백** 기능을 갖춘 지능형 취업 지원 서비스를 제공합니다.

## 서비스 소개

### 서비스 구조도

![pipeline](./assets/system_pipeline.png)

### 데이터베이스 구축

![vectordb](./assets/inserting_data.png)

## 서비스 데모 영상
- https://www.youtube.com/watch?v=m6EhfmpShCg

## 시스템 사용 방법

OmniParser 폴더 압축 해제

-   system 폴더안에 OmniParser_v1.zip 파일을 압축해제
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
