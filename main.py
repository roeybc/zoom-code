import asyncio
from pathlib import Path
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from claude_code_sdk.types import TextBlock, ToolUseBlock, ToolResultBlock
from dotenv import load_dotenv
import os

load_dotenv()

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

async def main():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a performance engineer",
            allowed_tools=["Bash", "Read", "WebSearch", "mcp__github"],
            max_turns=50,
            # Ensure tools can access the project files
            cwd=PROJECT_PATH,
            add_dirs=[PROJECT_PATH],
            # Avoid interactive permission prompts for tool calls
            permission_mode="bypassPermissions",
            mcp_servers=mcp_servers,
        )
    ) as client:
        # Ask Claude to explicitly use the Read tool on main.py first
        await client.query(
            "clone the repo zoom-hackathon-example, create a new branch, add an optional phone number to the user class, add an appropriate issue and pull request. Always return to main in the end of the run"
        )
        
        # Stream responses (text, tool use, and tool results)
        async for message in client.receive_response():
            content = getattr(message, "content", [])
            for block in content:
                if isinstance(block, TextBlock) and getattr(block, "text", None):
                    print(block.text, end="", flush=True)
                elif isinstance(block, ToolUseBlock):
                    name = getattr(block, "name", "")
                    tool_input = getattr(block, "input", {})
                    print(f"\n[tool_use] {name} {tool_input}\n", end="", flush=True)
                elif isinstance(block, ToolResultBlock):
                    result = getattr(block, "content", None)
                    if result is not None:
                        print(f"{result}", end="", flush=True)

# Run as script
if __name__ == "__main__":
    asyncio.run(main())