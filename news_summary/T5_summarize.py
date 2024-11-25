import json
import torch
from transformers import (
    AutoTokenizer,
    T5ForConditionalGeneration, 
    AutoModelForSeq2SeqLM
    )



def generate_summary(input_text, model, tokenizer, max_new_tokens):
    # 입력 문장을 문장 단위로 분할
    sentences = input_text.split("\n")
    num_sentences = len(sentences)
    summary_parts = []

    for i in range(0, num_sentences, max_new_tokens):
        part = " ".join(sentences[i : i + max_new_tokens])
        prefix = "summarize: " + part
        token = tokenizer.encode(prefix, return_tensors="pt", max_length=max_new_tokens, truncation=True)
        token = token.to(device)  # GPU 사용을 위해 토큰을 디바이스로 이동
        outputs = model.generate(input_ids=token, max_length=max_new_tokens)
        summary_part = tokenizer.decode(outputs[0], skip_special_tokens=True)
        summary_parts.append(summary_part)

    # 작은 문장들의 요약을 합쳐서 전체 문장의 요약 생성
    full_summary = " ".join(summary_parts)
    return full_summary

# GPU 사용 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 경로는 모델 폴더가 설치된 경로로 설정해야 합니다.
paths = [
    "google-t5/t5-base",
    "google-t5/t5-small",
    "google-t5/t5-3b",
    "google-t5/t5-large",
]
for path in paths:
# path = "t5-base"
    # model = T5ForConditionalGeneration.from_pretrained(path)
    # tokenizer = AutoTokenizer.from_pretrained(path)
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSeq2SeqLM.from_pretrained(path, cache_dir="/opt/models")

    # 모델을 GPU로 이동
    model.to(device)

    # JSON 데이터 로드
    input_file_path = "news_dataset.json"
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        articles = json.load(input_file)

    # 적절한 max_new_tokens 값 설정
    max_new_tokens = 2048 # 예시로 2048으로 설정

    # 요약 결과 저장할 리스트
    summarized_articles = []

    print(f"전체 데이터 개수: {len(articles)}")
    for index, article_data in enumerate(articles):
        print(f"{index}번째 요약 시작")
        article_id = article_data["article_id"]
        article_text = article_data["article"]

        # 요약 생성
        summary = generate_summary(article_text, model, tokenizer, max_new_tokens)
        
        # 새로운 JSON 형식으로 요약 결과 저장
        summarized_articles.append({
            "article_id": article_id,
            "article": article_text,
            "summary": summary
        })
        print(article_id)
        print(summary)
        print('-------------------------------------------------------------')

    # 생성된 요약을 JSON 파일로 내보내기
    output_file_path = f"{path}.json"
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(summarized_articles, output_file, ensure_ascii=False, indent=4)
