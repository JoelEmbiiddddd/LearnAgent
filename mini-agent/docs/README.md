# Mini-Agent 技术文档

## 文档结构
- README.md - 本文件，总览与导航
- 01-overview.md - 技术栈、目录结构、入口点
- 02-quickstart.md - 快速开始与配置路径
- 03-architecture.md - 架构设计与组件关系
- 04-core-mechanisms.md - 核心机制（详细流程）
- 05-data-models.md - 配置与数据模型
- 06-api-reference.md - Python API 与 CLI 参考
- 07-development-guide.md - 开发与扩展指南
- 08-testing.md - 测试策略与用例索引
- 09-skills.md - Skills 子模块与加载机制
- 10-deepwiki-backup.md - DeepWiki 译文备份（含待确认标注）
- 11-end-to-end-flow.md - 端到端数据流与执行链路
- 12-tools-design.md - 内置工具设计与数据流

## 文档元信息
- 生成时间: 2025-12-21 09:15:29 +0800
- 分析范围: 379 个文件, 155902 行（排除 .git/node_modules/venv/__pycache__ 等）
- 工作目录: /home/work/learn/Mini-Agent
- 输出目录: /home/work/learn/Mini-Agent/docs
- 主要技术栈来源: pyproject.toml

## 入口与命令
- CLI 入口: mini-agent
- ACP 入口: mini-agent-acp

```toml
# File: pyproject.toml | Lines: 27-29 | Description: CLI entry points
[project.scripts]
mini-agent = "mini_agent.cli:main"
mini-agent-acp = "mini_agent.acp.server:main"
```

## 阅读顺序建议
1. [01-overview.md](01-overview.md)
2. [02-quickstart.md](02-quickstart.md)
3. [03-architecture.md](03-architecture.md)
4. [04-core-mechanisms.md](04-core-mechanisms.md)
5. [05-data-models.md](05-data-models.md)
6. [06-api-reference.md](06-api-reference.md)
7. [07-development-guide.md](07-development-guide.md)
8. [08-testing.md](08-testing.md)
9. [09-skills.md](09-skills.md)
10. [10-deepwiki-backup.md](10-deepwiki-backup.md)
11. [11-end-to-end-flow.md](11-end-to-end-flow.md)
12. [12-tools-design.md](12-tools-design.md)

## 现有项目文档
- [README.md](../README.md)
- [README_CN.md](../README_CN.md)
- [docs/DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- [docs/DEVELOPMENT_GUIDE_CN.md](DEVELOPMENT_GUIDE_CN.md)
- [docs/PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
- [docs/PRODUCTION_GUIDE_CN.md](PRODUCTION_GUIDE_CN.md)
- [examples/README.md](../examples/README.md)
- [examples/README_CN.md](../examples/README_CN.md)

## 说明
- 所有结论仅基于本仓库文件与代码片段。
- 代码片段均包含路径与行号，便于定位。
- Mermaid 图表位于代码块内，标签使用英文以满足代码块约束。
