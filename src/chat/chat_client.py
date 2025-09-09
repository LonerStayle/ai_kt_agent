import src.common.GlobalSetting as gl
from ollama import Client
from langchain_community.chat_models import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import initialize_agent, AgentType
import json
from src.tools.tavily_client import tavily_client
from dotenv import load_dotenv
load_dotenv()

llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME


llm = ChatOllama(
    model="llama3", 
    base_url="http://127.0.0.1:11434"
)

search_tool = TavilySearchResults(max_results=2)

# Function-style Agent (빠른 툴 처리)
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)



def run_tavily_and_get_urls(query: str, max_results: int = 3):
    try:
        res = tavily_client.search(query, max_results=max_results)
        urls = [item["url"] for item in res.get("results", []) if "url" in item]
        return urls
    except Exception as e:
        print("[Tavily Error]", e)
        return []

def stream_chat(mem, messages):
    """
    - 특정 키워드 포함 시 Tavily 실행 후 URL 포함 답변
    - 그 외에는 Ollama 스트리밍
    """
    user_text = messages[-1]["content"]

    # --- 키워드 기반 검색 분기 ---
    if any(keyword in user_text for keyword in ["검색", "맛집", "위치", "어디", "샵", "shop", "store", "restaurant", "news"]):
        urls = run_tavily_and_get_urls(user_text, max_results=3)

        if urls:
            # Tavily URL만 포함된 답변
            answer = "🔗 관련 정보를 아래 링크에서 확인할 수 있어요:\n" + "\n".join(urls)
        else:
            answer = "관련된 URL을 찾지 못했습니다. 😢"

        mem.add_assistant(answer)
        yield answer
        return

    # --- 일반 Ollama 스트리밍 ---
    chunks = []
    for chunk in llm_client.chat(
        model=model_name,
        messages=messages,
        stream=True,
        options={"num_predict": 128}
    ):
        if isinstance(chunk, tuple):
            chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            piece = chunk["message"]["content"]
            # 불필요한 태그 제거
            piece = piece.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
            chunks.append(piece)
            yield piece

    assistant_text = "".join(chunks).strip()
    mem.add_assistant(assistant_text)



# def stream_chat(mem, messages):
#     """
#     - 툴 필요 없는 경우: Ollama로 바로 스트리밍
#     - 툴 필요할 수 있는 경우: run_with_tools 호출
#     """
#     user_text = messages[-1]["content"]

#     # 간단한 분기 (툴 트리거 키워드 예시)
#     if any(keyword in user_text for keyword in ["검색", "맛집", "뉴스", "search", "restaurant", "news"]):
#         answer = run_with_tools(user_text)
#         mem.add_assistant(answer)
#         yield answer
#         return

#     # 일반 대화 → Ollama 스트리밍
#     chunks = []
#     for chunk in llm_client.chat(
#         model=model_name,
#         messages=messages,
#         stream=True,
#         options={"num_predict": 128}
#     ):
#         if isinstance(chunk, tuple):
#             chunk = chunk[0]
#         if "message" in chunk and "content" in chunk["message"]:
#             piece = chunk["message"]["content"]
#             piece = piece.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
#             chunks.append(piece)
#             yield piece

#     assistant_text = "".join(chunks).strip()
#     mem.add_assistant(assistant_text)

# def stream_chat(mem, messages):
#     chunks = []
#     for chunk in llm_client.chat(
#         model=model_name,
#         messages=messages,
#         stream=True,
#         options={"num_predict": 128}
#     ):
#         if isinstance(chunk, tuple): chunk = chunk[0]
#         if "message" in chunk and "content" in chunk["message"]:
#             piece = chunk["message"]["content"]

#             # 올라마는 기본적으로 <|system|> 를 붙이려는 성격이 있음 강제 제거 
#             piece = piece.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
#             chunks.append(piece)
#             yield piece


#     # 캐싱: 스트리밍 끝나고만 Redis에 최종 답변 저장
#     assistant_text = "".join(chunks).strip()
#     assistant_text = assistant_text.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
#     mem.add_assistant(assistant_text)
