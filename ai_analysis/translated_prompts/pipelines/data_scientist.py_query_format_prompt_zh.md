# 提示词翻译文档

## 元信息
- 原文件位置: `pipelines/data_scientist.py:20`
- 变量名称: `DataScienceQuery.format()`
- 功能模块: 数据科学查询格式化
- 调用场景: `BasePipeline` 在执行前将查询对象格式化为字符串提示词

## 中文翻译
任务：{self.prompt}
数据集路径：{self.data_path}
请提供完整的数据科学工作流

## 关键参数
- `{self.prompt}`
- `{self.data_path}`

## 相关代码上下文
该模板在 `pipelines/data_scientist.py` 的 `DataScienceQuery.format()` 中定义，用于生成传入 LLM 的查询文本。
