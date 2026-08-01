import asyncio
import sys
import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ga4_mcp.server"],
        env={
            **os.environ,
            "GOOGLE_APPLICATION_CREDENTIALS": "/dummy/path/to/credentials.json",
            "GA4_PROPERTY_ID": "123456789"
        }
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                print("Initializing session...")
                await session.initialize()
                print("Sending tools/list request...")
                
                result = await session.list_tools()
                tool_names = [tool.name for tool in result.tools]
                print(f"Success! Received {len(tool_names)} tools: {', '.join(tool_names)}")
                print("Test passed. The server correctly responded to a stateless tools/list request.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
