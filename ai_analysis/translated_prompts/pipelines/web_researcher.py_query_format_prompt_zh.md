# 提示词翻译文档

## 元信息
- 原文件位置: `pipelines/web_researcher.py:20`
- 变量名称: `WebSearchQuery.format()`
- 功能模块: Web 搜索查询格式化
- 调用场景: `BasePipeline` 在执行前将查询对象格式化为字符串提示词

## 中文翻译
Web 搜索查询：{self.prompt}
请提供完整的网页搜索工作流

## 关键参数
- `{self.prompt}`

## 相关代码上下文
该模板在 `pipelines/web_researcher.py` 的 `WebSearchQuery.format()` 中定义，用于生成传入 LLM 的查询文本。
