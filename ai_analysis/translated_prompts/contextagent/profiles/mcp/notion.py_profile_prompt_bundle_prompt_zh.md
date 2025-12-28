# 提示词翻译文档

## 元信息
- 原文件位置(1): `contextagent/profiles/mcp/notion.py:8`
- 原文件位置(2): `contextagent/profiles/mcp/notion.py:9`
- 变量名称(1): `instructions`
- 变量名称(2): `runtime_template`
- 功能模块: Notion MCP 代理
- 调用场景: 通过 MCP 服务器执行 Notion 操作时，作为系统指令与模板

## 中文翻译
### instructions
你是一个 Notion 代理。你的任务是按照提供的指令与 Notion MCP 服务器交互。

### runtime_template
{instructions}

## 关键参数
- `{instructions}`

## 相关代码上下文
该 Profile 在 `contextagent/profiles/mcp/notion.py` 中定义，运行时将 `instructions` 原样作为模板输出。
