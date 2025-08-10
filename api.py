import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from models import User
from claude_code_sdk.types import TextBlock, ToolUseBlock, ToolResultBlock
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Claude Code SDK API", description="API wrapper for Claude Code SDK")

GITHUB_MCP_PAT = os.getenv("GITHUB_MCP_PAT")

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

class UserCreateRequest(BaseModel):
    name: str
    email: str
    address: str = None

async def execute_claude_query(query: str) -> str:
    """Execute a query using Claude Code SDK and return the response"""
    response_text = []
    
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a performance engineer",
            allowed_tools=["Bash", "Read", "WebSearch", "mcp__github"],
            max_turns=50,
            cwd=Path(__file__).parent,
            add_dirs=[Path(__file__).parent],
            permission_mode="bypassPermissions",
            mcp_servers=mcp_servers,
        )
    ) as client:
        await client.query(query)
        
        async for message in client.receive_response():
            content = getattr(message, "content", [])
            for block in content:
                if isinstance(block, TextBlock) and getattr(block, "text", None):
                    response_text.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    name = getattr(block, "name", "")
                    tool_input = getattr(block, "input", {})
                    response_text.append(f"\n[tool_use] {name} {tool_input}\n")
                elif isinstance(block, ToolResultBlock):
                    result = getattr(block, "content", None)
                    if result is not None:
                        response_text.append(str(result))
    
    return "".join(response_text)

# In-memory storage for demo purposes
users_db = {}
next_user_id = 1

@app.post("/users", response_model=User)
async def create_user(user_request: UserCreateRequest):
    """Create a new user with address field"""
    global next_user_id
    user = User(
        id=next_user_id,
        name=user_request.name,
        email=user_request.email,
        address=user_request.address
    )
    users_db[next_user_id] = user
    next_user_id += 1
    return user

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a user by ID"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.put("/users/{user_id}/address")
async def update_user_address(user_id: int, address: str):
    """Update a user's address"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    users_db[user_id].address = address
    return {"message": "Address updated successfully", "user": users_db[user_id]}

@app.post("/execute")
async def execute_query(request: QueryRequest):
    """Execute a Claude Code SDK query"""
    logger.info(f"Received query: {request.query}")
    try:
        logger.info("Starting Claude SDK execution...")
        result = await execute_claude_query(request.query)
        logger.info("Claude SDK execution completed successfully")
        return {"success": True, "result": result}
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