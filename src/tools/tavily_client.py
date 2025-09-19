from tavily import TavilyClient

tavily_client = TavilyClient(api_key="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")

def tavily_chat(query: str, max_results=1) -> str:
    safe_query = query[:399] # query가 400자 넘으면 오류나는 문제 예방
    result = tavily_client.search(safe_query, max_results=max_results)
    obs_list = []
    for r in result["results"]:
        obs_list.append(f"- {r['title']}: {r['content']} ({r['url']})")
    return "\n".join(obs_list)


def run_tavily_and_get_urls(query: str, max_results: int = 3):
    try:
        safe_query = query[:399] # query가 400자 넘으면 오류나는 문제 예방
        res = tavily_client.search(safe_query, max_results=max_results)
        urls = [item["url"] for item in res.get("results", []) if "url" in item]
        return urls
    except Exception as e:
        print("[Tavily Error]", e)
        return []