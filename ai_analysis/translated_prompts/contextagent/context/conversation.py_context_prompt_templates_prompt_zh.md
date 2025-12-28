# 提示词翻译文档

## 元信息
- 原文件位置(1): `contextagent/context/conversation.py:35`
- 原文件位置(2): `contextagent/context/conversation.py:243`
- 变量名称(1): `BaseIterationRecord.history_block()`
- 变量名称(2): `ConversationState.format_context_prompt()`
- 功能模块: 上下文拼接与历史记录模板
- 调用场景: 当 Profile 未定义 `runtime_template` 时，使用上下文模板拼接最终提示词

## 中文翻译
### history_block 模板
[迭代 {index}]

<thought>
{observation}
</thought>

<payloads>
{payloads}
</payloads>

<findings>
{findings}
</findings>

### format_context_prompt 模板
[原始查询]
{query}

[前序迭代]
{history}

[当前输入]
{current_input}

## 关键参数
- `{index}`
- `{observation}`
- `{payloads}`
- `{findings}`
- `{query}`
- `{history}`
- `{current_input}`

## 相关代码上下文
这些模板在 `contextagent/context/conversation.py` 中定义，用于将历史、观测与当前输入拼接为最终提示词；真实输出会根据是否存在对应内容而动态省略或追加区块。
