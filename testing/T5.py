import torch
from transformers import T5ForConditionalGeneration, AutoTokenizer

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
        output = model.generate(input_ids=token, max_length=max_new_tokens, num_return_sequences=1)
        summary_part = tokenizer.decode(output[0], skip_special_tokens=True)
        summary_parts.append(summary_part)

    # 작은 문장들의 요약을 합쳐서 전체 문장의 요약 생성
    full_summary = " ".join(summary_parts)
    return full_summary

# GPU 사용 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 경로는 모델 폴더가 설치된 경로로 설정해야 합니다.
path = ".\\t5-base-korean-summarize-LOGAN"
model = T5ForConditionalGeneration.from_pretrained(path)
tokenizer = AutoTokenizer.from_pretrained(path)

# 모델을 GPU로 이동
model.to(device)

# 입력값을 input.txt에서 불러오기
input_file_path = "input.txt"
with open(input_file_path, "r", encoding="utf-8") as input_file:
    input_text = input_file.read()

# 적절한 max_new_tokens 값 설정
# 여러 번 실험을 통해 적절한 값을 찾아보세요.
max_new_tokens = 2048 # 예시로 2048으로 설정

summary = generate_summary(input_text, model, tokenizer, max_new_tokens)

# 생성된 요약을 output.txt로 내보내기
output_file_path = "output.txt"
with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.write(summary)