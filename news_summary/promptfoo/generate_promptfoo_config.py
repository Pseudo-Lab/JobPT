import yaml
import json
import pandas as pd

# 데이터 로드 (예: CSV 파일로부터 읽기)
file_path = "news_data.csv"  # CSV 파일 경로
data = pd.read_csv(file_path)

# 데이터 병합: company_name을 기준으로 병합
merged_data = (
    data.groupby("company_name")
    .agg(
        {
            "published_date": lambda x: ", ".join(x),
            "title": lambda x: "\n".join(x),
            "description": lambda x: "\n---\n".join(x),
            "url": lambda x: ", ".join(x),
            "origin": lambda x: ", ".join(x),
        }
    )
    .reset_index()
)


def load_text_from_file(file_path):
    """단일 텍스트 파일에서 내용을 읽어 반환합니다."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().strip()
    return content


def load_test_data_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


base_path = "prompts/"
# prompt_files = ["v5.txt", "v7.txt"]
prompt_files = ["final.txt"]

# 프롬프트 파일들을 불러와서 리스트에 추가
prompts = []
for file_path in prompt_files:
    prompt_content = load_text_from_file(base_path + file_path)
    prompts.append(prompt_content)


# 테스트 케이스용 텍스트 파일 경로 설정
# test_data = load_test_data_from_json("answer.json")

# 테스트 케이스 생성
tests = []
for idx, description in enumerate(merged_data["description"]):
    print(description)
    user_text = description
    test_case = {
        "vars": {"text": user_text},
        "assert": [
            # Chat GPT API 필요
            {
                "type": "llm-rubric",
                "value": f"Ensure the [article] captures the main ideas accurately and concisely.\n [article]\n{user_text}",
                "provider": "openai:gpt-4o-mini",
            },
            # {"type": "rouge-n", "value": assistant_text, "threshold": 0.4},
        ],
    }
    tests.append(test_case)

providers = ["file://inference.py:generate_text_qwen_templow"]
# providers = ["file://inference.py:generate_text_qwen", "file://inference.py:generate_text_qwen_templow"]
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
