# Mini-Agent 深度速览（MiniMax-AI/Mini-Agent）
更新：2025-12-20 由 Codex

## 核心信息
- 定位：基于 MiniMax M2（Anthropic 兼容）的最小可用 Agent 参考实现，涵盖执行环、上下文/记忆管理、工具体系、MCP、Claude Skills。
- 许可：MIT，可商用与二次开发。
- 主要模块：`mini_agent.agent`（执行循环）· `mini_agent.llm_client`（LLM 客户端）· `mini_agent.tools`（内置工具与记忆）· `mini_agent.config`（配置加载）· `mini_agent.mcp`（MCP 集成）· `skills/`（Claude Skills 子模块）。
- 工作区：所有读写/命令均限定在 `workspace_dir`，记忆文件存储为 `{workspace_dir}/.agent_memory.json`，日志位于工作区下。

## 快速学习路线（先 1 后 2）
1. 读 README/README_CN，明确功能边界与安装方式。
2. 浏览核心代码：`mini_agent/agent.py`（执行环）、`mini_agent/cli.py`（入口与配置）、`mini_agent/tools/`（工具体系）、`mini_agent/logger.py`（日志）、`mini_agent/config.py`（配置加载）。
3. 复盘主链路：CLI 解析 → Config 加载 → LLMClient 初始化 → Agent.run 循环 → Tool 执行 → Logger 记录。
4. 提炼可复用点：工具 schema、上下文摘要策略、持久记忆接口、技能/MCP 的统一接入。

## 必须掌握的知识清单
- LLM API：Anthropic 兼容协议、tool/function calling、流式返回与重试策略。
- Prompt 设计：system 指令、工具 schema 的描述方式、摘要提示词。
- Agent 执行环：多步循环、终止条件、错误处理与恢复。
- 工具体系：统一接口、参数校验、执行结果回写。
- 上下文管理：token 估算、超限摘要策略与历史裁剪。
- 记忆机制：会话记忆持久化、检索策略与结构化存储。
- 配置与 CLI：多层配置、workspace 约束、命令入口。
- 日志与评测：请求/响应/工具记录、成本与性能统计、回放能力。
- 测试与模拟：LLM mock、工具单测、端到端冒烟验证。
- 并发与异步：异步工具执行、流式响应处理。

## 框架重点（对齐 Mini-Agent）
- 稳定的执行环：LLM ↔ 工具 ↔ 历史消息往返，受 `max_steps` 约束。
- 统一工具协议：schema 描述 + 执行接口，支持内置工具与外部扩展。
- 智能上下文控制：token 预算 + 自动摘要，保证长任务不中断。
- 持久记忆：会话级记录与检索，减少重复上下文传递。
- 插件化生态：Claude Skills + MCP 接入路径保持一致。
- 可观测性：完整日志与统计，便于调试与成本管理。

## 我们的框架范围（Phase 2 定义）
- 核心模块：Agent、LLMClient、ToolRegistry、Memory、PromptManager、Logger、Config。
- 内置能力：文件读写/编辑、shell、会话记忆、基础摘要。
- 接入方式：CLI + 配置文件 + 环境变量。
- 验证体系：单元测试 + 冒烟测试 + 功能测试，配套示例任务。

## 安装与配置
- 快速体验（无源码改动）：`pipx install git+https://github.com/MiniMax-AI/Mini-Agent.git`，随后运行 `curl -fsSL https://raw.githubusercontent.com/MiniMax-AI/Mini-Agent/main/scripts/setup-config.sh | bash` 自动写入 `~/.mini-agent/config/config.yaml`。
- 开发模式：`git clone … && cd Mini-Agent && uv sync && git submodule update --init --recursive`；复制 `mini_agent/config/config-example.yaml` 为 `mini_agent/config/config.yaml`；运行 `uv run python -m mini_agent.cli` 或 `pipx install -e .` 后直接用 `mini-agent`。
- 必填配置：`api_key`、`api_base`（全球 `https://api.minimax.io/anthropic` / 国内 `https://api.minimaxi.com/anthropic`）、`model: MiniMax-M2`，可选 `max_steps`、`workspace_dir`。
- 配置优先级：`MINI_AGENT_CONFIG` 环境变量 > `~/.mini-agent/config/config.yaml` > `mini_agent/config/config.yaml`。

## 核心架构
- Agent 执行环：`Agent.run()` 迭代请求 LLM → 解析工具调用 → 执行工具 → 更新消息与统计，受 `max_steps` 限制。
- 上下文与记忆：使用 tiktoken 计数；超限触发摘要，保留用户消息并压缩 Agent 片段；`SessionNoteTool/RecallNoteTool` 将重要笔记持久化到 `.agent_memory.json`，按分类查询。
- LLM 客户端：Anthropic 兼容格式，支持思维链注入、工具 schema 转换、流式与指数退避重试。
- 工作区约束：内置文件/命令类工具统一以 `workspace_dir` 为根，保证路径隔离。

## 工具生态
- 内置工具：`ReadTool`（读文件）、`WriteTool`（写文件）、`EditTool`（就地编辑）、`BashTool`（工作区 shell）、`SessionNoteTool/RecallNoteTool`（持久记忆）。
- Claude Skills：`skills/` 子模块提供 15+ 专业能力（文档处理、设计、开发/测试等），通过 `git submodule update --init --recursive` 拉取；`create_skill_tools` 动态加载 SKILL.md。
- MCP 集成：读取 `mcp.json` 动态注册外部工具，`load_mcp_tools_async` 加载；示例包含 web 搜索等（需设置相应 API key 环境变量）。

## 使用与示例
- CLI：`mini-agent --version`；`mini-agent --workspace /path/to/project` 进入交互模式。
- 交互指令：`/help` 查看命令，`/stats` 显示步数/工具调用/Token，用 `/clear` 清空历史，`/exit` 退出并展示统计。
- 示例进阶（见深度 wiki）：基础文件工具 → 简单 Agent → 记忆示例 → 全量 Agent 与技能/MCP。

## 生产与运维要点
- 容器化：建议 Docker/K8s，设置 CPU/内存与磁盘限额，挂载工作区与配置卷。
- 权限：使用非 root 账户运行，最小权限原则。
- 工作区策略：按任务/租户隔离，必要时会话结束清理或归档 `.agent_memory.json`。
- 监控与日志：保留请求/响应与工具执行日志以便审计与调试；长会话注意磁盘占用。

## 关键路径速查
- 配置：`~/.mini-agent/config/config.yaml`（快速模式）或 `mini_agent/config/config.yaml`（开发模式）；模板 `mini_agent/config/config-example.yaml`。
- 记忆：`{workspace_dir}/.agent_memory.json`。
- 代码入口：`mini_agent/cli.py`；核心循环 `mini_agent/agent.py`；工具目录 `mini_agent/tools/`；技能目录 `skills/`；MCP 配置 `mcp.json`。

## 快速验证
```bash
mini-agent --version
mini-agent --workspace ./workspace  # 成功后应读到配置，初始化 LLM，进入交互提示
/stats  # 交互内查看计数
```

## 参考来源
- deepwiki: Overview、Getting Started、Core Architecture、Built-in Tools、Claude Skills System、Configuration Reference、Production Deployment 等页面
- 关联文件：README.md / README_CN.md / docs/DEVELOPMENT_GUIDE.md / docs/PRODUCTION_GUIDE.md / config-example.yaml
- https://github.com/MiniMax-AI/Mini-Agent
- https://raw.githubusercontent.com/MiniMax-AI/Mini-Agent/main/README.md

## 延伸阅读（本地）
- `learn/mini-agent-code-tour.md`
- `learn/mini-agent-like-blueprint.md`
- `learn/mini-agent-file-index.md`
