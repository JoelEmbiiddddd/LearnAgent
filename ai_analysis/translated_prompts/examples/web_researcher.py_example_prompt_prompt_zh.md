# 提示词翻译文档

## 元信息
- 原文件位置(1): `examples/web_researcher.py:9` (注释示例)
- 原文件位置(2): `examples/web_researcher.py:10`
- 变量名称(1): `prompt`（注释示例）
- 变量名称(2): `prompt`
- 功能模块: WebSearcher 示例脚本
- 调用场景: 示例运行时作为 WebSearchQuery 的用户输入

## 中文翻译
### 注释示例
当前时间：{current_time}。找出 ACL 2025 的杰出论文，用一句话提取其标题、作者列表、关键词、摘要和网址。

### 实际示例
当前时间：{current_time}。检查网站 https://www.sqlite.org/cli.html 并列出一些功能，每个功能用一句话描述。

## 关键参数
- `{current_time}`

## 相关代码上下文
该提示词在 `examples/web_researcher.py` 中作为示例输入，用于展示 Web 搜索管线的调用方式，其中一条为注释示例。
