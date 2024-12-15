import json

def remove_duplicates(input_file, output_file):
    # JSON 파일 읽기
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    seen_ids = set()  # 이미 본 article_id를 저장하는 집합
    filtered_data = []  # 중복을 제거한 데이터를 저장할 리스트
    
    # 중복되지 않는 데이터만 필터링
    for entry in data:
        if entry['article_id'] not in seen_ids:
            filtered_data.append(entry)
            seen_ids.add(entry['article_id'])
    
    # 결과를 output.json 파일로 저장
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(filtered_data, file, ensure_ascii=False, indent=4)

    print(f"{output_file}에 중복 제거된 데이터를 저장했습니다.")

# 파일 경로 예시
input_file = 'answer.json'
output_file = 'output.json'

# 함수 호출
remove_duplicates(input_file, output_file)