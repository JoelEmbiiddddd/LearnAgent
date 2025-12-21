# Mini-Agent 代码速读与理解路线
更新：2025-12-20 由 Codex

目标：用最短路径读懂 Mini-Agent 的全部核心代码与关键设计点，并能复刻核心机制。
本地仓库位置：`/home/work/learn/Mini-Agent`

## 1. 建议阅读顺序（先主线，后细节）
1) 功能与边界
- `README_CN.md`：明确核心特性、使用模式、配置方式。

2) 入口与配置
- `mini_agent/cli.py`：启动入口、配置加载、工具装配、交互循环。
- `mini_agent/config.py`：配置结构、默认值、配置文件查找优先级。
- `mini_agent/config/config-example.yaml`：实际可用配置项清单。

3) 核心运行时
- `mini_agent/agent.py`：Agent 主循环、上下文摘要、工具调用、终止条件。
- `mini_agent/schema/schema.py`：Message/ToolCall/Response 等核心数据结构。

4) LLM 客户端
- `mini_agent/llm/llm_wrapper.py`：统一 LLMClient 抽象与 Provider 选择。
- `mini_agent/llm/anthropic_client.py`：请求拼装、工具格式、响应解析。
- `mini_agent/llm/openai_client.py`：OpenAI 协议转换（与 Anthropic 对照）。
- `mini_agent/retry.py`：重试机制与指数退避。

5) 工具体系与扩展
- `mini_agent/tools/base.py`：工具接口与 schema。
- `mini_agent/tools/file_tools.py`：读写改工具与 token 截断策略。
- `mini_agent/tools/bash_tool.py`：前台/后台执行、bash_output/bash_kill。
- `mini_agent/tools/note_tool.py`：会话记忆读写与检索。
- `mini_agent/tools/skill_loader.py`、`mini_agent/tools/skill_tool.py`：Skills 发现与按需加载。
- `mini_agent/tools/mcp_loader.py`：MCP 配置与工具注入。

6) 可观测与细节
- `mini_agent/logger.py`：请求/响应/工具日志。
- `mini_agent/utils/terminal_utils.py`：终端宽度计算与显示。

7) 测试用例（验证思路）
- `tests/test_agent.py`：端到端 Agent 运行方式与最小任务验证。
- `tests/test_llm.py`、`tests/test_llm_clients.py`：LLM 客户端行为。
- `tests/test_note_tool.py`、`tests/test_tools.py`：工具与记忆。
- `tests/test_mcp.py`、`tests/test_skill_loader.py`：扩展体系。

## 2. 核心执行环（Agent.run）要点
入口：`mini_agent/agent.py`
- 初始化：系统提示词 + workspace 注入 → Message 列表起始于 system。
- 每步执行：
  1. `_summarize_messages()`：超限触发摘要，保留 user 消息，压缩中间执行片段。
  2. `llm.generate(messages, tools)`：传入 Tool 列表（Tool.to_schema）。
  3. 将 LLMResponse 写入 history（assistant 消息包含 thinking/tool_calls）。
  4. 若无 tool_calls → 返回最终 content。
  5. 遍历 tool_calls 执行，结果写为 tool 消息，再进入下一轮。
- 终止条件：`max_steps` 达到或 LLM 无工具调用。

理解关键：
- 主循环简单、状态显式，适合日志和重放。
- 工具调用与消息追加的结构是“可复刻”的核心框架。

## 3. 上下文控制与摘要策略
位置：`mini_agent/agent.py`
- `_estimate_tokens()`：tiktoken 精确计数；失败时 fallback。
- `_summarize_messages()`：只要本地估算或 API total_tokens 超限，就触发摘要。
- 摘要策略：保留 system 与所有 user，压缩“user 与 user 之间的 Agent 执行片段”。
- `_create_summary()`：用 LLM 总结执行过程，聚焦工具调用与结果，不复述用户意图。

可复刻点：
- “保用户、压执行”的结构非常关键，保证任务意图不丢失。

## 4. LLM 客户端链路
位置：`mini_agent/llm/`
- `LLMClient` 负责 provider 路由与 api_base 后缀拼接。
- `AnthropicClient`：把 Message 转成 Anthropic content blocks（thinking/tool_use/tool_result）。
- `OpenAIClient`：把 Tool schema 转成 OpenAI function/tool 格式。
- `retry.py`：异步重试装饰器 + 退避策略。

可复刻点：
- 保持内部统一 Message/ToolCall 模型，协议差异仅在 LLMClientBase 子类内处理。

## 5. 工具系统与扩展
位置：`mini_agent/tools/`
- `Tool` 抽象：name/description/parameters/execute + to_schema。
- 文件工具：所有路径相对 workspace，读文件带行号、写文件可覆盖、编辑要求唯一匹配。
- Bash 工具：支持后台任务 + 输出轮询（bash_output）+ 终止（bash_kill）。
- Note 工具：`.agent_memory.json` 持久化记忆，支持分类与关键词检索。
- Skills：
  - `SkillLoader` 读 SKILL.md → 元数据提示（Level 1）。
  - `GetSkillTool` 按需拉取完整内容（Level 2）。
- MCP：读取 `mcp.json`，启动 MCP server，动态挂载工具。

可复刻点：
- Tool 的 schema 化是 LLM 选择工具的核心前提。
- Skills 与 MCP 本质是“工具来源”，统一接口即可。

## 6. CLI、配置与工作区
位置：`mini_agent/cli.py`、`mini_agent/config.py`
- 配置优先级：本地 dev → 用户目录 `~/.mini-agent/config` → 安装包内。
- workspace：CLI 参数优先，工具与 Agent 使用同一 workspace 限定范围。
- System prompt：可从配置路径读取；支持注入 skills metadata。

可复刻点：
- workspace 作为唯一资源边界，路径解析与工具执行都以此为根。

## 7. 日志与可观测
位置：`mini_agent/logger.py`
- 日志存储：`~/.mini-agent/log/agent_run_*.log`
- 记录内容：LLM request/response、tool args、tool results。

可复刻点：
- 日志格式结构化 JSON，便于排障与回放。

## 8. 测试对照与学习抓手
- `tests/test_agent.py`：完整端到端执行环 + 文件任务验证。
- `tests/test_note_tool.py`：记忆读写与检索逻辑。
- `tests/test_llm_clients.py`：不同 provider 的请求格式转换。

## 9. 复刻清单（你要实现的最小完整闭环）
- Agent 执行环（LLM ↔ 工具 ↔ 历史）+ max_steps。
- Tool 抽象 + JSON schema 转换。
- LLMClient 统一封装（Anthropic/OpenAI）。
- 上下文摘要（token 预算 + 记录压缩）。
- 会话记忆（持久化 JSON）。
- CLI + config + workspace 限定。
- 结构化日志。
- 基础工具：读/写/编辑/命令 + note。
- MCP + Skills 的动态接入路径。

## 10. 学习完成的自检问题
- 我能画出 Agent.run 的每一步，并说明消息是如何追加的吗？
- 我能解释 tool_calls 在 Anthropic 与 OpenAI 的差异吗？
- 我知道 workspace 约束如何贯穿工具与 Agent 吗？
- 我能复述摘要触发条件和摘要策略吗？
- 我能指出 MCP 和 Skills 的接入点吗？
