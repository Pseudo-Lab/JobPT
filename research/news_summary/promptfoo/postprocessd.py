import json

# JSON 파일 경로
file_path = "answer.json"

try:
    # JSON 데이터 로드
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 중복 제거 처리
    seen_ids = set()
    unique_data = []

    for entry in data:
        if entry["article_id"] not in seen_ids:
            unique_data.append(entry)
            seen_ids.add(entry["article_id"])

    # 결과를 동일한 파일에 저장
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(unique_data, file, ensure_ascii=False, indent=4)

    print(f"중복 제거 완료. 결과는 '{file_path}'에 저장되었습니다.")

except FileNotFoundError:
    print(f"파일 '{file_path}'이(가) 존재하지 않습니다. 경로를 확인하세요.")
except json.JSONDecodeError:
    print(f"'{file_path}' 파일이 올바른 JSON 형식이 아닙니다.")
except Exception as e:
    print(f"오류 발생: {e}")
