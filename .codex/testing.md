# Testing Log

日期：2025-12-21  
执行者：Codex

## 单元测试/冒烟测试/功能测试
命令：
```bash
cd /home/work/LearnAgent/Server
npm test
```

输出摘要：
```
> md-reader-web@0.1.0 test
> node --test

✔ parseArgs 支持位置参数文件 (1.667783ms)
✔ parseArgs 支持 --file 参数 (0.354147ms)
✔ createRenderer 能渲染标题 (3.819594ms)
✔ extractTitle 识别首个标题 (0.352467ms)
✔ startServer 可提供渲染页面 (43.425406ms)
ℹ tests 5
ℹ suites 0
ℹ pass 5
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 194.143905
```

第二次运行（修正 README 识别逻辑后）：
```
> md-reader-web@0.1.0 test
> node --test

✔ parseArgs 支持位置参数文件 (1.57971ms)
✔ parseArgs 支持 --file 参数 (0.332206ms)
✔ createRenderer 能渲染标题 (3.680442ms)
✔ extractTitle 识别首个标题 (0.233215ms)
✔ startServer 可提供渲染页面 (38.715775ms)
ℹ tests 5
ℹ suites 0
ℹ pass 5
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 178.481789
```

## echocodeview Python 测试
命令：
```bash
cd /home/work/LearnAgent
python -m unittest discover -s tests
```

输出摘要：
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.064s

OK
```

第二次运行（修正入口路径校验后）：
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.032s

OK
```

第三次运行（调整 CLI 调用方式后）：
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.031s

OK
```

第四次运行（样式与目录过滤调整后）：
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.029s

OK
```

第五次运行（Mermaid 渲染支持后）：
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.032s

OK
```

第六次运行（目录过滤与 UI 优化后）：
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.031s

OK
```
