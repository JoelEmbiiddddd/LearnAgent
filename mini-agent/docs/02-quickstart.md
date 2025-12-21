# 快速开始

## 前置条件
- Python 版本要求：>= 3.10

```toml
# File: pyproject.toml | Lines: 1-6 | Description: Project metadata and Python version
[project]
name = "mini-agent"
version = "0.1.0"
description = "Minimal single agent demo with basic file tools and MCP support"
readme = "README.md"
requires-python = ">=3.10"
```

## 配置文件准备
1. 复制模板配置为本地配置：

```bash
cp mini_agent/config/config-example.yaml mini_agent/config/config.yaml
```

2. 按需填写 API Key 与模型信息（模板中提供字段说明）：

```yaml
# File: mini_agent/config/config-example.yaml | Lines: 13-38 | Description: LLM and agent configuration
api_key: "YOUR_API_KEY_HERE"  # Replace with your MiniMax API Key
api_base: "https://api.minimax.io"   # Global users (default)
# api_base: "https://api.minimaxi.com"  # China users
model: "MiniMax-M2"
# LLM provider: "anthropic" or "openai"
# The LLMClient will automatically append /anthropic or /v1 to api_base based on provider
provider: "anthropic"  # Default: anthropic

# ===== Retry Configuration =====
retry:
  enabled: true           # Enable retry mechanism
  max_retries: 3          # Maximum number of retries
  initial_delay: 1.0      # Initial delay time (seconds)
  max_delay: 60.0         # Maximum delay time (seconds)
  exponential_base: 2.0   # Exponential backoff base (delay = initial_delay * base^attempt)

# ===== Agent Configuration =====
max_steps: 100  # Maximum execution steps
workspace_dir: "./workspace"  # Working directory
system_prompt_path: "system_prompt.md"  # System prompt file (same config directory)
```

## 配置文件搜索顺序
CLI 会按以下优先级查找配置文件：开发目录 -> 用户目录 -> 包目录。

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

## 启动 CLI
- 开发模式：`python -m mini_agent.cli`
- 已安装命令：`mini-agent`（入口来自 pyproject.toml）

CLI 支持指定工作目录与版本查询：

```python
# File: mini_agent/cli.py | Lines: 179-199 | Description: CLI arguments
def parse_args() -> argparse.Namespace:
    """Parse command line arguments

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Mini Agent - AI assistant with file tools and MCP support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mini-agent                              # Use current directory as workspace
  mini-agent --workspace /path/to/dir     # Use specific workspace directory
        """,
    )
    parser.add_argument(
        "--workspace",
        "-w",
        type=str,
        default=None,
        help="Workspace directory (default: current directory)",
    )
```

## ACP 模式
- ACP CLI 入口：`mini-agent-acp`

```python
# File: mini_agent/acp/server.py | Lines: 1-5 | Description: ACP entry point
"""ACP server entry point."""

from mini_agent.acp import main

if __name__ == "__main__":
    main()
```

## MCP 相关配置
MCP 服务器在默认配置中被标记为 disabled，需要自行启用并配置环境变量：

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

## 自动化配置脚本（可选）
项目提供脚本用于初始化用户配置目录与下载配置模板：

```bash
# File: scripts/setup-config.sh | Lines: 15-55 | Description: Config setup script
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

# Step 2: Download configuration files from GitHub
echo -e "${BLUE}[2/2]${NC} Downloading configuration files..."
```
