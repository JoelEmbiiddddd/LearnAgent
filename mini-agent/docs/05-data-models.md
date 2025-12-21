# 数据模型与配置结构

## 配置模型（Config）
配置模型由 pydantic BaseModel 定义，包含 LLM、Agent 与 Tools 三个子配置。

```python
# File: mini_agent/config.py | Lines: 12-55 | Description: Config models
class RetryConfig(BaseModel):
    """Retry configuration"""

    enabled: bool = True
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class LLMConfig(BaseModel):
    """LLM configuration"""

    api_key: str
    api_base: str = "https://api.minimax.io"
    model: str = "MiniMax-M2"
    provider: str = "anthropic"  # "anthropic" or "openai"
    retry: RetryConfig = Field(default_factory=RetryConfig)


class AgentConfig(BaseModel):
    """Agent configuration"""

    max_steps: int = 50
    workspace_dir: str = "./workspace"
    system_prompt_path: str = "system_prompt.md"


class ToolsConfig(BaseModel):
    """Tools configuration"""

    # Basic tools (file operations, bash)
    enable_file_tools: bool = True
    enable_bash: bool = True
    enable_note: bool = True
```

### 设计动机与收益
- **子配置分离**：LLM/Agent/Tools 分开定义，便于按职责扩展与局部验证（字段默认值在类定义中可见）。
- **默认值降低门槛**：`max_steps`、`workspace_dir`、工具开关给出默认值，使最小配置即可运行。
- **显式类型**：使用 pydantic 提供类型校验与默认值统一入口，减少运行期配置错误。

## 消息与工具调用模型（schema）
定义了对话消息、工具调用结构与 LLM 响应。

```python
# File: mini_agent/schema/schema.py | Lines: 7-55 | Description: Message and response models
class LLMProvider(str, Enum):
    """LLM provider types."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class FunctionCall(BaseModel):
    """Function call details."""

    name: str
    arguments: dict[str, Any]  # Function arguments as dict


class ToolCall(BaseModel):
    """Tool call structure."""

    id: str
    type: str  # "function"
    function: FunctionCall


class Message(BaseModel):
    """Chat message."""

    role: str  # "system", "user", "assistant", "tool"
    content: str | list[dict[str, Any]]  # Can be string or list of content blocks
    thinking: str | None = None  # Extended thinking content for assistant messages
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None  # For tool role


class TokenUsage(BaseModel):
    """Token usage statistics from LLM API response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """LLM response."""

    content: str
    thinking: str | None = None  # Extended thinking blocks
    tool_calls: list[ToolCall] | None = None
    finish_reason: str
    usage: TokenUsage | None = None  # Token usage from API response
```

### 设计动机与收益
- **Message 兼容工具调用**：`tool_calls` 与 `tool_call_id` 使工具结果可与 LLM 调用闭环对接。
- **thinking 字段保留推理块**：`thinking` 独立字段支持“思维/内容”分离显示与日志记录。
- **TokenUsage 外挂**：`usage` 可承载 LLM 返回的 token 统计，为摘要触发提供依据。

## 工具接口与结果模型
Tool 与 ToolResult 描述了工具能力与返回结构。

```python
# File: mini_agent/tools/base.py | Lines: 8-55 | Description: Tool base models
class ToolResult(BaseModel):
    """Tool execution result."""

    success: bool
    content: str = ""
    error: str | None = None


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

    def to_schema(self) -> dict[str, Any]:
        """Convert tool to Anthropic tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
```

### 设计动机与收益
- **统一结果语义**：`ToolResult` 统一 success/error/content，使日志与错误处理路径一致。
- **Schema 作为契约**：`parameters` + `to_schema` 将工具输入结构明确化，便于 LLM 生成结构化调用。

## Skill 数据模型
Skills 被解析为 Skill dataclass 并提供给 get_skill 使用。

```python
# File: mini_agent/tools/skill_loader.py | Lines: 15-37 | Description: Skill dataclass
@dataclass
class Skill:
    """Skill data structure"""

    name: str
    description: str
    content: str
    license: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None
    skill_path: Optional[Path] = None

    def to_prompt(self) -> str:
        """Convert skill to prompt format"""
        return f"""
# Skill: {self.name}

{self.description}

---

{self.content}
"""
```

### 设计动机与收益
- **元数据与内容分离**：`name/description` 用于发现与索引，`content` 用于按需加载。
- **prompt 封装**：`to_prompt` 直接输出规范化文本，降低工具调用时的拼接复杂度。
