# 提示词翻译文档

## 元信息
- 原文件位置: `contextagent/tools/data_tools/image.py:113`
- 变量名称: `prompt`
- 功能模块: image_qa 工具内部默认提示词
- 调用场景: 当未传入 question 时，用于生成图像描述

## 中文翻译
请对这张图片进行详细描述，包括物体、人物、动作、颜色以及可见文字。

## 关键参数
- 无

## 相关代码上下文
该提示词在 `contextagent/tools/data_tools/image.py` 中定义，`image_qa` 工具在 `question` 为空时默认使用该提示词向 Gemini 模型提问。
