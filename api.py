import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from claude_code_sdk.types import TextBlock, ToolUseBlock, ToolResultBlock
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Claude Code SDK API", description="API wrapper for Claude Code SDK")

GITHUB_MCP_PAT = os.getenv("GITHUB_MCP_PAT")
PROJECT_PATH = os.getenv("PROJECT_PATH")

mcp_servers = {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": f"Bearer {GITHUB_MCP_PAT}"
      }
    }
}

class QueryRequest(BaseModel):
    query: str

async def execute_claude_query(query: str) -> None:
    """Execute a query using Claude Code SDK and log the response"""
    logger.info(f"Executing query in background: {query}")
    
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a performance engineer. you're always working on the zoom-hackathon-example repo, whataver the user asks, always create an issue and a pull requst. Link the issue and the pull request. Always return to main in the end of the run. NEVER merge the pull request.",
            allowed_tools=["Bash", "Read", "WebSearch", "mcp__github"],
            max_turns=50,
            cwd=PROJECT_PATH,
            add_dirs=[PROJECT_PATH],
            permission_mode="bypassPermissions",
            mcp_servers=mcp_servers,
        )
    ) as client:
        await client.query(query)
        
        async for message in client.receive_response():
            content = getattr(message, "content", [])
            for block in content:
                if isinstance(block, TextBlock) and getattr(block, "text", None):
                    logger.info(block.text)
                elif isinstance(block, ToolUseBlock):
                    name = getattr(block, "name", "")
                    tool_input = getattr(block, "input", {})
                    logger.info(f"ToolUse: {name} with input {tool_input}")
                elif isinstance(block, ToolResultBlock):
                    result = getattr(block, "content", None)
                    if result is not None:
                        logger.info(f"ToolResult: {result}")
    
    logger.info(f"Background execution for query '{query}' finished.")

@app.post("/execute")
async def execute_query(request: QueryRequest):
    """Execute a Claude Code SDK query"""
    logger.info(f"Received query: {request.query}")
    try:
        logger.info("Starting Claude SDK execution...")
        asyncio.create_task(execute_claude_query(request.query))
        logger.info("Claude SDK execution enqueued successfully")
        return {"success": True, "message": "Query execution started in the background."}
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)