from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import StructuredTool
from dotenv import load_dotenv
load_dotenv()
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from urllib.parse import urlencode
import asyncio
base_url = "https://server.smithery.ai/@harimkang/mcp-korea-tourism-api/mcp"
params = {
    "api_key": "d94de5b0-3de2-4b06-934e-592e78870d6e",
    "profile": "usual-reindeer-MZSQQr"
}
url = f"{base_url}?{urlencode(params)}"


def mcp_tool_to_langchain(tool, session):
    async def _func(**kwargs):
        res = await session.call_tool(tool.name, kwargs)
        return "\n".join([c.text for c in res.content if c.text])
    return StructuredTool.from_function(
        func=_func,
        name=tool.name,
        description=tool.description or "MCP tool",
    )

async def main():
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()

            # MCP → LangChain 변환
            lc_tools = [mcp_tool_to_langchain(t, session) for t in tools_result.tools]

            # OpenAI LLM
            llm = ChatOpenAI(model="gpt-4o-mini")

            agent = initialize_agent(
                tools=lc_tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
            )

            # 자연어 → MCP 툴 자동 선택
            result = await agent.arun("남산타워 근처 관광지 추천해줘")
            print(result)

if __name__ == "__main__":
    asyncio.run(main())
