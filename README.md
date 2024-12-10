# JobPT

구직자의 이력서와 채용 공고를 매칭해주고, 채용 공고에 맞는 이력서를 검색하여 추천해주는 채용공고 매칭시스템

## 프로젝트 멤버

김민아, 김민우, 최재강

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
