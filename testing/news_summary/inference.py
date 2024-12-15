import os
import time
import csv
import json

os.environ["CUDA_VISIBLE_DEVICES"] = "0, 1"

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedTokenizerFast,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer,
    set_seed,
    AdamW,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    TextStreamer,
    TextIteratorStreamer,
)

# from peft import PeftConfig, PeftModel
from threading import Thread

# from datasets import load_dataset

# base_model_name = "OrionStarAI/Orion-14B-LongChat"
# base_model_name = "OrionStarAI/Orion-14B-Chat"
# base_model_name = "Qwen/Qwen2-7B"
# base_model_name = "Qwen/Qwen2.5-7B-Instruct"
# base_model_name = "Qwen/Qwen-7B-Chat"

# base_model_name = "maywell/EEVE-Korean-Instruct-10.8B-v1.0-32k"
# base_model_name = "beomi/Llama-3-Open-Ko-8B"
# base_model_name = "google/gemma-7b-it"
# base_model_name = "google/gemma-2-9b"
# base_model_name = "upstage/SOLAR-10.7B-v1.0"
base_model_name = "meta-llama/Llama-3.2-3B-Instruct"
# base_model_name = "Qwen/Qwen2.5-3B-Instruct"
# base_model_name = "google/gemma-2-2b"
# base_model_name = "kurugai/Kurugai-EEVE-v1.0"

# base_model_name = "OrionStarAI/Orion-14B-Chat"
# adapter_model_name = "/opt/models/summary_625_2_1_30_1e4_8_8/checkpoint-15180"
# /opt/models/sim_pairs_422_2_1_10_1e4_8_8/checkpoint-5030

bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quany=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
# bnb_config = BitsAndBytesConfig(load_in_8bit=True)

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    cache_dir="/opt/models/",
    trust_remote_code=True,
    torch_dtype=torch.float16,
    # quantization_config=bnb_config,
    device_map="cuda:0",
)
# model = PeftModel.from_pretrained(model, adapter_model_name)

tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True, cache_dir="/opt/models/")

# system = "다음 문서를 명사형 종결로 Markdown 형식으로 요약해 주세요. 주요 정보는 계층 구조로 작성하고, 각 항목은 불렛 포인트로 나열해 주세요. 모든 항목은 반드시 명사로 끝나거나 음슴체로 끝나게 해주세요."


def generate_response(input):
    streamer = TextStreamer(tokenizer)
    input_ids = tokenizer.encode(input, return_tensors="pt").to(model.device)

    terminators = tokenizer.encode("<|eot_id|>", add_special_tokens=False)[0]
    outputs = model.generate(
        input_ids, pad_token_id=tokenizer.eos_token_id, max_new_tokens=1024, streamer=streamer, eos_token_id=terminators, repetition_penalty=1.05
    )
    response = outputs[0]
    return tokenizer.decode(response, skip_special_tokens=True)


# 개조식, 핵심, 상세 순

prompts = [
    f"""
Summarize the following [document] in English.
Summarize as simple and concisely as possible.
Don't generate token after <|eot_id|>.
If you don't follow the [Termination Rule], you'll be fined $50,000.
[Termination rule]
Do not participate in the conversation anymore or explain the previous content to people. Your Assistant will <|eot_id|> the response immediately after finishing the summary.

<example>
[Document]
Nick Scholfield is lined up to ride Spring Heeled in the Grand National at Aintree on April 11.\n\nNick Scholfield has been lined up to ride Jim Culloty’s Spring Heeled in the Crabbie’s Grand National at Aintree on Saturday week.\n\nScholfield had been expected to partner Paul Nicholls-trained Sam Winner, who was pulled up in the Cheltenham Gold Cup, in the £1million race.\n\nBut the champion trainer  said on Wednesday it was unfair to tie Scholfield down to a gelding which is far from certain to run when the mount on another leading definite contender is being offered.\n\nScholfield, who has ridden in six Nationals and finished third in 2013 on Teaforthree, will travel to Ireland to sit on Spring Heeled at Culloty’s County Cork stable on Friday.\n\nNicholls said: ‘I have not made up my mind if I am going to run Sam Winner yet and Nick needed a decision.\n\n‘I did not want to get into a situation next week when I had to say \"sorry mate, he is not running\" and did not want to stop him getting a good ride.\n\n‘I have not pressed any buttons on any of the horses who ran at Cheltenham. That will happen over the weekend and early next week. I don’t want to run unless I am really happy.\n\n‘I have plenty of other lads who could ride Sam Winner if he runs and would not be afraid to use Will Biddick or Harry Skelton.’\n\nSpring Heeled (right) wins the Fulke Walwyn Kim Muir Challenge Cup at Cheltenham last year.\n\nSpring Heeled, winner of Fulke Walwyn Kim Muir Challenge Cup at last season’s Cheltenham Festival, has been given a National preparation.\n\nThe eight-year-old has run only once since finishing fourth to Road To Riches in the Galway Plate in July when he was fourth of five in the Bobbyjo Chase at Fairyhouse in February.\n\nRacemail revealed on Wednesday that Culloty would have two runners in the National.\n\nRobbie McNamara will ride his 2014 Gold Cup winner Lord Windermere.\n\nScholfield rides Teaforthree (front) as the horse jumps the last fence at Aintree in the 2013 Grand National.\n\nMcNamara said: ‘It's a great ride to get and I'm looking forward to it. I've ridden him before in a Grade One in Leopardstown and I was supposed to ride him in the Hennessy there as well, but I broke my collarbone the day before. I'm delighted to get back on him.’\n\nWith Nigel Twiston-Davies-trained Double Ross another confirmed non runner, David Pipe’s well supported Soll appears guaranteed a run at the bottom of the weights.\n\nLuke Morris became the first jockey to ride 100 winners during an All Weather Flat racing season when a double at Chelmsford on Wednesday aboard Giantouch and Middle East Pearl carried him to 101 successes for the campaign.
[Assistant]
Nick Schofield is riding Spring Heeled in the Crabbie's Grand National on Saturday. Schofield was expected to ride Sam Winner. 
Says Schofield, I have plenty of other lads who could ride Sam Winner..." Spring Heeled has only run once since finishing fourth in the Galway Plate.<|eot_id|>
</example>
[Document]
""",
]


file_path = "answer.json"
output_path = f"{base_model_name.split('/')[1]}.csv"
print(output_path)
# model output (summarization 결과)
for idx, prompt in enumerate(prompts):
    with open(file_path, "r", encoding="utf-8") as file:
        inputs = json.load(file)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["article_id", "article", "answer", "prediction"]  # 컬럼 이름 설정
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # CSV 파일의 헤더 작성

        for i, input in enumerate(inputs):
            article_id = input["article_id"]
            article = input["article"]
            answer = input["summary"]
            prompt += "\n" + article + "\nAssistant:"

            output = generate_response(prompt)
            output = output.split("Assistant:")
            output = output[-1]
            start_time = time.time()

            writer.writerow({"article_id": article_id, "article": article, "answer": answer, "prediction": output})
            print(time.time() - start_time)

            if i == 5:
                break
