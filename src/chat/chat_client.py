import src.common.GlobalSetting as gl
from ollama import Client
from langchain_community.chat_models import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import initialize_agent, AgentType
from src.tools.tavily_client import tavily_client
from dotenv import load_dotenv

load_dotenv()

llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME
llm = ChatOllama(model="llama3", base_url="http://127.0.0.1:11434")
search_tool = TavilySearchResults(max_results=2)

# Function-style Agent (빠른 툴 처리)
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
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
    - Ollama로 스트리밍 답변
    - 필요하면 중간에 Tavily 검색 결과를 Observation처럼 붙여서 마무리
    """
    user_text = messages[-1]["content"]

    # 스트리밍 중간 결과 모으기
    chunks = []
    for chunk in llm_client.chat(
        model=model_name, messages=messages, stream=True, options={"num_predict": 1024}
    ):
        if isinstance(chunk, tuple):
            chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            piece = chunk["message"]["content"]
            piece = (
                piece.replace("<|system|>", "")
                .replace("<|user|>", "")
                .replace("<|assistant|>", "")
            )
            chunks.append(piece)
            yield piece  # 사용자에게 실시간 전송

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
        urls = run_tavily_and_get_urls(user_text, max_results=3)
        if urls:
            obs_text = "\n\n🔎 참고할 수 있는 관련 링크:\n" + "\n".join(urls)
            assistant_text += obs_text
            yield obs_text  # URL도 스트리밍으로 이어 붙이기

    # 메모리에 최종 답변 저장
    mem.add_assistant(assistant_text)
