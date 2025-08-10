import asyncio
from pathlib import Path
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from claude_code_sdk.types import TextBlock, ToolUseBlock, ToolResultBlock
from dotenv import load_dotenv
import os

load_dotenv()

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

async def main():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a performance engineer",
            allowed_tools=["Bash", "Read", "WebSearch", "mcp__github"],
            max_turns=5,
            # Ensure tools can access the project files
            cwd=Path(__file__).parent,
            add_dirs=[Path(__file__).parent],
            # Avoid interactive permission prompts for tool calls
            permission_mode="bypassPermissions",
            mcp_servers=mcp_servers,
        )
    ) as client:
        # Ask Claude to explicitly use the Read tool on main.py first
        await client.query(
            "Create a new pull request with a main.py file with 'hello world!' on zoom-hackathon-example in github"
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