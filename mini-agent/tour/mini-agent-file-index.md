# Mini-Agent 文件索引（带职责说明）
更新：2025-12-20 由 Codex

本地仓库位置：`/home/work/learn/Mini-Agent`

## 1) 核心包 mini_agent/
- `mini_agent/__init__.py`：包导出入口。
- `mini_agent/agent.py`：Agent 主循环、上下文摘要、工具调度。
- `mini_agent/cli.py`：CLI 入口、配置加载、工具初始化、交互会话。
- `mini_agent/config.py`：配置模型、默认值、配置文件查找策略。
- `mini_agent/logger.py`：LLM 请求/响应、工具调用日志。
- `mini_agent/retry.py`：通用异步重试与指数退避。
- `mini_agent/schema/schema.py`：Message/ToolCall/LLMResponse 模型。
- `mini_agent/utils/terminal_utils.py`：终端显示宽度计算与截断。

### 配置与模板
- `mini_agent/config/config-example.yaml`：配置示例。
- `mini_agent/config/mcp.json`：MCP 工具配置示例。
- `mini_agent/config/system_prompt.md`：system prompt 模板。

### LLM 适配层
- `mini_agent/llm/base.py`：LLMClientBase 抽象。
- `mini_agent/llm/llm_wrapper.py`：LLMClient 统一封装与 provider 选择。
- `mini_agent/llm/anthropic_client.py`：Anthropic 协议实现。
- `mini_agent/llm/openai_client.py`：OpenAI 协议实现。

### 工具层
- `mini_agent/tools/base.py`：Tool/ToolResult 抽象与 schema 转换。
- `mini_agent/tools/file_tools.py`：读/写/改文件工具。
- `mini_agent/tools/bash_tool.py`：bash 执行 + 输出查看 + 终止。
- `mini_agent/tools/note_tool.py`：会话记忆（JSON）读写与检索。
- `mini_agent/tools/skill_loader.py`：读取 SKILL.md 并注入元数据。
- `mini_agent/tools/skill_tool.py`：get_skill 工具，按需加载完整 Skill。
- `mini_agent/tools/mcp_loader.py`：MCP server 连接与工具注入。

### ACP（编辑器协议）
- `mini_agent/acp/__init__.py`：ACP 协议桥接，封装 Agent 为 ACP server。
- `mini_agent/acp/server.py`：ACP server 入口。

### Skills
- `mini_agent/skills/README.md`：Skills 说明。
- `mini_agent/skills/agent_skills_spec.md`：Skills 规范。
- `mini_agent/skills/THIRD_PARTY_NOTICES.md`：第三方声明。

## 2) tests/
- `tests/test_agent.py`：端到端 Agent 任务执行测试。
- `tests/test_llm.py`：LLM 接口行为测试。
- `tests/test_llm_clients.py`：Anthropic/OpenAI 客户端转换测试。
- `tests/test_tools.py`：工具基类与基本工具行为测试。
- `tests/test_bash_tool.py`：bash 工具测试。
- `tests/test_note_tool.py`：记忆工具测试。
- `tests/test_mcp.py`：MCP 工具加载测试。
- `tests/test_skill_loader.py`：技能加载测试。
- `tests/test_skill_tool.py`：技能工具测试。
- `tests/test_tool_schema.py`：工具 schema 兼容测试。
- `tests/test_terminal_utils.py`：终端显示工具测试。
- `tests/test_integration.py`：集成测试。
- `tests/test_session_integration.py`：会话级测试。
- `tests/test_markdown_links.py`：markdown 链接相关测试。
- `tests/test_acp.py`：ACP 适配测试。
