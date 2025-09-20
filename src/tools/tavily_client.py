from tavily import TavilyClient

tavily_client = TavilyClient(api_key="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")

def tavily_chat(query: str, max_results=1) -> str:
    result = tavily_client.search(query, max_results=max_results)
    obs_list = []
    print(len(query))
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