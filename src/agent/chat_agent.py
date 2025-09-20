import src.common.GlobalSetting as gl
from ollama import Client
from langchain_community.chat_models import ChatOllama
from src.tools.tavily_client import run_tavily_and_get_urls, tavily_chat
from dotenv import load_dotenv
import os 
from openai import OpenAI
import json


load_dotenv()

llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME
llm = ChatOllama(model="llama3", base_url="http://127.0.0.1:11434")


api_key = os.getenv("OPENAI_API_KEY")
gpt = OpenAI(api_key=api_key)


def eng_chat(mem,user_text):
    temp_list = [
        {"role":"system",
         "content":"""
          [Required]  
          This time, you must answer in English only.  
          Do not include any Korean.
          """
         },
         {
             "role":"user",
             "content":user_text
         }
    ]
    chunks = []
    for chunk in llm_client.chat(
        model=model_name, messages=temp_list, stream=True, options={"num_predict": 1024}
    ):
        if isinstance(chunk, tuple):
            chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            piece = chunk["message"]["content"]

            chunks.append(piece)
            yield piece 
            
    assistant_text = "".join(chunks).strip()
    assistant_text.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
    mem.add_assistant(assistant_text)

def main_chat(mem, messages):
    user_text = messages[-1]["content"]
    chunks = []
    for chunk in llm_client.chat(
        model=model_name, messages=messages, stream=True, options={"num_predict": 1024}
    ):
        if isinstance(chunk, tuple):
            chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            piece = chunk["message"]["content"]

            chunks.append(piece)
            yield piece 
            

    assistant_text = "".join(chunks).strip()

    # 🔑 검색이 필요한 질문이면 Tavily 실행
    if any(
        keyword in user_text
        for keyword in [
            "검색",
            "맛집"
        ]
    ):
        urls = run_tavily_and_get_urls(user_text, max_results=1)
        if urls:
            obs_text = "\n\n🔎 참고할 수 있는 관련 링크:\n" + "\n".join(urls)
            assistant_text += obs_text
            yield obs_text  # URL도 스트리밍으로 이어 붙이기
    
    if any(
        keyword in user_text
        for keyword in [
            "케데헌",
            "케이팝데몬헌터스",
            "케이팝 데몬 헌터스",
            "굿즈",
            "goods",
            'merchandise'
            "상품",
            "products",
            "items",
            "기념품",
            "souvenir"
        ]
    ):
        goods_images = [
            "goods/dufy.png",
            "goods/hunt.png",
            "goods/sin.png",
            "goods/ts.png",
        ]
        
        yield "\n" + json.dumps({"type": "images", "content": goods_images}) + "\n" # chunk 단위로 보내지 않고 한줄로 보내도록 처리
    assistant_text = assistant_text.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
    mem.add_assistant(assistant_text)


# GPT Router: 툴 호출 여부 판단 ---
def routing_with_gpt(user_text: str) -> str:
    """
    GPT API를 사용해서 'chat' or 'search' 판단
    """
    system_prompt = """You are a router agent.
Decide if the user question needs real-world search (e.g. restaurants, locations, news).
Respond ONLY with one word: 'chat' or 'search'."""

    completion = gpt.chat.completions.create(
        model="gpt-4o-mini",  
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=2,
    )
    return completion.choices[0].message.content.strip().lower()


import re

def is_english_num_space(s: str) -> bool:
    return bool(re.fullmatch(r"[ -~]+", s))



def chat(mem, messages):
    user_text = messages[-1]["content"]
    if is_english_num_space(user_text):
        print("[Router Decision] ENG")
        for token in eng_chat(mem,user_text):
            yield token
        return 
    
    route = routing_with_gpt(user_text)
    print(f"[Router Decision] {route}")
    
    if route == "chat":
        for token in main_chat(mem, messages):
            yield token

    elif route == "search":
        obs_text = tavily_chat(user_text, max_results=1)
        messages.append({
            "role": "system",
            "content": f"🔎 Tavily 검색 결과:\n{obs_text}\n\n위 내용을 반영해서 답변을 보강하기\n답변에 절대<|system|>와 같은 이상한 단어 넣지 말기"
        })
        for token in main_chat(mem, messages):
            yield token

    else:
        # fallback: 그냥 chat
        for token in main_chat(mem, messages):
            yield token

