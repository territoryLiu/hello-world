# Changbaishan-Yanji Trip Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh `吉林延吉长白山trip.html` with a cleaner premium travel-editorial look while preserving content order, and create `吉林延吉长白山trip-专题版.html` with an answer-first reading flow.

**Architecture:** Keep both deliverables as standalone offline HTML files with no external dependencies. Reuse one visual system across both pages, preserve anchors and section order in the original file, and only reorganize/dedupe content in the new专题版 copy. Add one lightweight PowerShell regression script so structure checks are repeatable.

**Tech Stack:** HTML, CSS, minimal vanilla JS only if required, PowerShell validation script, Git

---

### Task 1: Rebuild The Original Page Visual Shell

**Files:**
- Create: `tests/trip-page-regression.ps1`
- Modify: `吉林延吉长白山trip.html`
- Test: `tests/trip-page-regression.ps1`

- [ ] **Step 1: Write the failing structure check for the original file**

```powershell
param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Assert-Match {
  param(
    [string]$Content,
    [string]$Pattern,
    [string]$Label
  )

  if ($Content -notmatch $Pattern) {
    throw "Missing $Label ($Pattern)"
  }
}

$tripPath = Join-Path $Root "吉林延吉长白山trip.html"
$tripContent = Get-Content -Raw $tripPath

foreach ($id in @("wear", "best", "plans", "tips", "sources")) {
  Assert-Match -Content $tripContent -Pattern "id=`"$id`"" -Label "anchor #$id"
}

Assert-Match -Content $tripContent -Pattern "--bg-warm:" -Label "warm background token"
Assert-Match -Content $tripContent -Pattern 'class="hero-summary"' -Label "hero summary rail"
Assert-Match -Content $tripContent -Pattern 'class="section-intro"' -Label "section intro wrapper"
Assert-Match -Content $tripContent -Pattern 'class="dark-panel"' -Label "dark emphasis panel"

Write-Host "trip.html structure checks passed"
```

- [ ] **Step 2: Run the structure check and verify it fails**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\trip-page-regression.ps1 -Root .
```

Expected: FAIL with a message similar to `Missing warm background token (--bg-warm:)`.

- [ ] **Step 3: Implement the original-file redesign with preserved anchors**

Update `吉林延吉长白山trip.html` so it keeps the current content order and `id` anchors, but swaps the visual shell to the approved direction.

Replace the top-level token block with a tighter palette and shared surfaces:

```html
<style>
  :root{
    --bg-warm:#efe7dc;
    --bg-cream:#f7f1e8;
    --surface:#fffaf3;
    --surface-soft:#f2eadf;
    --surface-deep:#d9cfbe;
    --ink:#26262b;
    --ink-soft:#5f5a55;
    --accent:#f2cc78;
    --accent-deep:#c98f3f;
    --sage:#7f8c73;
    --pine:#2a2d34;
    --line:rgba(38,38,43,.08);
    --shadow:0 24px 60px rgba(42,34,28,.10);
    --radius-xl:34px;
    --radius-lg:26px;
    --radius-md:18px;
  }

  body{
    margin:0;
    color:var(--ink);
    font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
    line-height:1.75;
    background:
      radial-gradient(circle at 10% 18%,rgba(242,204,120,.18),transparent 18%),
      radial-gradient(circle at 86% 12%,rgba(127,140,115,.14),transparent 18%),
      linear-gradient(180deg,#f3ece2 0%,#efe7dc 44%,#f8f3eb 100%);
  }

  .hero-summary,
  .feature-panel,
  .paper,
  .source,
  .dark-panel{
    border-radius:var(--radius-lg);
    border:1px solid var(--line);
    box-shadow:var(--shadow);
  }
```

Rebuild the header area into a magazine-style hero with summary chips:

```html
<header class="hero">
  <div class="wrap hero-shell">
    <div class="hero-copy">
      <p class="eyebrow">May Day Travel Guide</p>
      <h1 class="page-title">五一旅游攻略：长春 · 延吉 · 长白山</h1>
      <p class="hero-lead">给第一次走东北线的人：先把路线、穿衣和订票顺序看明白，再决定要不要把每一餐都安排成连续剧。</p>
    </div>
    <aside class="dark-panel hero-summary">
      <strong>先抓 4 件事</strong>
      <ul>
        <li>长春轻春装，长白山按冬春交界准备。</li>
        <li>第一次去优先长春 → 延吉 → 二道白河 → 北坡。</li>
        <li>先锁长白山票，再锁二道白河住宿。</li>
        <li>返程以顺利回去为第一原则。</li>
      </ul>
    </aside>
  </div>
</header>
```

Wrap each section header in a reusable intro block and tone down the old handcraft effects:

```html
<div class="section-intro">
  <p class="kicker">Wardrobe</p>
  <div class="head">
    <h2>五一穿衣指南</h2>
    <p>城市已经进入春装节奏，但长白山五一仍可能有积雪和明显风感，建议按城市一套、上山一套来准备。</p>
  </div>
</div>
```

Also add one reusable dark emphasis module inside the original page, for example in the “最推荐路线” or “注意事项” area:

```html
<article class="dark-panel">
  <span class="label">Route Snapshot</span>
  <h3>第一次去最稳的节奏</h3>
  <p>长春只留一晚，延吉给完整吃喝拍照时间，北坡前一晚住二道白河，机动日留给天气和体力。</p>
</article>
```

- [ ] **Step 4: Run the structure check and verify it passes**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\trip-page-regression.ps1 -Root .
```

Expected: PASS with `trip.html structure checks passed`.

- [ ] **Step 5: Commit the original-page redesign**

```bash
git add tests/trip-page-regression.ps1 "吉林延吉长白山trip.html"
git commit -m "feat: redesign original changbaishan trip page"
```

### Task 2: Create The Restructured Story Edition

**Files:**
- Create: `吉林延吉长白山trip-专题版.html`
- Modify: `tests/trip-page-regression.ps1`
- Test: `tests/trip-page-regression.ps1`

- [ ] **Step 1: Extend the regression script with failing checks for the story edition**

Append these checks to `tests/trip-page-regression.ps1` after the original-file assertions:

```powershell
$storyPath = Join-Path $Root "吉林延吉长白山trip-专题版.html"

if (-not (Test-Path $storyPath)) {
  throw "Missing 吉林延吉长白山trip-专题版.html"
}

$storyContent = Get-Content -Raw $storyPath

foreach ($id in @("summary", "timeline", "packing", "booking", "guide", "tips", "sources")) {
  Assert-Match -Content $storyContent -Pattern "id=`"$id`"" -Label "story anchor #$id"
}

foreach ($marker in @("专题速览", "路线时间轴", "订票顺序", "完整展开攻略", "信息来源")) {
  Assert-Match -Content $storyContent -Pattern $marker -Label $marker
}

Assert-Match -Content $storyContent -Pattern 'class="hero-summary"' -Label "story hero summary rail"
Assert-Match -Content $storyContent -Pattern 'class="dark-panel"' -Label "story dark emphasis panel"

Write-Host "story edition checks passed"
```

- [ ] **Step 2: Run the regression script and verify it fails for the missing story file**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\trip-page-regression.ps1 -Root .
```

Expected: FAIL with `Missing 吉林延吉长白山trip-专题版.html`.

- [ ] **Step 3: Build the new answer-first story page**

Create `吉林延吉长白山trip-专题版.html` as a standalone page that reuses the visual system from the original redesign but changes the reading flow.

Use this section order in the new file:

```html
<nav class="navin">
  <a href="#summary">先看结论</a>
  <a href="#timeline">路线时间轴</a>
  <a href="#packing">穿衣打包</a>
  <a href="#booking">订票顺序</a>
  <a href="#guide">完整展开攻略</a>
  <a href="#tips">注意事项</a>
  <a href="#sources">信息来源</a>
</nav>
```

Build the top of the page so the first one to two screens answer the four required questions from the spec:

```html
<section id="summary" class="feature-panel">
  <div class="section-intro">
    <p class="kicker">专题速览</p>
    <h2>第一次去，先照这个节奏走</h2>
    <p>路线优先级、穿衣判断、住宿落点和订票顺序都先放在前面，不让人一上来先掉进长表格里。</p>
  </div>
  <div class="summary-grid">
    <article class="dark-panel">
      <span class="label">路线</span>
      <h3>长春 → 延吉 → 二道白河 → 北坡</h3>
      <p>这是第一次去最稳的主方案。</p>
    </article>
    <article class="paper">
      <span class="label">穿衣</span>
      <p>城市按春装，进山按冬春交界多备一层。</p>
    </article>
    <article class="paper">
      <span class="label">住宿</span>
      <p>延吉住延边大学 / 西市场一线；北坡前夜住二道白河。</p>
    </article>
    <article class="paper">
      <span class="label">顺序</span>
      <p>先票后房，再补城市交通与返程。</p>
    </article>
  </div>
</section>
```

Follow with the answer-first modules and move the long-form content later:

```html
<section id="timeline" class="feature-panel">
  <div class="section-intro">
    <p class="kicker">路线时间轴</p>
    <h2>最推荐路线</h2>
  </div>
</section>

<section id="packing" class="feature-panel">
  <div class="section-intro">
    <p class="kicker">穿衣打包</p>
    <h2>一句话记住：城市春装，进山多一层</h2>
  </div>
</section>

<section id="booking" class="feature-panel">
  <div class="section-intro">
    <p class="kicker">订票顺序</p>
    <h2>别把票房顺序搞反</h2>
  </div>
</section>

<section id="guide" class="feature-panel">
  <div class="section-intro">
    <p class="kicker">完整展开攻略</p>
    <h2>如果你想把备选方案和细节都看全，再往下读</h2>
  </div>
</section>
```

When moving content from the original file, keep facts and links, but dedupe repeated guidance instead of repeating the same conclusion in multiple panels.

- [ ] **Step 4: Run the regression script and verify both files pass**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\trip-page-regression.ps1 -Root .
```

Expected: PASS with both lines:

```text
trip.html structure checks passed
story edition checks passed
```

- [ ] **Step 5: Commit the story-edition file**

```bash
git add tests/trip-page-regression.ps1 "吉林延吉长白山trip-专题版.html"
git commit -m "feat: add story edition for changbaishan trip guide"
```

### Task 3: Lock Responsive Behavior And Final QA

**Files:**
- Modify: `tests/trip-page-regression.ps1`
- Modify: `吉林延吉长白山trip.html`
- Modify: `吉林延吉长白山trip-专题版.html`
- Test: `tests/trip-page-regression.ps1`

- [ ] **Step 1: Add failing responsive checks for both HTML files**

Append these checks to `tests/trip-page-regression.ps1`:

```powershell
foreach ($item in @(
  @{ Name = "trip"; Content = $tripContent },
  @{ Name = "story"; Content = $storyContent }
)) {
  Assert-Match -Content $item.Content -Pattern "@media \(max-width:960px\)" -Label "$($item.Name) mobile breakpoint"
  Assert-Match -Content $item.Content -Pattern "grid-template-columns:1fr" -Label "$($item.Name) single-column fallback"
}

Write-Host "responsive checks passed"
```

- [ ] **Step 2: Run the regression script and verify it fails on the missing responsive contract**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\trip-page-regression.ps1 -Root .
```

Expected: FAIL with a message similar to `Missing story mobile breakpoint`.

- [ ] **Step 3: Add the final responsive contract and polish both files**

Make sure both HTML files include the same mobile fallback rules for the large grids and hero shell:

```css
@media (max-width:960px){
  .hero-shell,
  .split,
  .recommend,
  .cards,
  .cards.two,
  .grid-3,
  .summary-grid{
    grid-template-columns:1fr;
  }

  .hero-summary,
  .dark-panel{
    order:initial;
  }
}

@media (max-width:720px){
  .navin{
    border-radius:22px;
    padding:10px;
  }

  .page-title{
    font-size:clamp(30px,9vw,42px);
  }

  .table{
    display:block;
    overflow:auto;
  }
}
```

Then run one whitespace/error pass before the final test:

```powershell
git diff --check -- "吉林延吉长白山trip.html" "吉林延吉长白山trip-专题版.html" "tests/trip-page-regression.ps1"
```

Expected: no output.

- [ ] **Step 4: Run the full regression check and do a manual browser QA pass**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\trip-page-regression.ps1 -Root .
```

Expected:

```text
trip.html structure checks passed
story edition checks passed
responsive checks passed
```

Then manually open both files and verify:

```powershell
Start-Process "d:\vscode\hello-world\吉林延吉长白山trip.html"
Start-Process "d:\vscode\hello-world\吉林延吉长白山trip-专题版.html"
```

Manual expected result:

- 首屏不是彩色碎片卡片堆。
- 原文件仍可用导航跳到 `wear / best / plans / tips / sources`。
- 专题版前两屏能直接读到路线、穿衣、住宿和订票顺序。
- 窄屏下没有双列挤爆或表格溢出遮挡正文。

- [ ] **Step 5: Commit the responsive polish and QA pass**

```bash
git add tests/trip-page-regression.ps1 "吉林延吉长白山trip.html" "吉林延吉长白山trip-专题版.html"
git commit -m "fix: finalize responsive trip guide redesign"
```

## Self-Review

### Spec coverage

- 原文件覆盖版保留内容顺序与锚点：Task 1
- 统一奶油暖底 + 深色面板 + 杂志式排版：Task 1 and Task 2
- 新增“先结论后展开”的专题副本：Task 2
- 手机与桌面可读、双文件结构验证：Task 3
- 单文件离线 HTML、无外链依赖：Task 1 and Task 2 implementation constraints

No spec gaps found.

### Placeholder scan

Searched the plan for `TODO`, `TBD`, vague “handle later” wording, and unresolved filenames. No placeholders remain.

### Type consistency

- Original-file preserved anchors: `wear`, `best`, `plans`, `tips`, `sources`
- Story-edition anchors: `summary`, `timeline`, `packing`, `booking`, `guide`, `tips`, `sources`
- Shared structural classes used consistently: `hero-summary`, `section-intro`, `dark-panel`

No naming conflicts found.
