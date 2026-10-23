# 技术陷阱清单

这一页踩过的坑，按出现顺序排列。照着做可以少走一轮。

## 一、Python 环境

`fitz`（PyMuPDF）不在系统 Python 里。用托管环境：

```bash
/Users/mac/.workbuddy-ai/binaries/python/envs/default/bin/python
# 缺包时：
/Users/mac/.workbuddy-ai/binaries/python/envs/default/bin/pip install pymupdf pillow
```

直接跑 `python xxx.py` 会报 `ModuleNotFoundError: fitz`。

## 二、PDF 解析会 segfault

某些 PDF 上，以下调用会让进程直接崩（Exit 139），没有异常可捕获：

- `page.get_text("dict")`
- `page.search_for(...)`

**改用** `page.get_images(full=True)` + `page.get_image_bbox(img)` 定位图片边界，用 `page.get_text("text")` 取文字。这条路径稳定。

## 三、多分图会返回多个 bbox

`get_image_bbox` 是**按嵌入的位图**返回的。一张 6 分图的 Figure 里有 6 张位图，就返回 6 个 bbox，而且它们不覆盖矢量标注（字母 A–G、坐标轴、比例尺）。

结论：**不要指望自动框选**。正确流程：

1. `--detect` 渲染整页 `pageNN.png`（110 dpi 足够看清）。
2. 肉眼看图，记下「图几在第几页、大致范围」。
3. 手写 `crops.json`，用 `--crop` 精确裁。

crop box 单位是 **PDF point（1/72 inch）**，原点在**左上角**，格式 `[page, x0, y0, x1, y1]`，page 从 1 开始。

裁完必须**逐张目视确认**：有没有带进正文文字、有没有切掉子图字母或比例尺。这一步省不得，返工成本高。

## 四、图片体积

参数基准（已验证）：

| 参数 | 值 | 效果 |
|---|---|---|
| dpi | 175 | 屏幕阅读清晰，放大不糊 |
| 最大宽度 | 1150 px | 超过无意义（页面栏宽约 800） |
| JPEG quality | 82 | 6 张图合计约 1.0–1.3 MB |

base64 会让体积**膨胀约 33%**。6 张图内嵌后整页约 1.4 MB，可接受；超过 6 MB 要降 dpi 或 quality（`assemble.py` 会警告）。

## 五、JS 字符串里的引号

在 JS 数据里写英文原句，**不要用直双引号 `"` 包内容再在内容里用 `"`**——会截断字符串。

规则：
- 字符串边界用反引号 `` ` ``（模板字符串），内部可自由使用 `"` 和 `'`。
- 或边界用双引号，内容里的引号改成中文引号 `“”`。

写完跑一次 `node --check`。`verify_page.py --js` 会自动做。

## 六、零宽字符

从 PDF 复制的中文/符号里可能混入 `U+200B`（零宽空格），导致 `data-i="4"` 匹配失败、句子点不动。

生成后用脚本清一遍：`src.replace('\u200b', '')`。

## 七、`<` 和 `>` 被当成标签

原句里有 `At pH > 10`、`<100 nm` 这类内容。直接塞进 `innerHTML` 会被解析成标签，后面的内容全乱。

`render.js` 里已有 `esc()` 对 `tx` 转义。但 `para` 是**故意不转义**的（它含 `<mark>` 标签），所以 `para` 里的 `<` `>` 必须手写成 `&lt;` `&gt;`。

## 八、headless Chrome 的最小宽度

`--window-size=390,1500` 实际渲染宽度约 **485px**，截图却按 390 裁——结果看起来像「横向溢出」，其实是**截图裁切**，不是布局 bug。

诊断方法：注入脚本读 `document.documentElement.scrollWidth` 与 `clientWidth`，相等即无溢出。

要真测窄屏，用 iframe 包一层：

```html
<iframe src="page.html" style="width:390px;height:3000px;border:0"></iframe>
```

`verify_page.py --shot <id> --mobile` 已内置这一层。

## 九、单元 id 没有补零

`id` 是 `u1`、`u2` … `u19`，**不是** `u01`。用 `#u02` 做选择器会静默匹配不到，截图一片空白。

## 十、验证计数会被模板字符串污染

`--dump-dom` 会把 `<script>` 的文本也输出，里面的 `'<section class="unit" id="'+u.id+'"'` 会被误计为一个单元。

正确计数方式：只匹配真实 id，`id="(u\d+)"`。`verify_page.py` 已按此实现。

## 十一、zsh 的 nomatch

`rm -f _verify_*.png` 在没有匹配文件时，zsh 会报 `no matches found` 并**中止整条命令**（含 `&&` 链后面的清理）。

要么先确认存在，要么 `setopt null_glob`，要么逐个列文件名。

## 十二、文案与数据对不上

页面顶部写「12 个单元 / 72 句」，实际数据是 19 / 89——改数据后忘改文案。

生成后固定跑：

```bash
python verify_page.py page.html --dom
```

输出 `rendered units=19 cards=89 nav links=19`，与文案逐项核对。
