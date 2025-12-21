    # 测试策略与用例索引

    ## 快速运行
    ```bash
    # File: README.md | Lines: 268-273 | Description: Test commands
    # Run all tests
    pytest tests/ -v

    # Run core functionality tests
    pytest tests/test_agent.py tests/test_note_tool.py -v
    ```

    ## 测试覆盖声明（README）
    README 对测试类型做了分类说明，可作为测试范围的高层索引。

    ```markdown
    # File: README.md | Lines: 263-280 | Description: Test coverage summary
    The project includes comprehensive test cases covering unit tests, functional tests, and integration tests.

    ### Test Coverage

    - ✅ **Unit Tests** - Tool classes, LLM client
    - ✅ **Functional Tests** - Session Note Tool, MCP loading
    - ✅ **Integration Tests** - Agent end-to-end execution
    - ✅ **External Services** - Git MCP Server loading
    ```

    ## 测试前置条件
    部分测试依赖 `mini_agent/config/config.yaml` 与有效 API Key。

    ```python
    # File: tests/test_agent.py | Lines: 20-40 | Description: Config loading in tests
    # Load config
    config_path = Path("mini_agent/config/config.yaml")
    config = Config.from_yaml(config_path)

    # Create temp workspace
    with tempfile.TemporaryDirectory() as workspace_dir:
        print(f"Using workspace: {workspace_dir}")

        # Load system prompt (Agent will auto-inject workspace info)
        system_prompt_path = Path("mini_agent/config/system_prompt.md")
        if system_prompt_path.exists():
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            system_prompt = "You are a helpful AI assistant that can use tools."

        # Initialize LLM client
        llm_client = LLMClient(
            api_key=config.llm.api_key,
            api_base=config.llm.api_base,
            model=config.llm.model,
        )
    ```

    ```python
    # File: tests/test_integration.py | Lines: 29-39 | Description: API key check in integration tests
    # Load configuration
    config_path = Path("mini_agent/config/config.yaml")
    if not config_path.exists():
        pytest.skip("config.yaml not found")

    config = Config.from_yaml(config_path)

    # Check API key
    if not config.llm.api_key or config.llm.api_key == "YOUR_MINIMAX_API_KEY_HERE":
        pytest.skip("API key not configured")
    ```

    ## 关键测试模块（示例）
    以下测试文件已在仓库中提供，描述了核心能力：

    ```python
    # File: tests/test_bash_tool.py | Lines: 10-21 | Description: Bash tool foreground command test
    @pytest.mark.asyncio
    async def test_foreground_command():
        """Test executing a simple foreground command."""
        print("
=== Testing Foreground Command ===")

        bash_tool = BashTool()
        result = await bash_tool.execute(command="echo 'Hello from foreground'")

        assert result.success
        assert "Hello from foreground" in result.stdout
        assert result.exit_code == 0
        print(f"Output: {result.content}")
    ```

    ```python
    # File: tests/test_mcp.py | Lines: 20-38 | Description: MCP tools loading test
    @pytest.mark.asyncio
    async def test_mcp_tools_loading():
        """Test loading MCP tools from mcp.json."""
        print("
=== Testing MCP Tool Loading ===")

        try:
            # Load MCP tools
            tools = await load_mcp_tools_async("mini_agent/config/mcp.json")

            print(f"Loaded {len(tools)} MCP tools")

            # Display loaded tools
            if tools:
                for tool in tools:
                    desc = tool.description[:60] if len(tool.description) > 60 else tool.description
                    print(f"  - {tool.name}: {desc}")

            # Test should pass even if no tools loaded (e.g., no mcp.json or no Node.js)
            assert isinstance(tools, list), "Should return a list of tools"
            print("✅ MCP tools loading test passed")
    ```

    ```python
    # File: tests/test_skill_loader.py | Lines: 16-35 | Description: Skill loader test
    def create_test_skill(skill_dir: Path, name: str, description: str, content: str):
        """Create a test skill"""
        skill_file = skill_dir / "SKILL.md"
        skill_content = f"""---
    name: {name}
    description: {description}
    ---

    {content}
    """
        skill_file.write_text(skill_content, encoding="utf-8")


    def test_load_valid_skill():
        """Test loading a valid skill"""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
    ```

    ```python
    # File: tests/test_agent.py | Lines: 50-57 | Description: Agent instantiation in tests
    # Create agent
    agent = Agent(
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        max_steps=10,  # Limit steps for testing
        workspace_dir=workspace_dir,
    )
    ```

    ## 其他测试
    tests/ 目录包含更多单元与集成测试（例如 test_llm.py、test_terminal_utils.py 等），可按需扩展覆盖面。
