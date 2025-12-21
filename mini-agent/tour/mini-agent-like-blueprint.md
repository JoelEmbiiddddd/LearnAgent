# Mini-Agent 类框架实现蓝图
更新：2025-12-20 由 Codex

目标：在尽量复刻 Mini-Agent 设计理念的前提下，快速产出一个可运行、可扩展、可测试的 Agent 框架。

## 1. 架构分层与模块边界
1) 入口层
- CLI（交互/命令模式），负责配置加载与会话循环。

2) 运行时层
- Agent：主循环、历史消息、上下文摘要、工具调度。
- Planner/Executor（可选）：如果需要规划，可拆分为独立组件。

3) LLM 层
- LLMClient 统一接口 + Provider 子类（Anthropic/OpenAI）。
- 负责消息格式转换、工具 schema 适配、流式/重试。

4) 工具层
- Tool 抽象：schema + execute。
- 内置工具：文件、命令、记忆。
- 扩展工具：Skills、MCP。

5) 记忆与上下文层
- 会话记忆：JSON/SQLite（Mini-Agent 为 JSON）。
- 历史摘要：token 预算 + 执行摘要。

6) 配置与日志
- Config（YAML）+ 优先级查找。
- Logger：记录请求/响应/工具调用。

## 2. 关键接口（与 Mini-Agent 对齐）
- Message
  - role: system/user/assistant/tool
  - content: str 或 content blocks
  - thinking/tool_calls/tool_call_id

- Tool
  - name/description/parameters
  - execute(**kwargs) -> ToolResult
  - to_schema() / to_openai_schema()

- LLMClient
  - generate(messages, tools) -> LLMResponse

- Agent
  - add_user_message(content)
  - run() -> str

## 3. 运行时数据流（核心链路）
1. CLI 读取配置 → 初始化 LLMClient → 加载 Tools → 创建 Agent。
2. Agent.run 循环：
   - 摘要检测 → LLM generate → 写入 assistant 消息。
   - tool_calls → 执行工具 → 写入 tool 消息。
   - 无 tool_calls → 结束。
3. Logger 记录每次请求/响应/工具结果。

## 4. 关键策略（复刻 Mini-Agent）
- 上下文控制：保留用户消息，压缩中间执行片段。
- 工具分发：LLM 选工具，Agent 只做注册与执行。
- 扩展路径：Skills 与 MCP 都是“工具来源”。
- 工作区隔离：所有文件与命令都在 workspace 内完成。

## 5. 模块清单（建议目录结构）
- agent/
  - agent.py
  - message.py
- llm/
  - base.py
  - anthropic_client.py
  - openai_client.py
  - llm_client.py
- tools/
  - base.py
  - file_tools.py
  - bash_tool.py
  - note_tool.py
  - skill_loader.py
  - skill_tool.py
  - mcp_loader.py
- config/
  - config.py
  - config-example.yaml
  - system_prompt.md
- logging/
  - logger.py
- utils/
  - terminal_utils.py
- cli.py
- tests/
  - test_agent.py
  - test_tools.py
  - test_llm.py
  - test_mcp.py

## 6. 配置设计（与 Mini-Agent 近似）
- api_key / api_base / model / provider
- retry: enabled / max_retries / initial_delay / max_delay
- agent: max_steps / workspace_dir / system_prompt_path
- tools: enable_file_tools / enable_bash / enable_note / enable_skills / enable_mcp

## 7. 最小完整实现顺序（便于快速开发）
1. Schema + Tool 抽象 + LLMClient 基类
2. Agent.run 主循环 + Message/ToolCall 数据结构
3. LLM Provider（先 Anthropic，再 OpenAI）
4. File/Bash/Note 工具
5. Config + CLI + workspace 管理
6. Logger + basic stats
7. Skills + MCP 接入
8. 测试与样例任务

## 8. 验证与测试
- 单测：Tool/LLM/Config/摘要逻辑。
- 冒烟：CLI 启动 + 简单任务执行。
- 功能：多步任务 + 工具调用 + 记忆写入。

## 9. 与 Mini-Agent 的关键对齐点
- 统一 Message/ToolCall 结构。
- 工具 schema 与 LLM 协议转换。
- 运行时循环的日志粒度。
- 上下文摘要策略与触发条件。
- MCP 与 Skills 的扩展方式。
