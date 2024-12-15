import os
import torch
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig

# GPU 설정
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"


def load_model_and_tokenizer(model_name, quantize=True):
    """
    모델과 토크나이저를 로드합니다.
    :param model_name: Hugging Face 모델 이름
    :param quantize: 양자화 사용 여부
    """
    if quantize and model_name != "meta-llama/Llama-3.2-3B-Instruct":
        # 양자화 설정
        bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, cache_dir="/opt/models/", trust_remote_code=True, torch_dtype=torch.float16, quantization_config=bnb_config, device_map="auto"
        )
    else:
        # Llama 모델이나 양자화가 필요 없는 경우
        model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir="/opt/models/", trust_remote_code=True, torch_dtype=torch.float16, device_map="auto")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, cache_dir="/opt/models/")
    return model, tokenizer


# Qwen 모델 프롬프트 생성 함수
def generate_text_qwen(prompt: str, max_tokens=2048, *args, **kwargs):
    model, tokenizer = load_model_and_tokenizer("Qwen/Qwen2.5-7B-Instruct")
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(input_ids, pad_token_id=tokenizer.eos_token_id, max_new_tokens=1024, repetition_penalty=1.05)
    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    output = output.split("Results:")[1].split('"Denser_Summary":')[-1].split("}")[0].split("]")[0]
    response = {"output": output}
    return response


# Qwen 모델 프롬프트 생성 함수
def generate_text_qwen_templow(prompt: str, max_tokens=2048, *args, **kwargs):
    model, tokenizer = load_model_and_tokenizer("Qwen/Qwen2.5-7B-Instruct")
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(input_ids, pad_token_id=tokenizer.eos_token_id, max_new_tokens=1024, repetition_penalty=1.05, temperature=0.4)
    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    output = output.split("Results:")[1].split('"Denser_Summary":')[-1].split("}")[0].split("]")[0]
    response = {"output": output}
    return response


# Llama 모델 프롬프트 생성 함수 (양자화 적용 안 함)
def generate_text_llama(prompt: str, max_tokens=2048, *args, **kwargs):
    model, tokenizer = load_model_and_tokenizer("meta-llama/Llama-3.2-3B-Instruct", quantize=False)
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(input_ids, pad_token_id=tokenizer.eos_token_id, max_new_tokens=1024, repetition_penalty=1.05)
    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    output = output.split("Results:")[1].split('"Denser_Summary":')[-1].split("}")[0].split("]")[0]
    response = {"output": output}
    return response


def load_text_from_file(file_path):
    """단일 텍스트 파일에서 내용을 읽어 반환합니다."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read().strip()
    return content


if __name__ == "__main__":

    base_path = "prompts/"
    prompt_files = ["v5.txt"]

    # 프롬프트 파일들을 불러와서 리스트에 추가
    prompts = []
    for file_path in prompt_files:
        prompt_content = load_text_from_file(base_path + file_path)
        prompts.append(prompt_content)
    for prompt in prompts:
        result = generate_text_qwen(prompt)
        print(result)  # {"output": "Paris"}
