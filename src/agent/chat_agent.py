import src.common.GlobalSetting as gl
from ollama import Client
from langchain_community.chat_models import ChatOllama
from src.tools.tavily_client import run_tavily_and_get_urls, tavily_chat
from dotenv import load_dotenv
import os 
from openai import OpenAI
import json
import base64


load_dotenv()

llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME
llm = ChatOllama(model="llama3", base_url="http://127.0.0.1:11434")


api_key = os.getenv("OPENAI_API_KEY")
gpt = OpenAI(api_key=api_key)



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
            "맛집",
            "위치",
            "어디",
            "샵",
            "shop",
            "store",
            "restaurant",
            "news",
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
        
    assistant_text.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
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


def chat(mem, messages, image):
    
    if image:
        print('exist image')
        # 이미지가 있는 경우 사용자 채팅 자체를 '{image_kind}가 뭐야로 바꿔서 믿음에 질의'
        image_name = infer_image_name(messages, image)
        messages = f'{image_name}에 대한 정보 알려줘'
        
    user_text = messages[-1]["content"]
    route = routing_with_gpt(user_text)
    print(f"[Router Decision] {route}")
    
    if route == "chat":
        for token in main_chat(mem, messages):
            yield token

    elif route == "search":
        obs_text = tavily_chat(user_text, max_results=2)
        messages.append({
            "role": "system",
            "content": f"🔎 Tavily 검색 결과:\n{obs_text}\n\n위 내용을 반영해서 답변을 보강하세요."
        })
        for token in main_chat(mem, messages):
            yield token

    else:
        # fallback: 그냥 chat
        for token in main_chat(mem, messages):
            yield token

def infer_image_name(user_text, image):
    
    messages = [
        {"role": "system", "content": "너는 한국적 이미지를 보면 장소/물건 이름을 정확하게 판단 할 수 있는 이미지 전문가야"},
        {"role": "user", "content": "응답은 간단하게 한 단어로 해줘 예를 들자면 다음과 같아 '요쿠르트 판매차', '경복궁, '남산'"}
    ]

    # 텍스트 추가
    messages[1]["content"].append({
        "type": "text",
        "text": user_text
    })

    # 이미지 추가
    if image is not None:
        base64_image = base64.b64encode(image.read()).decode("utf-8")
        
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        })

    # LLM 호출
    response = gpt.chat.completions.create(
        model="gpt-5",
        messages=messages,
        temperature=0.0,
    )

    return response.choices[0].message["content"]