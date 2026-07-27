import asyncio
import sys
import os
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters

async def main():
    # In CI, we use the current python interpreter to run the installed ga4_mcp module
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "ga4_mcp"],
        env=os.environ.copy()
    )
    
    print("Starting MCP Server via stdio for integration testing...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("Initializing session...")
                await session.initialize()
                print("Session initialized successfully!")
                
                print("Fetching tools...")
                tools_response = await session.list_tools()
                
                print("\n✅ MCP Server is healthy and responding to protocol messages.")
                print(f"Discovered {len(tools_response.tools)} tools:")
                for tool in tools_response.tools:
                    print(f" - {tool.name}")
                    
                # Basic validation: ensure we have tools
                if len(tools_response.tools) == 0:
                    print("❌ Error: Server returned 0 tools.")
                    sys.exit(1)
                    
    except Exception as e:
        print(f"\n❌ MCP Server failed to start or communicate: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
