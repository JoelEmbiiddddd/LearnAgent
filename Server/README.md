# Markdown Reader Web

本地 Markdown 阅读器，提供 CLI 启动方式并自动打开浏览器页面，样式参考 codeviewx。

## 环境要求
- Node.js 18+
- npm 9+

## 安装
```bash
cd /home/work/LearnAgent/Server
npm install
```

## 使用方式
```bash
# 读取指定文件
npm start -- --file /path/to/file.md

# 读取目录（自动选择 README.md 或首个 Markdown 文件）
npm start -- --root /path/to/dir

# 自定义端口与地址
npm start -- --file /path/to/file.md --host 0.0.0.0 --port 4100

# 关闭自动打开浏览器
npm start -- --file /path/to/file.md --no-open
```

## CLI 参数
- `file`：Markdown 文件路径（位置参数或 `--file`）
- `--root`：根目录，用于构建文件列表
- `--host`：监听地址（默认 `127.0.0.1`）
- `--port`：监听端口（默认 `3000`）
- `--no-open`：启动后不自动打开浏览器

## 说明
- 页面仅面向本地单用户使用，不包含鉴权或多用户逻辑。
- 文件列表目前仅扫描根目录下的 Markdown 文件。

---
日期：2025-12-21  
执行者：Codex
