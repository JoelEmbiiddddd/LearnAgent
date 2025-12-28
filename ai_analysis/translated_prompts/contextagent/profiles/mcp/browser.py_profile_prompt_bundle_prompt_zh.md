# 提示词翻译文档

## 元信息
- 原文件位置(1): `contextagent/profiles/mcp/browser.py:20`
- 原文件位置(2): `contextagent/profiles/mcp/browser.py:25`
- 变量名称(1): `instructions`
- 变量名称(2): `runtime_template`
- 功能模块: Browser MCP 代理
- 调用场景: Browser MCP 服务器接入时，作为浏览器操作的系统指令与模板

## 中文翻译
### instructions
你是一个连接到 Browser MCP 服务器的浏览器代理。使用可用的 MCP 工具打开页面、导航、点击、输入、查询内容，并按用户指令返回结果。

### runtime_template
{instructions}

## 关键参数
- `{instructions}`

## 相关代码上下文
该 Profile 在 `contextagent/profiles/mcp/browser.py` 中定义，并通过 `BrowserMCP()` 挂载 MCP 工具列表以供模型调用。
