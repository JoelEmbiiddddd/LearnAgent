const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { resolveConfig, startServer } = require("../src/server");

test("startServer 可提供渲染页面", async () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "md-reader-"));
  const filePath = path.join(tempDir, "README.md");
  fs.writeFileSync(filePath, "# Smoke Test\n\nHello.");

  const config = resolveConfig({ root: tempDir, host: "127.0.0.1", port: 0 });
  const { server, url } = await startServer(config);

  try {
    const response = await fetch(url);
    const text = await response.text();
    assert.ok(response.ok);
    assert.match(text, /Smoke Test/);
  } finally {
    server.close();
  }
});
