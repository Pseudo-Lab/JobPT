from configs import UPSTAGE_API_KEY
import requests

def run_parser(pdf_path):
    """
    Upstage API를 사용하여 PDF에서 텍스트를 추출합니다.
    """
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": open(pdf_path, "rb")}
    data = {
        "ocr": "force",
        "base64_encoding": "['table']",
        "model": "document-parse",
        "output_formats": "['markdown', 'text']"
    }

    response = requests.post(url, headers=headers, files=files, data=data)

    # ✅ 응답 검사
    try:
        response_data = response.json()
    except Exception as e:
        print(" JSON 파싱 실패:", e)
        print("응답 원문:", response.text)
        raise Exception("Upstage API 응답이 JSON 형식이 아닙니다")

    if response.status_code != 200:
        print("Upstage API 요청 실패")
        print("Status Code:", response.status_code)
        print("응답:", response_data)
        raise Exception("Upstage API 요청 실패")

    if 'elements' not in response_data:
        print("'elements' 키가 응답에 없음:", response_data)
        raise Exception("Upstage 응답에 elements 키 없음")

    coordinates = []
    contents = []

    for i in response_data['elements']:
        coordinates.append(i['coordinates'])
        contents.append(i['content'].get('markdown', ''))

    full_contents = response_data.get('content', {}).get('text', '')
    contents = "\n".join(contents)

    print(f"{pdf_path}에서 텍스트 추출 완료")
    return contents, coordinates, full_contents

