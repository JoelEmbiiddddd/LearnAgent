const test = require("node:test");
const assert = require("node:assert");
const { parseArgs } = require("../src/cli");

test("parseArgs 支持位置参数文件", () => {
  const result = parseArgs(["node", "cli.js", "docs/readme.md", "--no-open"]);
  assert.strictEqual(result.file, "docs/readme.md");
  assert.strictEqual(result.open, false);
});

test("parseArgs 支持 --file 参数", () => {
  const result = parseArgs([
    "node",
    "cli.js",
    "--file",
    "docs/guide.md",
    "--host",
    "0.0.0.0",
    "--port",
    "4100",
  ]);
  assert.strictEqual(result.file, "docs/guide.md");
  assert.strictEqual(result.host, "0.0.0.0");
  assert.strictEqual(result.port, 4100);
});
