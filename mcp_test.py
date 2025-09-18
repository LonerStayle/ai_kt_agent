from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv
import os
load_dotenv()

mcp = os.getenv("MCP_KEY")
profile = os.getenv("MCP_PROFILE")
# Construct server URL with authentication

from urllib.parse import urlencode
base_url = "https://server.smithery.ai/@harimkang/mcp-korea-tourism-api/mcp"
params = {
    "api_key": "d94de5b0-3de2-4b06-934e-592e78870d6e",
    "profile": "language=ko;"
}
url = f"{base_url}?{urlencode(params)}"


async def main():
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            for tool in tools_result:
                print(tool)        
            print(f"Available tools: {', '.join([t.name for t in tools_result.tools])}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())