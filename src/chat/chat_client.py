import src.common.GlobalSetting as gl
from ollama import Client
from langchain_community.chat_models import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import initialize_agent, AgentType
from src.tools.tavily_client import tavily_client
from dotenv import load_dotenv
import os 
from openai import OpenAI

load_dotenv()

llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME
llm = ChatOllama(model="llama3", base_url="http://127.0.0.1:11434")


api_key = os.getenv("OPENAI_API_KEY")
gpt = OpenAI(api_key=api_key)



def run_tavily_and_get_urls(query: str, max_results: int = 3):
    try:
        res = tavily_client.search(query, max_results=max_results)
        urls = [item["url"] for item in res.get("results", []) if "url" in item]
        return urls
    except Exception as e:
        print("[Tavily Error]", e)
        return []


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

    assistant_text.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
    mem.add_assistant(assistant_text)


def tavily_chat(query: str, max_results=1) -> str:
    result = tavily_client.search(query, max_results=max_results)
    obs_list = []
    for r in result["results"]:
        obs_list.append(f"- {r['title']}: {r['content']} ({r['url']})")
    return "\n".join(obs_list)


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


def chat(mem, messages):
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

