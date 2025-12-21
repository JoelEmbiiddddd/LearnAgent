const fs = require("fs");
const path = require("path");
const express = require("express");
const MarkdownIt = require("markdown-it");
const markdownItAnchor = require("markdown-it-anchor");

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 3000;
const README_NAME = "readme.md";

function createRenderer() {
  return new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
  }).use(markdownItAnchor, {
    permalink: markdownItAnchor.permalink.ariaHidden({
      placement: "after",
      class: "heading-anchor",
    }),
  });
}

function extractTitle(markdown) {
  const lines = markdown.split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("#")) {
      const title = trimmed.replace(/^#+/, "").trim();
      if (title) {
        return title;
      }
    }
  }
  return null;
}

function getMarkdownTitle(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    return extractTitle(content);
  } catch (error) {
    return null;
  }
}

function listMarkdownFiles(rootDir, activeRelPath) {
  if (!fs.existsSync(rootDir)) {
    return [];
  }

  const entries = fs.readdirSync(rootDir, { withFileTypes: true });
  const files = entries
    .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".md"))
    .map((entry) => {
      const relPath = entry.name;
      const absPath = path.join(rootDir, entry.name);
      const displayName =
        entry.name.toLowerCase() === README_NAME
          ? "README"
          : getMarkdownTitle(absPath) || entry.name.replace(/\.md$/i, "");

      return {
        name: entry.name,
        displayName,
        relPath,
        active: relPath === activeRelPath,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name, "en"));

  return files;
}

function resolveFilePath(rootDir, relPath) {
  const normalized = relPath ? relPath.replace(/\\/g, "/") : "";
  const candidate = path.resolve(rootDir, normalized);
  const relative = path.relative(rootDir, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    return null;
  }
  return candidate;
}

function findDefaultEntry(rootDir) {
  const entries = fs.readdirSync(rootDir, { withFileTypes: true });
  const markdownFiles = entries
    .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".md"))
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b, "en"));

  const readme = markdownFiles.find(
    (name) => name.toLowerCase() === README_NAME
  );
  if (readme) {
    return path.join(rootDir, readme);
  }

  if (markdownFiles.length === 0) {
    return null;
  }

  return path.join(rootDir, markdownFiles[0]);
}

function resolveConfig({ file, root, host, port, open }) {
  const resolvedHost = host || DEFAULT_HOST;
  const resolvedPort = Number.isFinite(Number(port)) ? Number(port) : DEFAULT_PORT;

  const rootDir = root ? path.resolve(root) : null;
  const entryPath = file ? path.resolve(file) : null;
  const finalRoot = rootDir || (entryPath ? path.dirname(entryPath) : process.cwd());

  if (!fs.existsSync(finalRoot) || !fs.statSync(finalRoot).isDirectory()) {
    throw new Error(`Root 目录不存在或不可访问: ${finalRoot}`);
  }

  let finalEntry = entryPath;
  if (finalEntry) {
    const rel = path.relative(finalRoot, finalEntry);
    if (rel.startsWith("..") || path.isAbsolute(rel)) {
      throw new Error("Markdown 文件必须位于 root 目录中。");
    }
  } else {
    finalEntry = findDefaultEntry(finalRoot);
  }

  if (!finalEntry) {
    throw new Error("未找到可渲染的 Markdown 文件。");
  }

  const entryRel = path.relative(finalRoot, finalEntry).replace(/\\/g, "/");

  return {
    rootDir: finalRoot,
    entryPath: finalEntry,
    entryRel,
    host: resolvedHost,
    port: resolvedPort,
    open: open !== false,
  };
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderPage({ title, markdownHtml, fileTree, rootDir, activeRel }) {
  const navItems = fileTree
    .map((file) => {
      const activeClass = file.active ? " file-item--active" : "";
      const href = `/view?file=${encodeURIComponent(file.relPath)}`;
      return `<a class="file-item${activeClass}" href="${href}">${escapeHtml(
        file.displayName
      )}</a>`;
    })
    .join("");

  const headerTitle = title || activeRel;
  const safeRoot = escapeHtml(rootDir);
  const safeFile = escapeHtml(activeRel);

  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(headerTitle)}</title>
    <link rel="stylesheet" href="/assets/css/styles.css" />
    <link rel="stylesheet" href="/assets/css/typo.css" />
  </head>
  <body>
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-title">Markdown Reader</div>
          <div class="brand-subtitle">本地阅读器</div>
        </div>
        <div class="sidebar-section">
          <div class="sidebar-label">Root</div>
          <div class="sidebar-path">${safeRoot}</div>
        </div>
        <nav class="file-list">
          ${navItems || '<div class="file-empty">未发现 Markdown 文件</div>'}
        </nav>
      </aside>
      <main class="content">
        <header class="content-header">
          <div class="title-group">
            <h1>${escapeHtml(headerTitle)}</h1>
            <div class="content-path">${safeFile}</div>
          </div>
        </header>
        <article class="markdown typo">
          ${markdownHtml}
        </article>
      </main>
    </div>
  </body>
</html>`;
}

function renderErrorPage(message) {
  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Markdown Reader Error</title>
    <link rel="stylesheet" href="/assets/css/styles.css" />
  </head>
  <body>
    <div class="error-page">
      <h1>加载失败</h1>
      <p>${escapeHtml(message)}</p>
    </div>
  </body>
</html>`;
}

function createApp({ rootDir, entryRel }) {
  const app = express();
  const renderer = createRenderer();
  const staticDir = path.join(__dirname, "..", "public");

  app.use("/assets", express.static(staticDir));

  app.get("/", (req, res) => {
    res.redirect(`/view?file=${encodeURIComponent(entryRel)}`);
  });

  app.get("/view", (req, res) => {
    const target = typeof req.query.file === "string" ? req.query.file : entryRel;
    const resolved = resolveFilePath(rootDir, target);

    if (!resolved || !fs.existsSync(resolved)) {
      res.status(404).send(renderErrorPage(`文件不存在: ${target}`));
      return;
    }

    const markdown = fs.readFileSync(resolved, "utf8");
    const html = renderer.render(markdown);
    const title = extractTitle(markdown) || path.basename(target);
    const fileTree = listMarkdownFiles(rootDir, target);

    res.send(
      renderPage({
        title,
        markdownHtml: html,
        fileTree,
        rootDir,
        activeRel: target,
      })
    );
  });

  return app;
}

function startServer({ rootDir, entryRel, host, port }) {
  const app = createApp({ rootDir, entryRel });
  return new Promise((resolve, reject) => {
    const server = app.listen(port, host, () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        reject(new Error("无法获取服务器地址。"));
        return;
      }
      const url = `http://${host}:${address.port}/`;
      resolve({ server, url });
    });
  });
}

module.exports = {
  createRenderer,
  extractTitle,
  findDefaultEntry,
  listMarkdownFiles,
  renderPage,
  resolveConfig,
  resolveFilePath,
  startServer,
};
