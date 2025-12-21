# 项目概览

## 项目定位
Mini-Agent 是以 CLI 为入口的单 Agent 运行时，负责加载配置、初始化工具、创建 Agent 并进入交互会话；同时提供 ACP 适配以支持编辑器/客户端集成。

## 核心能力（README 摘要）
README 明确列出了核心能力与定位，涵盖执行循环、记忆、上下文摘要、Skills、MCP 与日志。

```markdown
# File: README.md | Lines: 5-15 | Description: Project positioning and feature list
**Mini Agent** is a minimal yet professional demo project that showcases the best practices for building agents with the MiniMax M2 model. Leveraging an Anthropic-compatible API, it fully supports interleaved thinking to unlock M2's powerful reasoning capabilities for long, complex tasks.

This project comes packed with features designed for a robust and intelligent agent development experience:

*   ✅ **Full Agent Execution Loop**: A complete and reliable foundation with a basic toolset for file system and shell operations.
*   ✅ **Persistent Memory**: An active **Session Note Tool** ensures the agent retains key information across multiple sessions.
*   ✅ **Intelligent Context Management**: Automatically summarizes conversation history to handle contexts up to a configurable token limit, enabling infinitely long tasks.
*   ✅ **Claude Skills Integration**: Comes with 15 professional skills for documents, design, testing, and development.
*   ✅ **MCP Tool Integration**: Natively supports MCP for tools like knowledge graph access and web search.
*   ✅ **Comprehensive Logging**: Detailed logs for every request, response, and tool execution for easy debugging.
*   ✅ **Clean & Simple Design**: A beautiful CLI and a codebase that is easy to understand, making it the perfect starting point for building advanced agents.
```

关键结论：
- README 将“执行循环/记忆/摘要/Skills/MCP/日志”作为核心卖点，与代码中对应模块一一匹配。
- “interleaved thinking” 出现在 README 中，侧重于 M2 能力展示而非代码实现细节。

## 使用示例（README 摘要）
README 提供了 3 个场景示例，覆盖“基础任务执行 / Skills / MCP”。

```markdown
# File: README.md | Lines: 239-258 | Description: Usage examples section
## Usage Examples

Here are a few examples of what Mini Agent can do.

### Task Execution

*In this demo, the agent is asked to create a simple, beautiful webpage and display it in the browser, showcasing the basic tool-use loop.*

### Using a Claude Skill (e.g., PDF Generation)

*Here, the agent leverages a Claude Skill to create a professional document (like a PDF or DOCX) based on the user's request, demonstrating its advanced capabilities.*

### Web Search & Summarization (MCP Tool)

*This demo shows the agent using its web search tool to find up-to-date information online and summarize it for the user.*
```

```python
# File: mini_agent/cli.py | Lines: 300-321 | Description: Workspace tools initialization
def add_workspace_tools(tools: List[Tool], config: Config, workspace_dir: Path):
    """Add workspace-dependent tools

    These tools need to know the workspace directory.

    Args:
        tools: Existing tools list to add to
        config: Configuration object
        workspace_dir: Workspace directory path
    """
    # Ensure workspace directory exists
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # File tools - need workspace to resolve relative paths
    if config.tools.enable_file_tools:
        tools.extend(
            [
                ReadTool(workspace_dir=str(workspace_dir)),
                WriteTool(workspace_dir=str(workspace_dir)),
                EditTool(workspace_dir=str(workspace_dir)),
            ]
        )
        print(f"{Colors.GREEN}✅ Loaded file operation tools (workspace: {workspace_dir}){Colors.RESET}")

    # Session note tool - needs workspace to store memory file
    if config.tools.enable_note:
        tools.append(SessionNoteTool(memory_file=str(workspace_dir / ".agent_memory.json")))
        print(f"{Colors.GREEN}✅ Loaded session note tool{Colors.RESET}")
```

```python
# File: mini_agent/acp/__init__.py | Lines: 95-104 | Description: ACP session creates Agent
async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
    session_id = f"sess-{len(self._sessions)}-{uuid4().hex[:8]}"
    workspace = Path(params.cwd or self._config.agent.workspace_dir).expanduser()
    if not workspace.is_absolute():
        workspace = workspace.resolve()
    tools = list(self._base_tools)
    add_workspace_tools(tools, self._config, workspace)
    agent = Agent(llm_client=self._llm, system_prompt=self._system_prompt, tools=tools, max_steps=self._config.agent.max_steps, workspace_dir=str(workspace))
    self._sessions[session_id] = SessionState(agent=agent)
    return NewSessionResponse(sessionId=session_id)
```

## 技术栈与依赖声明

### 依赖声明（pyproject.toml）
```toml
# File: pyproject.toml | Lines: 11-24 | Description: Declared dependencies
dependencies = [
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
    "httpx>=0.27.0",
    "mcp>=1.0.0",
    "pytest>=8.4.2",
    "requests>=2.31.0",
    "tiktoken>=0.5.0",
    "prompt-toolkit>=3.0.0",
    "pip>=25.3",
    "pipx>=1.8.0",
    "anthropic>=0.39.0",
    "openai>=1.57.4",
    "agent-client-protocol>=0.6.0",
]
```

### 代码中已导入的关键依赖（证据）
#### prompt-toolkit（CLI 交互）
```python
# File: mini_agent/cli.py | Lines: 12-23 | Description: prompt_toolkit imports
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
```

#### tiktoken（Token 估算）
```python
# File: mini_agent/agent.py | Lines: 85-95 | Description: Token estimation uses tiktoken
def _estimate_tokens(self) -> int:
    """Accurately calculate token count for message history using tiktoken

    Uses cl100k_base encoder (GPT-4/Claude/M2 compatible)
    """
    try:
        # Use cl100k_base encoder (used by GPT-4 and most modern models)
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback: if tiktoken initialization fails, use simple estimation
        return self._estimate_tokens_fallback()
```

#### pydantic + pyyaml（配置与模型）
```python
# File: mini_agent/config.py | Lines: 6-15 | Description: yaml and pydantic imports
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class RetryConfig(BaseModel):
    """Retry configuration"""
```

#### anthropic / openai（LLM Provider SDK）
```python
# File: mini_agent/llm/anthropic_client.py | Lines: 1-10 | Description: Anthropic SDK import
"""Anthropic LLM client implementation."""

import logging
from typing import Any

import anthropic

from ..retry import RetryConfig, async_retry
```

```python
# File: mini_agent/llm/openai_client.py | Lines: 1-12 | Description: OpenAI SDK import
"""OpenAI LLM client implementation."""

import json
import logging
from typing import Any

from openai import AsyncOpenAI
```

#### MCP（模型上下文协议）
```python
# File: mini_agent/tools/mcp_loader.py | Lines: 1-11 | Description: MCP client imports
"""MCP tool loader with real MCP client integration."""

import json
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
```

#### ACP（Agent Client Protocol）
```python
# File: mini_agent/acp/__init__.py | Lines: 12-30 | Description: ACP imports
from acp import (
    PROTOCOL_VERSION,
    AgentSideConnection,
    CancelNotification,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    session_notification,
    start_tool_call,
    stdio_streams,
    text_block,
    tool_content,
    update_agent_message,
    update_agent_thought,
    update_tool_call,
)
```

### 仅在依赖声明/文档中出现的库（待确认）
- requests、httpx、pip、pipx、pytest 等在依赖声明中出现，但在核心包 import 搜索中未发现使用；是否用于运行时仍需结合实际执行环境确认。
- 这类库的存在可优先理解为“安装依赖集合”，不等同于“运行时必需”。

## 目录结构（核心目录）
```text
mini-agent/
├── mini_agent/              # Core package
│   ├── acp/                  # ACP adapter
│   ├── config/               # Config assets (yaml/json/prompt)
│   ├── llm/                  # LLM clients (Anthropic/OpenAI)
│   ├── schema/               # Pydantic message/tool schemas
│   ├── skills/               # Skills submodule
│   ├── tools/                # Built-in tools (file/bash/mcp/skill)
│   └── utils/                # Terminal utils
├── docs/                     # Documentation
├── examples/                 # Usage examples
├── scripts/                  # Setup scripts
├── tests/                    # Tests
├── pyproject.toml            # Project metadata
└── uv.lock                   # Dependency lock
```

## 技能子模块（技能集）
```ini
# File: .gitmodules | Lines: 1-3 | Description: Skills submodule
[submodule "mini_agent/skills"]
	path = mini_agent/skills
	url = https://github.com/anthropics/skills.git
```

## 入口点（CLI / ACP）
```toml
# File: pyproject.toml | Lines: 27-29 | Description: CLI entry points
[project.scripts]
mini-agent = "mini_agent.cli:main"
mini-agent-acp = "mini_agent.acp.server:main"
```

```python
# File: mini_agent/cli.py | Lines: 580-596 | Description: CLI main entry
def main():
    """Main entry point for CLI"""
    # Parse command line arguments
    args = parse_args()

    # Determine workspace directory
    if args.workspace:
        workspace_dir = Path(args.workspace).absolute()
    else:
        # Use current working directory
        workspace_dir = Path.cwd()

    # Ensure workspace directory exists
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Run the agent (config always loaded from package directory)
    asyncio.run(run_agent(workspace_dir))
```

```python
# File: mini_agent/acp/server.py | Lines: 1-5 | Description: ACP entry point
"""ACP server entry point."""

from mini_agent.acp import main

if __name__ == "__main__":
    main()
```
