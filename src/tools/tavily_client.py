from tavily import TavilyClient
from datetime import datetime
tavily_client = TavilyClient(api_key="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")

def tavily_chat(query: str, max_results=1) -> str:
    today = datetime.today()
    formatted_day = today.strftime("%Y년 %m월 %d일")
    f"""
    today = datetime.today()
    formatted_day = today.strftime("%Y년 %m월 %d일")
    [역할]
    서울 관광 가이드의 최신 내용을 검색할 수 있도록 서포트를 한다.
    응답을 할때 출처 url를 적도록 한다.
    행사를 확인할 때 현재 날짜가 지나지 않았는지 확인한다.
    오늘 날짜
    {formatted_day}
                                
    [질문]
    {query}
    """
    result = tavily_client.search(query, max_results=max_results)
    obs_list = []
    for r in result["results"]:
        obs_list.append(f"- {r['title']}: {r['content']} ({r['url']})")
    return "\n".join(obs_list)


def run_tavily_and_get_urls(query: str, max_results: int = 3):
    try:
        res = tavily_client.search(query, max_results=max_results)
        urls = [item["url"] for item in res.get("results", []) if "url" in item]
        return urls
    except Exception as e:
        print("[Tavily Error]", e)
        return []