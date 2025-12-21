# Mini-Agent 架构与工具详解（教学版）
更新：2025-12-15 由 Codex  
目的：帮助你从零设计/实现一个类 Mini-Agent 的系统，逐块理解可直接复刻的结构。

## 1. 总览与分层（对应源码骨架）
- **入口/CLI 层**：`mini_agent/cli.py` 解析参数（含 `--workspace`），`Config.from_yaml` 加载配置，初始化 LLMClient、工具列表、Agent，启动交互。
- **Agent 核心层**：`mini_agent/agent.py` 的 `Agent` 类统筹循环（LLM ↔ 工具 ↔ 历史），控制 `max_steps`、终止条件、日志。
- **上下文与记忆层**：`Agent._estimate_tokens` 计数，`Agent._summarize_messages` 超限摘要；持久记忆在 `note_tool.py`（SessionNote/Recall）。
- **LLM 客户端层**：`LLMClient`（文件未展开但被 CLI/Agent 使用）负责 Anthropic 兼容格式、工具 schema 转换、重试/流式。
- **工具生态层**：`tools/base.py` 抽象；`file_tools.py`、`bash_tool.py`、`note_tool.py` 内置工具；`skills/` 子模块；MCP 工具由 `load_mcp_tools_async` 动态加载。
- **工作区/环境层**：`workspace_dir` 由 CLI 解析并注入 Agent/工具，所有文件与命令操作都被沙箱在此；日志/记忆文件落在工作区。

## 2. 执行环（`mini_agent/agent.py`）
### 2.1 Agent 结构
- 构造参数：`llm`(LLMClient)、`tools`(dict name→Tool)、`max_steps`、`token_limit`、`workspace_dir`、`system_prompt`、`logger`。
- 设计理由：在构造阶段就固化资源边界（工作区）、上下文预算（token_limit）和工具表，便于测试和可重放。

### 2.2 `run` 循环（核心调度）
```python
async def run(self):
    self.logger.start_new_run()
    step = 0
    while step < self.max_steps:
        await self._summarize_messages()  # 防止上下文爆炸
        # 1) 调 LLM：self.llm.generate(messages=self.messages, tools=tool_schemas)
        # 2) 若有 tool_calls：分发到注册表执行
        # 3) 将 tool_results 写回消息历史
        # 4) 无 tool_calls 或 finish → 退出
        step += 1
```
- 设计理由：单一状态机，便于日志与重放；`max_steps` 是硬刹车，防止工具循环失控。

### 2.3 Token 估算 `_estimate_tokens`
```python
encoding = tiktoken.get_encoding("cl100k_base")
for msg in self.messages:
    if isinstance(msg.content, str):
        total += len(encoding.encode(msg.content))
    # 还会计入 thinking、tool_calls，末尾加 4 token 元数据开销
```
- 设计理由：真实计数优先；若 tiktoken 不可用则 fallback 粗估，保证功能可用性。

### 2.4 摘要 `_summarize_messages`
策略：**保留所有用户消息，压缩用户-用户之间的 Agent/工具片段**。  
流程：估算 tokens → 超限则分段 → 调 `_create_summary` 生成摘要 → 重组消息（system + user + summary）。  
- 设计理由：最大化保用户意图，缩减 Agent 执行日志；摘要由 LLM 生成，关注“做了什么/用过哪些工具/结果如何”。

### 2.5 工具分发与历史写回
- `tool_schemas = [t.to_schema() for t in tools]` 传给 LLM；响应的 `tool_calls` 按 name 查注册表并执行。
- 执行结果附在 assistant 消息的 `tool_results` 中，再进入下一轮。  
- 设计理由：工具选择由 LLM 决定，Agent 只做安全分发；结果回写使 LLM 能基于工具输出继续推理。

## 3. 上下文与摘要策略
- **Token 估算**：tiktoken/等编码器，遍历历史累加。  
- **触发阈值**：如 80k tokens，预留余量给新回复。  
- **摘要方法**：对用户-用户之间的 Agent 片段做压缩，生成一条 summary，保留所有用户消息不动。  
- **接口建议**：`maybe_summarize(history) -> history`；内部拆分、调用 LLM 生成 summary，再合并。  
- **目的**：保持长对话稳定，不丢用户意图。

## 4. 持久记忆（`tools/note_tool.py`）
- **SessionNoteTool/RecallNoteTool**：封装在工具层，读写 `{workspace_dir}/.agent_memory.json`。
- 代码要点：初始化传入 `workspace_dir`；写入自动建文件；Note 结构含 `id/content/category/timestamp/metadata`。
- 设计理由：记忆与上下文分离，避免把长历史塞回对话窗口；分类字段便于按主题检索。

## 5. LLM 客户端（`LLMClient`，由 CLI/Agent 使用）
- 虽未展开源码，但使用点显示：`LLMClient.generate(messages, tools)` 返回 `LLMResponse`（content/thinking/tool_calls/finish_reason）。
- `RetryConfig`（见 `cli.py`）提供 `max_retries/initial_delay/max_delay/exponential_base/on_retry`，说明内部有指数退避重试。
- 设计理由：把“协议/格式/重试/流式”隔离在客户端，Agent 只关心业务状态。

## 6. 工具体系（`mini_agent/tools`）
### 6.1 抽象基类（`tools/base.py`）
```python
class Tool(ABC):
    @property @abstractmethod def name(self) -> str
    @property @abstractmethod def description(self) -> str
    @property @abstractmethod def parameters(self) -> Dict[str, Any]
    @abstractmethod async def execute(self, **kwargs) -> ToolResult
```
- 设计理由：统一接口（schema + execute），便于 LLM 选择、Agent 分发与测试替身。

### 6.2 文件工具（`tools/file_tools.py`）
- `ReadTool/WriteTool/EditTool` 均持有 `workspace_dir`，所有路径相对工作区，防越界。
- 设计理由：最小可用文件操作 + 路径沙箱，支撑代码/文档类任务。

### 6.3 Bash 工具（`tools/bash_tool.py`）
- 在 `cwd=workspace_dir` 下执行命令；由配置 `enable_bash` 控制是否启用。
- 设计理由：提供通用自动化能力，但受工作区限制，降低风险。

### 6.4 记忆工具（`tools/note_tool.py`）
- `record_note` / `recall_notes`，操作 `.agent_memory.json`；测试用例 `tests/test_note_tool.py` 验证持久化。

### 6.5 工具注册与暴露
- `tools/__init__.py` 汇总导出；CLI 初始化阶段构建工具列表传给 Agent。

### 6.6 Claude Skills（`skills/` 子模块）
- SKILL.md 声明 → Loader 解析为 Tool；通过 `git submodule update --init --recursive` 拉取。
- 设计理由：声明式扩展，无需写 Python，快速获得 15+ 专业技能。

### 6.7 MCP 工具（`load_mcp_tools_async`）
- 入口：`cli.py` 初始化工具时，如 `config.tools.enable_mcp` 为真：
```python
mcp_config_path = Config.find_config_file(config.tools.mcp_config_path)
mcp_tools = await load_mcp_tools_async(str(mcp_config_path))
tools.extend(mcp_tools)
```
- `mcp.json` 描述服务器命令/参数/env；找不到文件会告警不致命。
- 设计理由：把外部服务以 Tool 形式挂入统一分发口，协议解耦、可选加载。

## 7. 工作区与安全边界（配置与 CLI）
- 配置解析：`Config.find_config_file` 按优先级查 `config.yaml`：当前目录 `mini_agent/config/` → `~/.mini-agent/config/` → 包内默认。
- `workspace_dir` 解析：CLI `--workspace` 优先；未提供则用配置或当前目录；不存在则创建。
- 工具与 Agent 均拿到绝对工作区路径，限制文件/命令操作范围；记忆文件 `.agent_memory.json`、日志也放此处。
- 设计理由：显式边界 + 多层回退路径，兼容快速安装与开发模式；沙箱化避免误操作宿主文件。

## 8. 日志与可观察性
- 每步记录：请求体、响应、工具调用、耗时、Token 计数、step 序号。  
- 失败重试：记录重试次数与原因。  
- 目的：回放问题、评估 Token/工具成本。

## 9. 设计/实现蓝图（带源码对应点）
1) **Tool 抽象与注册表**：照 `tools/base.py`；先实现 `Read/Write/Edit/Bash/Note`（`file_tools.py`、`bash_tool.py`、`note_tool.py`），全部接受 `workspace_dir`。
2) **LLMClient**：接口参考 `Agent` 调用的 `generate(messages, tools)`；实现 Anthropic 兼容格式 + RetryConfig（见 `cli.py` 用法）。
3) **Agent.run**：照 `agent.py` 流程，含 `_summarize_messages`、`_estimate_tokens`、工具分发与终止条件。
4) **上下文控制**：复制“保用户、压 Agent”的摘要策略；tiktoken 计数 + fallback。
5) **持久记忆**：JSON 文件 + Note 工具，路径在工作区。
6) **技能与 MCP**：Skills Loader 解析 SKILL.md；`load_mcp_tools_async` 按 `mcp.json` 动态挂载。
7) **CLI/配置**：`Config.find_config_file` 多层查找，`--workspace` 覆盖；启动时创建工作区。
8) **日志/统计**：仿 `AgentLogger` 记录请求/响应/工具调用/Token/步数。
9) **测试**：单测工具与摘要函数；集成测（mock LLM）；冒烟（CLI + 简单任务）。

## 10. 你可以直接使用的最小代码轮廓（伪代码）
```python
class Tool:
    def __init__(self, name, description, parameters): ...
    def execute(self, args, ctx): ...

class LLMClient:
    def send(self, messages, tools, stream=False):
        # 格式化 -> 调用 API -> 处理 tool_calls -> 返回 response 对象
        ...

class Agent:
    def __init__(self, llm, tools, max_steps, summarizer, tokenizer, workspace_dir):
        ...
    def run(self, task):
        history = [{"role": "user", "content": task}]
        for _ in range(self.max_steps):
            history = maybe_summarize(history, self.tokenizer, self.summarizer)
            resp = self.llm.send(history, tools=self.tools)
            if not resp.tool_calls:
                return resp.content
            results = dispatch_tools(resp.tool_calls, self.tools, ctx={"workspace_dir": self.workspace_dir})
            history.append({"role": "assistant", "content": resp.content, "tool_results": results})
        raise RuntimeError("max steps reached")
```

## 11. 复习要点清单
- 有且只有一个主循环，状态机简单可回放。  
- Tool 抽象统一，所有资源访问都在工作区内。  
- 上下文控制 = Token 计数 + 必要的摘要（保用户、压 Agent）。  
- 持久记忆与临时上下文分开：长时信息进 JSON，短时留在消息历史。  
- LLM 客户端职责单一，业务无关。  
- 技能包/MCP 都只是 Tool 来源，接口一致即可。  
- 日志要详：请求、响应、tool 调用、Token、步数，方便调试和成本分析。
