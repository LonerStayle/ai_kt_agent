import torch
import src.common.GlobalSetting as gl
import src.common.prompts as prompts
from src.common.LLMType import LLMType
# from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, TextIteratorStreamer
import threading
from ollama import Client

kt_base_name = "K-intelligence/Midm-2.0-Base-Instruct"
_tokenizer = None
_config = None
_model = None
client = Client(host="http://127.0.0.1:11434")



# def cache_model():
#     global _tokenizer, _config, _model
#     if _model is None:
        # _tokenizer = AutoTokenizer.from_pretrained(kt_base_name)
        # _config = GenerationConfig.from_pretrained(kt_base_name)
        # _model = AutoModelForCausalLM.from_pretrained(
        #     kt_base_name,
        #     dtype =  torch.bfloat16,
        #     trust_remote_code = True,
        #     device_map = gl.device
        # )
    

    
def send_prompt(question:str):
    messages = prompts.build_question_prompts(question,LLMType.KT_MINI)
    # input_ids = _mini_tokenizer.apply_chat_template(
    #     messages,
    #     tokenize=True,
    #     add_generation_prompt=True,
    #     return_tensors="pt"
    # )
    # inputs = _tokenizer(messages, return_tensors="pt").to(gl.device)
    # output = _model.generate(
    #     input_ids=inputs["input_ids"],
    #     attention_mask=inputs["attention_mask"],
    #     generation_config=_config,
    #     eos_token_id=_tokenizer.eos_token_id,
    #     max_new_tokens=128,
    #     do_sample=False,
    # )
    # 대화 요청
    
    for chunk in client.chat(
        model="kt-midm-base-q4",  # Ollama에 등록한 이름
        messages=messages,
        stream=True,
        options={
        "num_predict": 128  # 기본 512보다 줄여서 빠르게
        }
    ):         # chunk가 tuple로 오면 첫 번째 요소만 가져오기
        if isinstance(chunk, tuple):
            chunk = chunk[0]

        if "message" in chunk and "content" in chunk["message"]:
            print(chunk["message"]["content"], end="", flush=True)

    # print(_tokenizer.decode(output[0]))
    # streamer = TextIteratorStreamer(_tokenizer, skip_special_tokens=True)
    # inputs = _tokenizer(messages, return_tensors="pt").to(gl.device)

    # thread = threading.Thread(target=_model.generate, kwargs=dict(
    #     input_ids=inputs["input_ids"],
    #     attention_mask=inputs["attention_mask"],
    #     generation_config=_config,
    #     max_new_tokens=128,
    #     do_sample=False,
    #     streamer=streamer
    # ))
    # thread.start()
    # for new_text in streamer:
    #     print(new_text, end="", flush=True)


def main():
    # cache_model()
    send_prompt("hi hello my name jin sup lee lee!!!ra go!!")


if __name__ == "__main__":
    main()

