import yaml
import json


def load_text_from_file(file_path):
    """단일 텍스트 파일에서 내용을 읽어 반환합니다."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().strip()
    return content


def load_test_data_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


base_path = "prompts/"
prompt_files = ["v5.txt", "v7.txt"]

# 프롬프트 파일들을 불러와서 리스트에 추가
prompts = []
for file_path in prompt_files:
    prompt_content = load_text_from_file(base_path + file_path)
    prompts.append(prompt_content)


# 테스트 케이스용 텍스트 파일 경로 설정
test_data = load_test_data_from_json("answer.json")

# 테스트 케이스 생성
tests = []
for idx, item in enumerate(test_data):
    user_text = item["article"]
    assistant_text = item["summary"]
    test_case = {
        "vars": {"text": user_text},
        "assert": [
            # Chat GPT API 필요
            {"type": "llm-rubric", "value": f"Ensure the [article] captures the main ideas accurately and concisely.\n [article]\n{user_text}"},
            # {"type": "rouge-n", "value": assistant_text, "threshold": 0.4},
        ],
    }
    tests.append(test_case)
    if idx == 14:
        break

providers = ["file://inference.py:generate_text_qwen", "file://inference.py:generate_text_qwen_templow"]
# YAML 구성 설정
config = {
    "description": "News Summary Evaluation",
    "prompts": prompts,
    "providers": providers,
    # "defaultTest": {
    #     "options": {
    #         "provider": {
    #             "embedding": {
    #                 "id": "huggingface:sentence-similarity:sentence-transformers/all-MiniLM-L6-v2",
    #             }
    #         }
    #     }
    # },
    "tests": tests,
}

# YAML 파일로 저장
with open("promptfooconfig.yaml", "w", encoding="utf-8") as yaml_file:
    yaml.dump(config, yaml_file, allow_unicode=True, default_flow_style=False)

print("promptfooconfig.yaml 파일이 생성되었습니다.")
