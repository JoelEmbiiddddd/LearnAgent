const test = require("node:test");
const assert = require("node:assert");
const { createRenderer, extractTitle } = require("../src/server");

test("createRenderer 能渲染标题", () => {
  const renderer = createRenderer();
  const html = renderer.render("# Hello World");
  assert.match(html, /<h1.*?>Hello World/);
});

test("extractTitle 识别首个标题", () => {
  const title = extractTitle("# Title\n\nContent");
  assert.strictEqual(title, "Title");
});
