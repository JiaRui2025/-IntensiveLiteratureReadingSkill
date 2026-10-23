/* Data schema for the close-reading units.
 *
 * Two arrays, concatenated by render.js:  const ALL = UNITS.concat(UNITS_B);
 * Split into two files when the article is long (UNITS = first half,
 * UNITS_B = second half) so neither file gets unwieldy.
 *
 * Unit object
 *   id    : "u1", "u2", ... (NO zero padding — verify_page.py matches u\d+)
 *   tag   : "01", "02", ...  (display badge)
 *   zh    : "引言 · 用异常开题"        (nav label after the last " · ")
 *   en    : "Introduction, paragraph 1"
 *   job   : paragraph function, 2–4 sentences. What is this paragraph DOING?
 *   para  : the original paragraph, marked up (see markup rules below)
 *   sent  : array of sentence objects, same order as the .sn spans
 *
 * Sentence object
 *   i  : 0-based index, MUST match data-i in the paragraph span
 *   tx : the sentence in plain text (escaped by esc() at render time)
 *   g  : grammar skeleton — clause structure, not a translation
 *   l  : logical function — why the author wrote it here
 *   t  : reusable template — swap X/Y/A/B and reuse
 *   n  : optional detail / pitfall reminder
 *
 * Markup rules for `para`
 *   <mark class="c">content</mark>      teal  — substantive content
 *   <mark class="p">pattern</mark>      amber — reusable academic phrasing
 *   <span class="lc">signal</span>      dashed underline — logic signal words
 *   <span class="sn" data-i="0">...</span>  clickable sentence (REQUIRED)
 *
 * Rules of thumb
 *   - One .sn span per sentence, covering the whole sentence.
 *   - data-i runs 0..n-1 with no gaps, matching sent[].i.
 *   - Keep highlight density ~20–35%. Highlighting everything = highlighting nothing.
 *   - Nested marks are not supported; split instead.
 */

const UNITS = [
{
  id: "u1",
  tag: "01",
  zh: "标题与摘要",
  en: "Title & Abstract",
  job: `摘要只做四件事：交代背景 → 指出缺口 → 说明做了什么 → 给出结论。这一段的写法值得逐句拆，因为它把「为什么值得读」压缩在了 120 个词里。`,
  para: `<span class="sn" data-i="0">Lime plasters <mark class="p">have been used for</mark> decorative and building purposes <mark class="p">since the origin of</mark> pyrotechnology in the Levant ca. 10,000 to 12,000 BCE.</span> <span class="sn" data-i="1">Pre-Columbian civilizations such as the Maya <mark class="c">independently developed</mark> lime pyrotechnology, with first evidence for architectural use dating ca. 1100 BCE.</span> <span class="sn" data-i="2">These plasters <mark class="p">display an unexpectedly good state of conservation</mark> <mark class="c">despite &gt;1200-year exposure</mark> to a deleterious hot and humid tropical environment.</span>`,
  sent: [
    {
      i: 0,
      tx: "Lime plasters have been used for decorative and building purposes since the origin of pyrotechnology in the Levant ca. 10,000 to 12,000 BCE.",
      g: `现在完成时被动（have been used）+ since + 时间点 + ca.（约）。`,
      l: `开篇不写「石灰很重要」，而是给一个时间跨度：一万两千年。用「长度」建立分量，比用形容词更省力。`,
      t: `X have been used for A and B purposes since the origin of C in D ca. 0000 BCE.`,
      n: `since 后面接时间点，不接时间段；ca. 是 circa 的缩写，用于考古年代，比 about 更专业。`
    },
    {
      i: 1,
      tx: "Pre-Columbian civilizations such as the Maya independently developed lime pyrotechnology, with first evidence for architectural use dating ca. 1100 BCE.",
      g: `独立结构（with + 名词 + 分词 dating）。`,
      l: `independently 一个词点出「平行发明」——这很重要，因为它意味着玛雅的配方是自己演化出来的，不是从旧大陆传过去的。`,
      t: `X such as Y independently developed Z, with first evidence for A dating ca. 0000 BCE.`,
      n: `with 独立结构是补充信息的利器：主句说主张，with 段补证据，读者顺链走，不用停顿。`
    },
    {
      i: 2,
      tx: "These plasters display an unexpectedly good state of conservation despite >1200-year exposure to a deleterious hot and humid tropical environment.",
      g: `主句 + despite + 名词短语（对比）。`,
      l: `全段的重心句。unexpectedly 是态度词，despite 引出反差条件——「本该坏，却没坏」，这就是全文的问题起点。`,
      t: `X display an unexpectedly good state of A despite >N-year exposure to a deleterious B environment.`,
      n: `despite 后接名词短语，although 后接从句。学术写作里 despite 更紧凑，但要注意别写成 despite of。`
    }
  ]
}
];

/* const UNITS_B = [ ... ];  // second half, same shape */
