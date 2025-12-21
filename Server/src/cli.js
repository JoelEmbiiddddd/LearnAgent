#!/usr/bin/env node
const { Command } = require("commander");
const open = require("open");
const { resolveConfig, startServer } = require("./server");

function parsePort(value) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    throw new Error("端口必须为数字。");
  }
  return parsed;
}

function parseArgs(argv) {
  const program = new Command();
  program
    .name("md-reader")
    .argument("[file]", "Markdown 文件路径")
    .option("-f, --file <path>", "Markdown 文件路径")
    .option("-r, --root <path>", "根目录，用于构建文件列表")
    .option("--host <host>", "监听地址", "127.0.0.1")
    .option("-p, --port <port>", "监听端口", parsePort, 3000)
    .option("--no-open", "启动后不自动打开浏览器")
    .exitOverride();

  program.parse(argv);

  const options = program.opts();
  return {
    file: options.file || program.args[0],
    root: options.root,
    host: options.host,
    port: options.port,
    open: options.open,
  };
}

async function run() {
  try {
    const config = resolveConfig(parseArgs(process.argv));
    const { url } = await startServer(config);

    console.log("Markdown Reader 已启动");
    console.log(`Root: ${config.rootDir}`);
    console.log(`入口文件: ${config.entryRel}`);
    console.log(`访问地址: ${url}`);

    if (config.open) {
      await open(url);
    }
  } catch (error) {
    console.error(`启动失败: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  run();
}

module.exports = { parseArgs, run };
