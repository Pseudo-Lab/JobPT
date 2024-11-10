import os
import torch
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
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir="/opt/models/",
            trust_remote_code=True,
            torch_dtype=torch.float16,
            quantization_config=bnb_config,
            device_map="auto"
        )
    else:
        # Llama 모델이나 양자화가 필요 없는 경우
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir="/opt/models/",
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, cache_dir="/opt/models/")
    return model, tokenizer

# Qwen 모델 프롬프트 생성 함수
def generate_text_qwen(prompt: str, max_tokens=2048, *args, **kwargs):
    model, tokenizer = load_model_and_tokenizer("Qwen/Qwen2.5-7B-Instruct")
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    terminators = tokenizer.encode("<|eot_id|>", add_special_tokens=False)[0]
    outputs = model.generate(
        input_ids, pad_token_id=tokenizer.eos_token_id, max_new_tokens=1024, eos_token_id=terminators, repetition_penalty=1.05
    )
    response = {
        "output":tokenizer.decode(outputs[0], skip_special_tokens=True)
    }
    return response

# Llama 모델 프롬프트 생성 함수 (양자화 적용 안 함)
def generate_text_llama(prompt: str, max_tokens=2048, *args, **kwargs):
    model, tokenizer = load_model_and_tokenizer("meta-llama/Llama-3.2-3B-Instruct", quantize=False)
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    terminators = tokenizer.encode("<|eot_id|>", add_special_tokens=False)[0]
    outputs = model.generate(
        input_ids, pad_token_id=tokenizer.eos_token_id, max_new_tokens=1024, eos_token_id=terminators, repetition_penalty=1.05
    )
    response = {
        "output":tokenizer.decode(outputs[0], skip_special_tokens=True)
    }
    return response

if __name__ == "__main__":
    result = generate_text_qwen("What is the capital of France?", max_tokens=50)
    print(result)  # {"output": "Paris"}