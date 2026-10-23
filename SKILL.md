---
name: paper-close-reading
description: "从论文 PDF 生成「以写作为目的」的精读教学网页（单文件 HTML）。当用户提供论文/文献（PDF、docx、网页链接或正文）并要求做精读网页、精读 HTML、逐句分析、学习这篇论文怎么写、拆解句式与论证、双色高亮、把文中图片都带上并解释时使用。产出包含三部分：文章框架与论证主线、逐句四栏精读（语法/逻辑/模板/细节）、写作工具箱，图片以 base64 内嵌。关键词：精读网页、精读 HTML、以写作为目的的精读、逐句拆解、学写作、论文网页、close reading page。注意：若用户要的是「分轮带读、每轮讲一部分等确认」，应改用 lit-deep-reading。"
agent_created: true
---

# 论文精读网页生成（Paper Close Reading Page）

把一篇论文变成**可反复查阅的单文件 HTML**：读者看完不只懂内容，还能提取可复用的句子骨架与论证动作。产物无外部依赖，图片 base64 内嵌，可直接双击打开或分享。

## 何时用 / 何时不用

用：
- 「做网页精读这篇 PDF」「精读 HTML」「学它怎么写」「逐句分析语法和逻辑」「双色高亮」「图片都要带上并解释」。

不用：
- 用户要**对话式带读**（每轮讲一部分、停下等确认）→ 用 `lit-deep-reading`。
- 用户只要摘要或问答，不要网页 → 直接回答。

## 产物形态

```
第一部分 · 框架      s0 阅读方式 → s1 三层问题 → s2 全文骨架 → s3 论证主线
                    → s4 方法论通俗版 → s4b 图版精读 → s5 写作动作
第二部分 · 逐段精读  N 个单元 / M 句，每句四栏
第三部分 · 工具箱    t1 句式库 → t2 引用动词 → t3 hedging → t4 时态
                    → t5 连接词 → t6 自检
```

每节的具体写法与质量线见 `references/page-structure.md`；单元切分与四栏标准见 `references/analysis-framework.md`。

---

## 工作流

### 第 1 步 · 抽取文本与候选图

```bash
python scripts/extract_pdf.py <paper.pdf> --work ./work --detect
```

产出 `work/text.txt`、整页渲染 `work/pageNN.png`、候选 bbox `work/candidates.txt`。

先通读 `text.txt`，确认章节边界（INTRODUCTION / RESULTS / DISCUSSION / METHODS / REFERENCES 的行号），再决定单元划分。

> 不要用 `page.get_text("dict")` 或 `search_for`，某些 PDF 会 segfault。详见 `references/pdf-pitfalls.md`。

### 第 2 步 · 定图并裁图

打开 `pageNN.png` 目视确认每张图的范围，写 `crops.json`：

```json
{"1": [2, 54, 58, 540, 458], "2": [4, 36, 58, 558, 376]}
```

格式 `{"图号": [页码(1起), x0, y0, x1, y1]}`，单位 PDF point，原点左上。

```bash
python scripts/extract_pdf.py <paper.pdf> --work ./work --crop crops.json
```

裁完**逐张看图确认**：没带进正文、没切掉子图字母/比例尺。参数默认 dpi=175、宽≤1150、quality=82。

### 第 3 步 · 写第一部分

复制 `assets/page-template.html` 到 `body.html`，按 `<!-- FILL -->` 提示填写 s0–s5。要点：

- **s1 必须是三层收紧的问题**（不该存在的现象 → 旧解释不够用 → 机制空白），不是平铺背景。
- **s4 每个方法一张 `.mcard`**，固定三段：一句话原理（日常类比）/ 在这篇里回答什么 / 怎么看结果。
- **s5 的六个动作要可执行**，配「如何排除竞争解释」专题表。

### 第 4 步 · 写图版章节

生成 `figsec.html`：`<section id="s4b">` 开头，含 `figindex` 锚点条、证据类型递进表、每图一个 `<figure class="fig">`。

每张图三层，缺一不可：

```html
<div class="fwhat"><b>在证明什么</b>　...</div>
<div class="fhow"><b>怎么看</b>　...</div>
<div class="fwrite"><b>写作提示</b>　...</div>
```

图片用 `data:image/jpeg;base64,...` 内嵌（`extract_pdf.py` 已输出 jpg）。

### 第 5 步 · 写逐句精读数据

参照 `assets/unit-schema.js` 写 `u1.js`、`u2.js`（长文分两半，`UNITS` / `UNITS_B`）。

硬性要求：
- `id` 用 `u1`…`uN`，**不补零**。
- 每句一个 `<span class="sn" data-i="k">`，`k` 从 0 连续，与 `sent[].i` 一一对应。
- 双色高亮：`<mark class="c">` 内容、`<mark class="p">` 句式、`<span class="lc">` 逻辑信号词；总密度 20–35%。
- `para` 里的 `<` `>` 手写成 `&lt;` `&gt;`（该字段不转义）。
- 模板栏把内容词换成 `X/Y/A/B`，保留功能词（despite / whereas / alone / only）。

写完立即校验：

```bash
node --check u1.js && node --check u2.js
```

### 第 6 步 · 写工具箱

`t1`–`t6` 六个 section。按**写作功能**组织，不按字母。每张表：模板 | 用在哪（或力度/实例）。

### 第 7 步 · 组装

```bash
python scripts/assemble.py --template body.html --out final.html \
    --units u1.js u2.js --figs figsec.html --toolbox tb.html
```

模板占位符：`{{CSS}} {{FIGS}} {{UNITS}} {{TOOLBOX}} {{RENDER}}`，由脚本替换。

### 第 8 步 · 验证

```bash
python scripts/verify_page.py final.html --js --dom
python scripts/verify_page.py final.html --shot s1 --out shot1.png
python scripts/verify_page.py final.html --shot s4b --out shotfig.png
python scripts/verify_page.py final.html --shot u2 --out shotu.png
python scripts/verify_page.py final.html --shot s1 --mobile --out shotm.png
```

`--dom` 输出形如 `rendered units=19 cards=89 nav links=19 images=6`。**逐项核对**：
- `nav links == units`
- 页面文案里的「N 个单元 / M 句」与 `units` / `cards` 完全一致（这是最常漏的一处）。
- `images` 等于图数。

截图后**必须肉眼过一遍**：图有没有显示、高亮是否分层、移动端有没有溢出。

### 第 9 步 · 清理

只留最终 HTML。删掉 `work/`、`body.html`、`u*.js`、`figsec.html`、`tb.html`、截图。

> zsh 下 `rm -f _verify_*.png` 无匹配会中止整条命令，先 `ls` 确认或逐个删。

---

## 质量线

一份合格的产物满足：

1. **每个结论都有锚点**——图号、原句、或数值。
2. **四栏各司其职**——语法栏不写成翻译，逻辑栏不写成「说明」，模板栏能直接造句。
3. **图版三层齐全**——「在证明什么」要说明它**不**证明什么；「怎么看」要给基准。
4. **工具箱可检索**——带着「我要写让步段」来，三十秒内取到骨架。
5. **文案与数据一致**——统计数字、单元数、图数与实际渲染结果逐项对上。

## 资源索引

| 文件 | 用途 |
|---|---|
| `scripts/extract_pdf.py` | 抽文本 + 检测候选图 + 精确裁图 |
| `scripts/assemble.py` | 模板 + 部件 → 单文件 HTML |
| `scripts/verify_page.py` | JS 语法 / DOM 计数 / 桌面与移动截图 |
| `assets/base.css` | 完整样式（双色高亮、图表、响应式、打印） |
| `assets/render.js` | 单元渲染、导航、句子跳转、复制、进度条 |
| `assets/page-template.html` | 页面骨架，含填写指引 |
| `assets/unit-schema.js` | 精读数据结构与标记规则示例 |
| `references/page-structure.md` | 每一节写什么、质量线 |
| `references/analysis-framework.md` | 单元切分、四栏写法、高亮密度、失败模式 |
| `references/pdf-pitfalls.md` | 环境、segfault、裁图、体积、headless、zsh 陷阱 |
