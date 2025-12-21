# API 与 CLI 参考

## Python 包导出（mini_agent）
```python
# File: mini_agent/__init__.py | Lines: 1-16 | Description: Public exports
"""Mini Agent - Minimal single agent with basic tools and MCP support."""

from .agent import Agent
from .llm import LLMClient
from .schema import FunctionCall, LLMProvider, LLMResponse, Message, ToolCall

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "LLMClient",
    "LLMProvider",
    "Message",
    "LLMResponse",
    "ToolCall",
    "FunctionCall",
]
```

## CLI 入口
```toml
# File: pyproject.toml | Lines: 27-29 | Description: CLI entry points
[project.scripts]
mini-agent = "mini_agent.cli:main"
mini-agent-acp = "mini_agent.acp.server:main"
```

## Agent 构造参数
```python
# File: mini_agent/agent.py | Lines: 45-53 | Description: Agent constructor
def __init__(
    self,
    llm_client: LLMClient,
    system_prompt: str,
    tools: list[Tool],
    max_steps: int = 50,
    workspace_dir: str = "./workspace",
    token_limit: int = 80000,  # Summary triggered when tokens exceed this value
):
```

## LLMClient（统一封装）
```python
# File: mini_agent/llm/llm_wrapper.py | Lines: 30-60 | Description: LLMClient wrapper
def __init__(
    self,
    api_key: str,
    provider: LLMProvider = LLMProvider.ANTHROPIC,
    api_base: str = "https://api.minimaxi.com",
    model: str = "MiniMax-M2",
    retry_config: RetryConfig | None = None,
):
    self.provider = provider
    self.api_key = api_key
    self.model = model
    self.retry_config = retry_config or RetryConfig()

    # for backward compatibility
    api_base = api_base.replace("/anthropic", "")

    # Append provider-specific suffix to api_base
    if provider == LLMProvider.ANTHROPIC:
        full_api_base = f"{api_base.rstrip('/')}/anthropic"
    elif provider == LLMProvider.OPENAI:
        full_api_base = f"{api_base.rstrip('/')}/v1"
```

## Tool 接口
```python
# File: mini_agent/tools/base.py | Lines: 16-36 | Description: Tool interface
class Tool:
    """Base class for all tools."""

    @property
    def name(self) -> str:
        """Tool name."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Tool description."""
        raise NotImplementedError

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema (JSON Schema format)."""
        raise NotImplementedError

    async def execute(self, *args, **kwargs) -> ToolResult:  # type: ignore
        """Execute the tool with arbitrary arguments."""
        raise NotImplementedError
```

## 参考用法（示例）
```python
# File: examples/02_simple_agent.py | Lines: 50-69 | Description: Minimal agent setup
# Initialize LLM client
llm_client = LLMClient(
    api_key=config.llm.api_key,
    api_base=config.llm.api_base,
    model=config.llm.model,
)

# Initialize tools
tools = [
    ReadTool(workspace_dir=workspace_dir),
    WriteTool(workspace_dir=workspace_dir),
    EditTool(workspace_dir=workspace_dir),
    BashTool(),
]

# Create agent
agent = Agent(
    llm_client=llm_client,
    system_prompt=system_prompt,
    tools=tools,
    max_steps=10,
    workspace_dir=workspace_dir,
)
```
