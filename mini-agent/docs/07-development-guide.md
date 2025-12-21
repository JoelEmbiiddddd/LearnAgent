# 开发与扩展指南

## 开发准备
- 建议先完成配置文件初始化，再运行 CLI。
- 需要有效的 API Key，否则 LLM 调用会失败（详见测试用例）。

### 自动化配置脚本
脚本会创建 `~/.mini-agent/config` 并下载配置模板：

```bash
# File: scripts/setup-config.sh | Lines: 15-46 | Description: Config setup script
CONFIG_DIR="$HOME/.mini-agent/config"

echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Mini Agent Configuration Setup              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Create config directory
echo -e "${BLUE}[1/2]${NC} Creating configuration directory..."
if [ -d "$CONFIG_DIR" ]; then
    # Auto backup existing config
    BACKUP_DIR="$HOME/.mini-agent/config.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}   Configuration directory exists, backing up to:${NC}"
    echo -e "${YELLOW}   $BACKUP_DIR${NC}"
    cp -r "$CONFIG_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}   ✓ Backup created${NC}"
else
    mkdir -p "$CONFIG_DIR"
    echo -e "${GREEN}   ✓ Created: $CONFIG_DIR${NC}"
fi
```

### 配置文件优先级
```python
# File: mini_agent/config.py | Lines: 160-187 | Description: Config file search order
def find_config_file(cls, filename: str) -> Path | None:
    """Find configuration file with priority order

    Search for config file in the following order of priority:
    1) mini_agent/config/{filename} in current directory (development mode)
    2) ~/.mini-agent/config/{filename} in user home directory
    3) {package}/mini_agent/config/{filename} in package installation directory
    """
    # Priority 1: Development mode - current directory's config/ subdirectory
    dev_config = Path.cwd() / "mini_agent" / "config" / filename
    if dev_config.exists():
        return dev_config

    # Priority 2: User config directory
    user_config = Path.home() / ".mini-agent" / "config" / filename
    if user_config.exists():
        return user_config

    # Priority 3: Package installation directory's config/ subdirectory
    package_config = cls.get_package_dir() / "config" / filename
    if package_config.exists():
        return package_config

    return None
```

## Skills 子模块
Skills 位于 git submodule 中，需要更新子模块后才能完整使用：

```ini
# File: .gitmodules | Lines: 1-3 | Description: Skills submodule
[submodule "mini_agent/skills"]
	path = mini_agent/skills
	url = https://github.com/anthropics/skills.git
```

## 扩展工具（自定义 Tool）
Tool 的扩展点在 `mini_agent/tools/` 下，需继承 Tool 基类并实现接口：

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

## MCP 服务器管理
MCP 服务器配置位于 `mini_agent/config/mcp.json`，默认 disabled：

```json
# File: mini_agent/config/mcp.json | Lines: 1-27 | Description: MCP servers disabled by default
{
  "mcpServers": {
    "minimax_search": {
      "description": "MiniMax Search - Powerful web search and intelligent browsing ⭐",
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MiniMax-AI/minimax_search",
        "minimax-search"
      ],
      "env": {
        "JINA_API_KEY": "",
        "SERPER_API_KEY": "",
        "MINIMAX_API_KEY": ""
      },
      "disabled": true
    },
    "memory": {
      "description": "Memory - Knowledge graph memory system (long-term memory based on graph database)",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ],
      "disabled": true
    }
  }
}
```

## 日志与调试
Agent 运行日志写入 `~/.mini-agent/log/`，便于回溯请求、响应与工具调用：

```python
# File: mini_agent/logger.py | Lines: 19-35 | Description: Log directory initialization
def __init__(self):
    """Initialize logger

    Logs are stored in ~/.mini-agent/log/ directory
    """
    # Use ~/.mini-agent/log/ directory for logs
    self.log_dir = Path.home() / ".mini-agent" / "log"
    self.log_dir.mkdir(parents=True, exist_ok=True)
    self.log_file = None
    self.log_index = 0

def start_new_run(self):
    """Start new run, create new log file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"agent_run_{timestamp}.log"
```

## 生产部署参考（仓库文档）
生产相关建议集中在 `docs/PRODUCTION_GUIDE.md`，强调本项目为教学级 Demo，需要补齐稳定性与安全性。

```markdown
# File: docs/PRODUCTION_GUIDE.md | Lines: 15-24 | Description: Demo-level feature scope
This project is a **teaching-level demo** that demonstrates the core concepts and execution flow of an Agent. To reach production level, many complex issues still need to be addressed.

### What We've Implemented (Demo Level)

| Feature                  | Demo Implementation                   |
| --------------------- | --------------------------- |
| **Context Management** | ✅ Simple persistence via SessionNoteTool with file storage; basic summarization when approaching context window limit |
| **Tool Calling**          | ✅ Basic Read/Write/Edit/Bash |
| **Error Handling**          | ✅ Basic exception catching              |
| **Logging**              | ✅ Simple print output           |
```

```markdown
# File: docs/PRODUCTION_GUIDE.md | Lines: 51-58 | Description: Container deployment advantages
### 3.1 Container Deployment Recommendations

We recommend using K8s/Docker environments for Agent deployment. Containerized deployment has the following advantages:

- **Resource Isolation**: Each Agent instance runs in an independent container without interference
- **Elastic Scaling**: Automatically adjust instance count based on load
- **Version Management**: Easy rollback and canary releases
- **Environment Consistency**: Development, testing, and production environments are completely consistent
```

```markdown
# File: docs/PRODUCTION_GUIDE.md | Lines: 107-113 | Description: Least privilege guidance
#### 3.3.1 Principle of Least Privilege

**Never run the Agent as root user**, as this poses serious security risks.

**Dockerfile Best Practices**:
```

## 社区与贡献参考
README 明确指向贡献指南与行为准则，可作为协作入口。

```markdown
# File: README.md | Lines: 316-321 | Description: Contributing references
## Contributing

Issues and Pull Requests are welcome!

- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines
```

## 已知文档差异（待确认）
README 中提到修改 `mini_agent/llm.py` 以解决 SSL 问题，但仓库中未找到该文件（基于文件列表检索）。对应片段如下：

```python
# File: README.md | Lines: 291-292 | Description: Troubleshooting snippet referencing mini_agent/llm.py
# Line 50: Add verify=False to AsyncClient
async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
```

生产指南示例中使用 `main.py` 作为启动入口，但仓库未发现该文件；建议以 `mini_agent.cli` 或 `mini-agent` 入口替换（待确认）。

```markdown
# File: docs/PRODUCTION_GUIDE.md | Lines: 141-145 | Description: Dockerfile entrypoint example
# Sync dependencies using uv
RUN uv sync

# Start the application
CMD ["uv", "run", "python", "main.py"]
```
