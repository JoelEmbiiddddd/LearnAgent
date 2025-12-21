# 内置工具设计与数据流

## 总览
内置工具由配置开关控制并在启动时完成注册。整体目标是：
- 用统一的 Tool 接口规范“能力入口”。
- 将 workspace 相关的工具与无关工具分离，便于复用与隔离。
- 将工具元数据提供给 LLM，允许 LLM 按需调用。

## 工具加载与分层
工具初始化分为“与 workspace 无关”和“与 workspace 强相关”两类。

```python
# File: mini_agent/cli.py | Lines: 211-321 | Description: Tool initialization by config
async def initialize_base_tools(config: Config):
    """Initialize base tools (independent of workspace)

    These tools are loaded from package configuration and don't depend on workspace.
    Note: File tools are now workspace-dependent and initialized in add_workspace_tools()

    Args:
        config: Configuration object

    Returns:
        Tuple of (list of tools, skill loader if skills enabled)
    """

    tools = []
    skill_loader = None

    # 1. Bash tool and Bash Output tool
    if config.tools.enable_bash:
        bash_tool = BashTool()
        tools.append(bash_tool)
        print(f"{Colors.GREEN}✅ Loaded Bash tool{Colors.RESET}")

        bash_output_tool = BashOutputTool()
        tools.append(bash_output_tool)
        print(f"{Colors.GREEN}✅ Loaded Bash Output tool{Colors.RESET}")

        bash_kill_tool = BashKillTool()
        tools.append(bash_kill_tool)
        print(f"{Colors.GREEN}✅ Loaded Bash Kill tool{Colors.RESET}")

    # 3. Claude Skills (loaded from package directory)
    if config.tools.enable_skills:
        print(f"{Colors.BRIGHT_CYAN}Loading Claude Skills...{Colors.RESET}")
        try:
            # Resolve skills directory with priority search
            skills_dir = config.tools.skills_dir
            if not Path(skills_dir).is_absolute():
                # Search in priority order:
                # 1. Current directory (dev mode: ./skills or ./mini_agent/skills)
                # 2. Package directory (installed: site-packages/mini_agent/skills)
                search_paths = [
                    Path(skills_dir),  # ./skills for backward compatibility
                    Path("mini_agent") / skills_dir,  # ./mini_agent/skills
                    Config.get_package_dir() / skills_dir,  # site-packages/mini_agent/skills
                ]

                # Find first existing path
                for path in search_paths:
                    if path.exists():
                        skills_dir = str(path.resolve())
                        break

            skill_tools, skill_loader = create_skill_tools(skills_dir)
            if skill_tools:
                tools.extend(skill_tools)
                print(f"{Colors.GREEN}✅ Loaded Skill tool (get_skill){Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️  No available Skills found{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Failed to load Skills: {e}{Colors.RESET}")

    # 4. MCP tools (loaded with priority search)
    if config.tools.enable_mcp:
        print(f"{Colors.BRIGHT_CYAN}Loading MCP tools...{Colors.RESET}")
        try:
            # Use priority search for mcp.json
            mcp_config_path = Config.find_config_file(config.tools.mcp_config_path)
            if mcp_config_path:
                mcp_tools = await load_mcp_tools_async(str(mcp_config_path))
                if mcp_tools:
                    tools.extend(mcp_tools)
                    print(f"{Colors.GREEN}✅ Loaded {len(mcp_tools)} MCP tools (from: {mcp_config_path}){Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️  No available MCP tools found{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️  MCP config file not found: {config.tools.mcp_config_path}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Failed to load MCP tools: {e}{Colors.RESET}")

    print()  # Empty line separator
    return tools, skill_loader


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

### 设计动机与收益
- **分层加载**：将 Bash/Skills/MCP 放到 base tools，文件与记忆工具放到 workspace tools，便于在不同 workspace 下复用核心能力。
- **容错与渐进启用**：MCP/Skills 加载失败仅告警，不中断主流程，便于渐进启用或缺省运行。
- **按配置裁剪能力**：通过 `enable_*` 开关控制工具集合，保证能力可控。

## 工具与 LLM 交互的统一契约
工具通过 `Tool` 抽象统一接口与参数 schema，LLM 通过 provider 的转换函数获取工具 schema。

```python
# File: mini_agent/tools/base.py | Lines: 16-44 | Description: Tool schema contract
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

```python
# File: mini_agent/llm/anthropic_client.py | Lines: 83-110 | Description: Tool schema conversion
 def _convert_tools(self, tools: list[Any]) -> list[dict[str, Any]]:
     """Convert tools to Anthropic format.

     Anthropic tool format:
     {
         "name": "tool_name",
         "description": "Tool description",
         "input_schema": {
             "type": "object",
             "properties": {...},
             "required": [...]
         }
     }

     Args:
         tools: List of Tool objects or dicts

     Returns:
         List of tools in Anthropic dict format
     """
     result = []
     for tool in tools:
         if isinstance(tool, dict):
             result.append(tool)
         elif hasattr(tool, "to_schema"):
             # Tool object with to_schema method
             result.append(tool.to_schema())
         else:
             raise TypeError(f"Unsupported tool type: {type(tool)}")
     return result
```

### 设计动机与收益
- **统一参数契约**：`parameters` + `to_schema` 将工具输入结构化，降低 LLM 调用歧义。
- **解耦 provider 细节**：由 LLM client 负责工具 schema 的 provider 适配，Tool 实现保持稳定。

## 文件工具（ReadTool / WriteTool / EditTool）
### ReadTool
```python
# File: mini_agent/tools/file_tools.py | Lines: 66-149 | Description: ReadTool behavior
class ReadTool(Tool):
    """Read file content."""

    def __init__(self, workspace_dir: str = "."):
        """Initialize ReadTool with workspace directory.

        Args:
            workspace_dir: Base directory for resolving relative paths
        """
        self.workspace_dir = Path(workspace_dir).absolute()

    async def execute(self, path: str, offset: int | None = None, limit: int | None = None) -> ToolResult:
        """Execute read file."""
        try:
            file_path = Path(path)
            # Resolve relative paths relative to workspace_dir
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}",
                )

            # Read file content with line numbers
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply offset and limit
            start = (offset - 1) if offset else 0
            end = (start + limit) if limit else len(lines)
            if start < 0:
                start = 0
            if end > len(lines):
                end = len(lines)

            selected_lines = lines[start:end]

            # Format with line numbers (1-indexed)
            numbered_lines = []
            for i, line in enumerate(selected_lines, start=start + 1):
                # Remove trailing newline for formatting
                line_content = line.rstrip("\n")
                numbered_lines.append(f"{i:6d}|{line_content}")

            content = "\n".join(numbered_lines)

            # Apply token truncation if needed
            max_tokens = 32000
            content = truncate_text_by_tokens(content, max_tokens)

            return ToolResult(success=True, content=content)
```

**设计动机与收益**
- **workspace 作为相对路径基准**：保证相对路径解析一致。
- **带行号输出**：便于精确定位与后续编辑。
- **offset/limit + truncation**：支持大文件分段读取，降低 token 成本。

### WriteTool
```python
# File: mini_agent/tools/file_tools.py | Lines: 155-207 | Description: WriteTool behavior
class WriteTool(Tool):
    """Write content to a file."""

    def __init__(self, workspace_dir: str = "."):
        """Initialize WriteTool with workspace directory.

        Args:
            workspace_dir: Base directory for resolving relative paths
        """
        self.workspace_dir = Path(workspace_dir).absolute()

    async def execute(self, path: str, content: str) -> ToolResult:
        """Execute write file."""
        try:
            file_path = Path(path)
            # Resolve relative paths relative to workspace_dir
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, content=f"Successfully wrote to {file_path}")
```

**设计动机与收益**
- **显式覆盖语义**：写入即覆盖，避免误以为是增量写。
- **自动创建目录**：降低生成新文件时的环境要求。

### EditTool
```python
# File: mini_agent/tools/file_tools.py | Lines: 212-283 | Description: EditTool behavior
class EditTool(Tool):
    """Edit file by replacing text."""

    def __init__(self, workspace_dir: str = "."):
        """Initialize EditTool with workspace directory.

        Args:
            workspace_dir: Base directory for resolving relative paths
        """
        self.workspace_dir = Path(workspace_dir).absolute()

    async def execute(self, path: str, old_str: str, new_str: str) -> ToolResult:
        """Execute edit file."""
        try:
            file_path = Path(path)
            # Resolve relative paths relative to workspace_dir
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}",
                )

            content = file_path.read_text(encoding="utf-8")

            if old_str not in content:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Text not found in file: {old_str}",
                )

            new_content = content.replace(old_str, new_str)
            file_path.write_text(new_content, encoding="utf-8")

            return ToolResult(success=True, content=f"Successfully edited {file_path}")
```

**设计动机与收益**
- **精确替换**：依赖 old_str 精确匹配，避免模糊修改导致意外变更。
- **与 ReadTool 配合**：先读取后替换，形成“可审阅的变更闭环”。

## Bash 工具族（BashTool / BashOutputTool / BashKillTool）
### BashTool
```python
# File: mini_agent/tools/bash_tool.py | Lines: 217-366 | Description: BashTool execution
class BashTool(Tool):
    """Execute shell commands in foreground or background.
    
    Automatically detects OS and uses appropriate shell:
    - Windows: PowerShell
    - Unix/Linux/macOS: bash
    """

    def __init__(self):
        """Initialize BashTool with OS-specific shell detection."""
        self.is_windows = platform.system() == "Windows"
        self.shell_name = "PowerShell" if self.is_windows else "bash"

    async def execute(
        self,
        command: str,
        timeout: int = 120,
        run_in_background: bool = False,
    ) -> ToolResult:
        """Execute shell command with optional background execution.

        Args:
            command: The shell command to execute
            timeout: Timeout in seconds (default: 120, max: 600)
            run_in_background: Set true to run command in background

        Returns:
            BashExecutionResult with command output and status
        """

        try:
            # Validate timeout
            if timeout > 600:
                timeout = 600
            elif timeout < 1:
                timeout = 120

            # Prepare shell-specific command execution
            if self.is_windows:
                # Windows: Use PowerShell with appropriate encoding
                shell_cmd = ["powershell.exe", "-NoProfile", "-Command", command]
            else:
                # Unix/Linux/macOS: Use bash
                shell_cmd = command

            if run_in_background:
                # Background execution: Create isolated process
                bash_id = str(uuid.uuid4())[:8]

                # Start background process with combined stdout/stderr
                if self.is_windows:
                    process = await asyncio.create_subprocess_exec(
                        *shell_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                else:
                    process = await asyncio.create_subprocess_shell(
                        shell_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )

                # Create background shell and add to manager
                bg_shell = BackgroundShell(bash_id=bash_id, command=command, process=process, start_time=time.time())
                BackgroundShellManager.add(bg_shell)

                # Start monitoring task
                await BackgroundShellManager.start_monitor(bash_id)

                # Return immediately with bash_id
                message = f"Command started in background. Use bash_output to monitor (bash_id='{bash_id}')."
                formatted_content = f"{message}\n\nCommand: {command}\nBash ID: {bash_id}"

                return BashOutputResult(
                    success=True,
                    content=formatted_content,
                    stdout=f"Background command started with ID: {bash_id}",
                    stderr="",
                    exit_code=0,
                    bash_id=bash_id,
                )
```

**设计动机与收益**
- **前台/后台分流**：短命令前台执行，长命令后台运行，避免阻塞。
- **OS 自动适配**：减少跨平台调用差异。
- **超时保护**：限制前台命令执行时间，降低资源风险。

### BashOutputTool
```python
# File: mini_agent/tools/bash_tool.py | Lines: 430-512 | Description: BashOutputTool behavior
class BashOutputTool(Tool):
    """Retrieve output from background bash shells."""

    @property
    def name(self) -> str:
        return "bash_output"

    @property
    def description(self) -> str:
        return """Retrieves output from a running or completed background bash shell.

        - Takes a bash_id parameter identifying the shell
        - Always returns only new output since the last check
        - Returns stdout and stderr output along with shell status
        - Supports optional regex filtering to show only lines matching a pattern
        - Use this tool when you need to monitor or check the output of a long-running shell
        - Shell IDs can be found using the bash tool with run_in_background=true

        Process status values:
          - "running": Still executing
          - "completed": Finished successfully
          - "failed": Finished with error
          - "terminated": Was terminated
          - "error": Error occurred

        Example: bash_output(bash_id="abc12345")"""
```

**设计动机与收益**
- **可观测性**：通过 bash_id 拉取增量输出，避免一次性拉全量日志。
- **适配长任务**：让后台任务保持可控与可追踪。

### BashKillTool
```python
# File: mini_agent/tools/bash_tool.py | Lines: 524-587 | Description: BashKillTool behavior
class BashKillTool(Tool):
    """Terminate a running background bash shell."""

    @property
    def name(self) -> str:
        return "bash_kill"

    @property
    def description(self) -> str:
        return """Kills a running background bash shell by its ID.

        - Takes a bash_id parameter identifying the shell to kill
        - Attempts graceful termination (SIGTERM) first, then forces (SIGKILL) if needed
        - Returns the final status and any remaining output before termination
        - Cleans up all resources associated with the shell
        - Use this tool when you need to terminate a long-running shell
        - Shell IDs can be found using the bash tool with run_in_background=true

        Example: bash_kill(bash_id="abc12345")"""
```

**设计动机与收益**
- **后台任务可控终止**：避免孤儿进程与资源泄露。
- **统一运维入口**：bash_output + bash_kill 组合实现后台任务生命周期管理。

## Session Note 工具（SessionNoteTool / RecallNoteTool）
```python
# File: mini_agent/tools/note_tool.py | Lines: 82-114 | Description: Persist notes to memory file
    def _save_to_file(self, notes: list):
        """Save notes to file.
        
        Creates parent directory and file if they don't exist (lazy initialization).
        """
        # Ensure parent directory exists when actually saving
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(json.dumps(notes, indent=2, ensure_ascii=False))

    async def execute(self, content: str, category: str = "general") -> ToolResult:
        """Record a session note.

        Args:
            content: The information to record
            category: Category/tag for this note

        Returns:
            ToolResult with success status
        """
        try:
            # Load existing notes
            notes = self._load_from_file()

            # Add new note with timestamp
            note = {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "content": content,
            }
            notes.append(note)

            # Save back to file
            self._save_to_file(notes)
```

```python
# File: mini_agent/tools/note_tool.py | Lines: 163-206 | Description: Recall notes
    async def execute(self, category: str = None) -> ToolResult:
        """Recall session notes.

        Args:
            category: Optional category filter

        Returns:
            ToolResult with notes content
        """
        try:
            if not self.memory_file.exists():
                return ToolResult(
                    success=True,
                    content="No notes recorded yet.",
                )

            notes = json.loads(self.memory_file.read_text())

            if not notes:
                return ToolResult(
                    success=True,
                    content="No notes recorded yet.",
                )

            # Filter by category if specified
            if category:
                notes = [n for n in notes if n.get("category") == category]
                if not notes:
                    return ToolResult(
                        success=True,
                        content=f"No notes found in category: {category}",
                    )

            # Format notes for display
            formatted = []
            for idx, note in enumerate(notes, 1):
                timestamp = note.get("timestamp", "unknown time")
                cat = note.get("category", "general")
                content = note.get("content", "")
                formatted.append(f"{idx}. [{cat}] {content}\n   (recorded at {timestamp})")

            result = "Recorded Notes:\n" + "\n".join(formatted)

            return ToolResult(success=True, content=result)
```

**设计动机与收益**
- **持久化记忆**：把关键信息写入 workspace 的 JSON 文件，跨轮次可复用。
- **延迟创建**：只有真正记录时才创建文件/目录，降低无用副作用。
- **分类检索**：通过 category 过滤，增强可管理性。

## Skills 工具（GetSkillTool）
```python
# File: mini_agent/tools/skill_tool.py | Lines: 13-54 | Description: GetSkillTool behavior
class GetSkillTool(Tool):
    """Tool to get detailed information about a specific skill"""

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "get_skill"

    @property
    def description(self) -> str:
        return "Get complete content and guidance for a specified skill, used for executing specific types of tasks"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill to retrieve (use list_skills to view available skills)",
                }
            },
            "required": ["skill_name"],
        }

    async def execute(self, skill_name: str) -> ToolResult:
        """Get detailed information about specified skill"""
        skill = self.skill_loader.get_skill(skill_name)

        if not skill:
            available = ", ".join(self.skill_loader.list_skills())
            return ToolResult(
                success=False,
                content="",
                error=f"Skill '{skill_name}' does not exist. Available skills: {available}",
            )

        # Return complete skill content
        result = skill.to_prompt()
        return ToolResult(success=True, content=result)
```

**设计动机与收益**
- **按需加载**：避免一次性将所有技能内容灌入上下文。
- **显式错误提示**：找不到 skill 时返回可用列表，降低用户试错成本。

## MCP 工具（动态扩展）
MCP 工具通过配置文件动态加载，属于“运行时可扩展工具”。

```python
# File: mini_agent/cli.py | Lines: 273-283 | Description: MCP tool loading
if config.tools.enable_mcp:
    print(f"{Colors.BRIGHT_CYAN}Loading MCP tools...{Colors.RESET}")
    try:
        # Use priority search for mcp.json
        mcp_config_path = Config.find_config_file(config.tools.mcp_config_path)
        if mcp_config_path:
            mcp_tools = await load_mcp_tools_async(str(mcp_config_path))
            if mcp_tools:
                tools.extend(mcp_tools)
                print(f"{Colors.GREEN}✅ Loaded {len(mcp_tools)} MCP tools (from: {mcp_config_path}){Colors.RESET}")
```

**设计动机与收益**
- **动态扩展能力**：通过 `mcp.json` 扩展外部工具，不侵入核心代码。
- **配置驱动**：工具启用/禁用可在配置层完成，适合分环境裁剪。

## 工具调用的数据流
- LLM 输出 `tool_calls`。
- Agent 解析 `tool_calls`，执行工具并将结果写回 `messages`。
- 下一轮 LLM 继续在“含工具结果的上下文”上推理。

```python
# File: mini_agent/agent.py | Lines: 359-378 | Description: Tool call extraction
# Execute tool calls
for tool_call in response.tool_calls:
    tool_call_id = tool_call.id
    function_name = tool_call.function.name
    arguments = tool_call.function.arguments
```

```python
# File: mini_agent/agent.py | Lines: 404-429 | Description: Tool result append
# Add tool result message
tool_msg = Message(
    role="tool",
    content=result.content if result.success else f"Error: {result.error}",
    tool_call_id=tool_call_id,
    name=function_name,
)
self.messages.append(tool_msg)
```

**设计动机与收益**
- **闭环上下文**：工具输出成为下一轮推理的上下文输入，保证工具结果可被继续使用。
- **一致的错误语义**：失败也写入 messages，LLM 可据此尝试修复或给出解释。
