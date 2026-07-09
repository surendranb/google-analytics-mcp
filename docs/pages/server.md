# server

## Function: `main`

Main entry point for the MCP server.

This function performs the following steps:
1. Validates required environment variables.
2. Fetches and caches the GA4 property schema (dimensions and metrics).
3. Registers the tools with the MCP server.
4. Starts the server and listens for requests.

