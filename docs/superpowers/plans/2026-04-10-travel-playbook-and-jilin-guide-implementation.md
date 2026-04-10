# Travel Playbook And Jilin Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `travel-planning-playbook.md` into a reusable travel-guide execution manual, then build the Jilin / Yanji / Changbai Mountain guide as matched desktop/mobile outputs with source notes and an image-placement plan.

**Architecture:** Keep `travel-planning-playbook.md` as the canonical workflow document at the repo root. Build the Jilin deliverables under `trips/jilin-yanji-changbaishan/` with one shared content file and one shared renderer so desktop and mobile stay factually aligned while differing in layout only. Add one new regression script and update the existing Playwright render check to validate file presence, section structure, and responsive behavior.

**Tech Stack:** Markdown, HTML, CSS, vanilla JavaScript, PowerShell regression checks, Playwright Python render checks, Git

---

## File Structure

Planned file ownership before task breakdown:

- Modify: `travel-planning-playbook.md`
  The reusable execution manual for future travel-guide work.
- Create: `trips/jilin-yanji-changbaishan/assets/guide-content.js`
  Shared factual content for desktop/mobile rendering.
- Create: `trips/jilin-yanji-changbaishan/assets/render-guide.js`
  Shared rendering helpers for section output and parity.
- Create: `trips/jilin-yanji-changbaishan/assets/base.css`
  Shared visual tokens and common layout rules.
- Create: `trips/jilin-yanji-changbaishan/desktop/index.html`
  Desktop travel guide entry page.
- Create: `trips/jilin-yanji-changbaishan/desktop/desktop.css`
  Desktop-only layout adjustments.
- Create: `trips/jilin-yanji-changbaishan/mobile/index.html`
  Mobile paginated travel guide entry page.
- Create: `trips/jilin-yanji-changbaishan/mobile/mobile.css`
  Mobile-only pagination and reading-flow adjustments.
- Create: `trips/jilin-yanji-changbaishan/notes/sources.md`
  Auditable source list grouped by topic.
- Create: `trips/jilin-yanji-changbaishan/notes/image-plan.md`
  Image-slot planning document with scene/source/timestamp guidance.
- Create: `tests/travel-guide-regression.ps1`
  Static regression checks for the new playbook and Jilin deliverables.
- Modify: `tests/playwright_trip_render_check.py`
  Browser render check updated to target the new desktop/mobile files.

### Task 1: Add A Failing Regression Harness For The New Workflow

**Files:**
- Create: `tests/travel-guide-regression.ps1`
- Modify: `tests/playwright_trip_render_check.py`
- Test: `tests/travel-guide-regression.ps1`

- [ ] **Step 1: Write the failing PowerShell regression script**

Create `tests/travel-guide-regression.ps1` with these checks:

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

$playbookPath = Join-Path $Root "travel-planning-playbook.md"
$desktopPath = Join-Path $Root "trips/jilin-yanji-changbaishan/desktop/index.html"
$mobilePath = Join-Path $Root "trips/jilin-yanji-changbaishan/mobile/index.html"
$sourceNotePath = Join-Path $Root "trips/jilin-yanji-changbaishan/notes/sources.md"
$imagePlanPath = Join-Path $Root "trips/jilin-yanji-changbaishan/notes/image-plan.md"
$contentPath = Join-Path $Root "trips/jilin-yanji-changbaishan/assets/guide-content.js"

$playbookContent = Get-Content -Raw $playbookPath

foreach ($heading in @(
  "## 开始前必须确认的信息",
  "## 调研执行顺序",
  "## 行程方案生成规则",
  "## HTML 内容顺序规范",
  "## 图位方案规范",
  "## 交付检查清单"
)) {
  Assert-Match -Content $playbookContent -Pattern [regex]::Escape($heading) -Label $heading
}

foreach ($pathInfo in @(
  @{ Path = $desktopPath; Label = "desktop index" },
  @{ Path = $mobilePath; Label = "mobile index" },
  @{ Path = $sourceNotePath; Label = "sources note" },
  @{ Path = $imagePlanPath; Label = "image plan note" },
  @{ Path = $contentPath; Label = "shared guide content" }
)) {
  if (-not (Test-Path $pathInfo.Path)) {
    throw "Missing $($pathInfo.Label): $($pathInfo.Path)"
  }
}

$desktopContent = Get-Content -Raw $desktopPath
$mobileContent = Get-Content -Raw $mobilePath
$sharedContent = Get-Content -Raw $contentPath

foreach ($contentInfo in @(
  @{ Name = "desktop"; Content = $desktopContent },
  @{ Name = "mobile"; Content = $mobileContent }
)) {
  foreach ($id in @("overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources")) {
    Assert-Match -Content $contentInfo.Content -Pattern "id=`"$id`"" -Label "$($contentInfo.Name) section #$id"
  }
}

Assert-Match -Content $mobileContent -Pattern 'data-page="' -Label "mobile pagination markers"
Assert-Match -Content $sharedContent -Pattern 'const tripGuide =' -Label "shared guide content export"

Write-Host "travel guide regression checks passed"
```

- [ ] **Step 2: Run the regression script and verify it fails**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: FAIL with a message similar to `Missing desktop index`.

- [ ] **Step 3: Point the Playwright render checker at the new target files**

Replace the `PAGES` block in `tests/playwright_trip_render_check.py` with:

```python
ROOT = Path(r"d:\vscode\hello-world")
PAGES = [
    ROOT / "trips" / "jilin-yanji-changbaishan" / "desktop" / "index.html",
    ROOT / "trips" / "jilin-yanji-changbaishan" / "mobile" / "index.html",
]
```

Keep the rest of the render checker intact for now.

- [ ] **Step 4: Re-run the regression script and keep it failing on missing outputs**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: still FAIL, because implementation files are not created yet.

- [ ] **Step 5: Commit the regression harness**

```bash
git add tests/travel-guide-regression.ps1 tests/playwright_trip_render_check.py
git commit -m "test: add regression harness for travel guide rebuild"
```

### Task 2: Rewrite The Playbook As An Execution Manual

**Files:**
- Modify: `travel-planning-playbook.md`
- Test: `tests/travel-guide-regression.ps1`

- [ ] **Step 1: Confirm the current playbook fails the new heading contract**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: FAIL on one or more missing headings such as `## 开始前必须确认的信息`.

- [ ] **Step 2: Replace the playbook header and top-level section order**

Restructure the file to begin like this:

```markdown
# 旅游攻略 HTML 执行手册

适用范围：用于整理旅游攻略、行程页、目的地专题页，以及需要同时交付桌面端和手机端的旅游 HTML 项目。

目标：先确认出行要求，再按固定顺序调研与整理，最后交付可以直接执行的旅游攻略页面。

## 开始前必须确认的信息

每次开始前先确认以下内容，并记录哪些字段已经明确、哪些字段需要继续追问。

- 出发城市
- 出行日期
- 总人数
- 年龄段
- 是否有小孩
- 是否有老人
- 分房需求
- 预算或估算方式
- 住宿偏好
- 行程节奏
- 是否接受早起
- 是否需要桌面端和手机端
- 是否需要图位方案
```

- [ ] **Step 3: Add the research, generation, HTML-order, and image-planning sections**

Insert these exact section headings and starter rules:

```markdown
## 调研执行顺序

1. 官方景区与文旅信息
2. 大交通与当地交通
3. 天气与历史气温
4. 门票、收费与预约规则
5. 美团、大众点评等餐饮信息
6. 小红书、抖音、B站正文、评论区与视频内容
7. 信息交叉核对与信息源整理

## 行程方案生成规则

- 每次至少生成 1 个最推荐方案和 2 个备选方案。
- 每个方案都要写清适合人群、每日安排、主要交通、住宿建议、费用估算和执行提醒。
- 最推荐方案放在最前，并说明为什么最适合当前人群。

## HTML 内容顺序规范

1. 标题
2. 每天安排总览
3. 最推荐方案
4. 其他备选方案
5. 景点详解
6. 门票、收费与预约时间
7. 美食与店铺推荐
8. 最佳月份与当前月份情况
9. 当前月份穿衣与必备物品
10. 出发地到目的地交通方式
11. 信息源

## 图位方案规范

每个图位都要写清：

- 图位编号
- 页面位置
- 适合的画面内容
- 推荐来源
- 如果来自视频，适合截取的镜头或时间段
- 这张图在页面里的作用
```

- [ ] **Step 4: Add the delivery checklist and reusable template**

End the playbook with:

```markdown
## 交付检查清单

- 是否已确认关键出行信息
- 是否已给出最推荐方案和备选方案
- 是否先写每天安排
- 是否写清景点收费与预约
- 是否写清店铺地址、菜系、推荐菜
- 是否写清最佳月份与当前月份情况
- 是否写清穿衣和必备物品
- 是否写清交通费用和预估时间
- 是否统一整理信息源
- 是否输出桌面端和手机端
- 是否单独整理图位方案

## 可复用执行模板

### 已确认信息
- 出发城市：
- 出行日期：
- 人数与年龄段：
- 住宿偏好：
- 行程节奏：

### 输出清单
- 桌面端 HTML
- 手机端 HTML
- 信息源文档
- 图位方案文档
```

- [ ] **Step 5: Run the regression script and verify the playbook portion passes**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: FAIL only on the still-missing trip output files, not on playbook headings.

- [ ] **Step 6: Commit the playbook rewrite**

```bash
git add travel-planning-playbook.md
git commit -m "docs: rewrite travel planning playbook as execution manual"
```

### Task 3: Scaffold The Jilin Project Directory And Notes

**Files:**
- Create: `trips/jilin-yanji-changbaishan/assets/guide-content.js`
- Create: `trips/jilin-yanji-changbaishan/assets/render-guide.js`
- Create: `trips/jilin-yanji-changbaishan/assets/base.css`
- Create: `trips/jilin-yanji-changbaishan/notes/sources.md`
- Create: `trips/jilin-yanji-changbaishan/notes/image-plan.md`
- Test: `tests/travel-guide-regression.ps1`

- [ ] **Step 1: Create the shared content file with confirmed trip metadata**

Create `trips/jilin-yanji-changbaishan/assets/guide-content.js`:

```javascript
const tripGuide = {
  meta: {
    slug: "jilin-yanji-changbaishan",
    title: "五一旅游攻略：南京出发 · 长春 / 延吉 / 长白山",
    dateRange: "2026-04-30 至 2026-05-05",
    departure: "南京",
    travelers: "4 位，28 岁左右，两男两女",
    pace: "可接受早起",
    stayPreference: "汉庭优先，标间 150-450 元",
    checkedAt: "截至 2026-04-10"
  },
  sections: {
    overview: [],
    recommended: [],
    options: [],
    attractions: [],
    food: [],
    season: [],
    packing: [],
    transport: [],
    sources: []
  }
};
```

- [ ] **Step 2: Create the shared renderer with section helpers**

Create `trips/jilin-yanji-changbaishan/assets/render-guide.js`:

```javascript
function byId(id) {
  return document.getElementById(id);
}

function renderList(items) {
  return items.map((item) => `<li>${item}</li>`).join("");
}

function renderCards(items, className = "card-grid") {
  return items.map((item) => `
    <article class="card">
      <h3>${item.title}</h3>
      <p>${item.summary}</p>
      ${item.points ? `<ul>${renderList(item.points)}</ul>` : ""}
    </article>
  `).join("");
}

window.tripGuideRenderer = {
  byId,
  renderList,
  renderCards
};
```

- [ ] **Step 3: Create the shared base stylesheet and note files**

Create `trips/jilin-yanji-changbaishan/assets/base.css`:

```css
:root{
  --bg:#f2eadf;
  --surface:#fffaf2;
  --surface-strong:#f7efe4;
  --ink:#22252b;
  --ink-soft:#5c5953;
  --line:rgba(34,37,43,.10);
  --accent:#d28e49;
  --forest:#314238;
  --radius-xl:32px;
  --radius-lg:24px;
  --radius-md:16px;
  --shadow:0 18px 48px rgba(34,24,16,.10);
}

*{box-sizing:border-box}
body{
  margin:0;
  color:var(--ink);
  background:linear-gradient(180deg,#f5eee5 0%,#efe6db 48%,#fbf7f1 100%);
  font-family:"Microsoft YaHei","PingFang SC",sans-serif;
}

.section-shell{
  width:min(1120px,calc(100% - 28px));
  margin:0 auto;
}
```

Create `trips/jilin-yanji-changbaishan/notes/sources.md`:

```markdown
# 吉林延吉长白山信息源

## 官方与一手信息

## 交通信息

## 天气与季节

## 餐饮与店铺

## 社交平台与评论区
```

Create `trips/jilin-yanji-changbaishan/notes/image-plan.md`:

```markdown
# 吉林延吉长白山图位方案

| 图位编号 | 页面位置 | 建议画面 | 推荐来源 | 视频镜头 / 时间段 | 页面作用 |
| --- | --- | --- | --- | --- | --- |
| A1 | 每天安排后 | 清晨市场热气、摊位和人流 | 小红书 / 抖音 | 开场 3-8 秒的摊位扫街镜头 | 让第二天早起安排更有代入感 |
```

- [ ] **Step 4: Run the regression script and verify only HTML sections are still missing**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: FAIL on desktop/mobile section markers, not on missing files.

- [ ] **Step 5: Commit the scaffold and notes**

```bash
git add trips/jilin-yanji-changbaishan/assets/guide-content.js trips/jilin-yanji-changbaishan/assets/render-guide.js trips/jilin-yanji-changbaishan/assets/base.css trips/jilin-yanji-changbaishan/notes/sources.md trips/jilin-yanji-changbaishan/notes/image-plan.md
git commit -m "feat: scaffold jilin guide workspace and notes"
```

### Task 4: Populate Shared Jilin Content Data

**Files:**
- Modify: `trips/jilin-yanji-changbaishan/assets/guide-content.js`
- Modify: `trips/jilin-yanji-changbaishan/notes/sources.md`
- Modify: `trips/jilin-yanji-changbaishan/notes/image-plan.md`
- Test: `tests/travel-guide-regression.ps1`

- [ ] **Step 1: Replace empty overview and recommended arrays with actual content**

Update `guide-content.js` so the `overview` and `recommended` sections include actual data:

```javascript
tripGuide.sections.overview = [
  {
    title: "每天安排先看这一版",
    summary: "4 月 30 日到 5 月 1 日先落长春，5 月 1 日晚转延吉，5 月 3 日前往二道白河，5 月 4 日上长白山北坡，5 月 5 日返程。",
    points: [
      "第一晚住长春，控制转场强度。",
      "延吉留完整吃喝拍照时间。",
      "北坡前一晚住二道白河，会更省力。"
    ]
  }
];

tripGuide.sections.recommended = [
  {
    title: "最推荐方案：长春一晚 + 延吉两晚 + 二道白河一晚",
    summary: "适合第一次去、愿意早起、想把景点和美食都走顺的人群。",
    points: [
      "先城市后景区，节奏更稳。",
      "把长白山放在后段，更方便看天气。",
      "回程缓冲更好安排。"
    ]
  }
];
```

- [ ] **Step 2: Add option, attraction, food, season, packing, transport, and sources data**

Continue in `guide-content.js` with this structure:

```javascript
tripGuide.sections.options = [
  {
    title: "轻松版",
    summary: "减少长春停留，延吉和二道白河节奏更松。",
    points: ["更适合重吃喝拍照。", "转场更少。", "景点覆盖略收。"]
  },
  {
    title: "景点更全版",
    summary: "增加长春城市打卡和延边周边顺路点位。",
    points: ["景点更满。", "每天移动更多。", "适合体力在线的同行人。"]
  }
];

tripGuide.sections.transport = [
  {
    title: "南京往返长春 / 延吉",
    summary: "同时列高铁、飞机、当地接驳，标注截至 2026-04-10 最近可查。",
    points: [
      "高铁 / 动车：写明主要车次、耗时、票价。",
      "飞机：写明直飞或更稳中转方案。",
      "公交 / 地铁 / 打车：写清机场、高铁站到核心住宿区的接驳。"
    ]
  }
];
```

At the same time, replace the placeholder note headings in `sources.md` with real source bullets grouped by:

```markdown
## 官方与一手信息
- 长白山景区官方预约与票务页
- 延吉文旅公开信息
- 长春文旅公开信息

## 交通信息
- 12306
- 航司或主流机票平台最近可查班次页
- 当地公交 / 机场接驳公开页面
```

Add at least five image slots to `image-plan.md`, covering:

- 每天安排总览
- 延吉早市
- 民俗园或网红墙
- 二道白河落脚点
- 长白山北坡

- [ ] **Step 3: Run the regression script and keep it failing on HTML only**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: FAIL because desktop/mobile pages still do not exist or lack required sections.

- [ ] **Step 4: Commit the shared content data**

```bash
git add trips/jilin-yanji-changbaishan/assets/guide-content.js trips/jilin-yanji-changbaishan/notes/sources.md trips/jilin-yanji-changbaishan/notes/image-plan.md
git commit -m "feat: add jilin guide content data and research notes"
```

### Task 5: Build The Desktop Guide

**Files:**
- Create: `trips/jilin-yanji-changbaishan/desktop/index.html`
- Create: `trips/jilin-yanji-changbaishan/desktop/desktop.css`
- Modify: `trips/jilin-yanji-changbaishan/assets/guide-content.js`
- Test: `tests/travel-guide-regression.ps1`

- [ ] **Step 1: Create the desktop HTML shell with all required sections**

Create `trips/jilin-yanji-changbaishan/desktop/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>吉林延吉长白山旅游攻略 · 桌面版</title>
  <link rel="stylesheet" href="../assets/base.css">
  <link rel="stylesheet" href="./desktop.css">
</head>
<body data-mode="desktop">
  <header class="hero section-shell">
    <p class="eyebrow">Jilin Travel Guide</p>
    <h1>每天怎么走，先在前面看清楚</h1>
    <p>南京出发，2026-04-30 至 2026-05-05，四人同行，按最推荐方案和备选方案一起展开。</p>
  </header>

  <nav class="section-shell nav-strip">
    <a href="#overview">每天安排</a>
    <a href="#recommended">最推荐方案</a>
    <a href="#options">备选方案</a>
    <a href="#attractions">景点详解</a>
    <a href="#food">美食推荐</a>
    <a href="#season">最佳月份</a>
    <a href="#packing">穿衣物品</a>
    <a href="#transport">交通方式</a>
    <a href="#sources">信息源</a>
  </nav>

  <main class="section-shell">
    <section id="overview"></section>
    <section id="recommended"></section>
    <section id="options"></section>
    <section id="attractions"></section>
    <section id="food"></section>
    <section id="season"></section>
    <section id="packing"></section>
    <section id="transport"></section>
    <section id="sources"></section>
  </main>

  <script src="../assets/guide-content.js"></script>
  <script src="../assets/render-guide.js"></script>
</body>
</html>
```

- [ ] **Step 2: Add desktop-specific layout styling**

Create `trips/jilin-yanji-changbaishan/desktop/desktop.css`:

```css
.hero{
  padding:36px 0 18px;
}

.nav-strip{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  padding-bottom:20px;
}

.nav-strip a,
.card{
  border:1px solid var(--line);
  border-radius:var(--radius-md);
  background:var(--surface);
  box-shadow:var(--shadow);
}

.card-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:18px;
}

section{
  padding:22px 0 0;
}

@media (max-width:960px){
  .card-grid{
    grid-template-columns:1fr;
  }
}
```

- [ ] **Step 3: Add render calls so overview and recommended sections output real cards**

Append to `desktop/index.html` before `</body>`:

```html
<script>
  const { renderCards } = window.tripGuideRenderer;
  document.getElementById("overview").innerHTML = `
    <h2>每天安排总览</h2>
    <div class="card-grid">${renderCards(tripGuide.sections.overview)}</div>
  `;
  document.getElementById("recommended").innerHTML = `
    <h2>最推荐方案</h2>
    <div class="card-grid">${renderCards(tripGuide.sections.recommended)}</div>
  `;
</script>
```

Then extend the same pattern to `options`, `attractions`, `food`, `season`, `packing`, `transport`, and `sources`.

- [ ] **Step 4: Run the regression script and verify desktop markers pass**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: FAIL only on mobile pagination markers or missing mobile sections.

- [ ] **Step 5: Commit the desktop guide**

```bash
git add trips/jilin-yanji-changbaishan/desktop/index.html trips/jilin-yanji-changbaishan/desktop/desktop.css trips/jilin-yanji-changbaishan/assets/guide-content.js
git commit -m "feat: add desktop jilin travel guide"
```

### Task 6: Build The Mobile Paginated Guide

**Files:**
- Create: `trips/jilin-yanji-changbaishan/mobile/index.html`
- Create: `trips/jilin-yanji-changbaishan/mobile/mobile.css`
- Modify: `trips/jilin-yanji-changbaishan/assets/render-guide.js`
- Test: `tests/travel-guide-regression.ps1`

- [ ] **Step 1: Create the mobile HTML with page markers for each major section**

Create `trips/jilin-yanji-changbaishan/mobile/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>吉林延吉长白山旅游攻略 · 手机版</title>
  <link rel="stylesheet" href="../assets/base.css">
  <link rel="stylesheet" href="./mobile.css">
</head>
<body data-mode="mobile">
  <main class="mobile-shell">
    <section id="overview" data-page="1"></section>
    <section id="recommended" data-page="2"></section>
    <section id="options" data-page="3"></section>
    <section id="attractions" data-page="4"></section>
    <section id="food" data-page="5"></section>
    <section id="season" data-page="6"></section>
    <section id="packing" data-page="7"></section>
    <section id="transport" data-page="8"></section>
    <section id="sources" data-page="9"></section>
  </main>

  <script src="../assets/guide-content.js"></script>
  <script src="../assets/render-guide.js"></script>
</body>
</html>
```

- [ ] **Step 2: Add mobile pagination styling**

Create `trips/jilin-yanji-changbaishan/mobile/mobile.css`:

```css
.mobile-shell{
  width:min(100%,460px);
  margin:0 auto;
  padding:16px 14px 24px;
}

[data-page]{
  min-height:100svh;
  padding:18px 0 22px;
}

[data-page]::before{
  content:"Page " attr(data-page);
  display:block;
  margin-bottom:10px;
  color:var(--accent);
  font-size:12px;
  letter-spacing:.12em;
  text-transform:uppercase;
}

.card-grid{
  display:grid;
  grid-template-columns:1fr;
  gap:14px;
}
```

- [ ] **Step 3: Add a mobile section renderer and parity checks**

Append to `render-guide.js`:

```javascript
function renderSection(title, items) {
  return `
    <header class="mobile-head">
      <h2>${title}</h2>
    </header>
    <div class="card-grid">${renderCards(items)}</div>
  `;
}

window.tripGuideRenderer.renderSection = renderSection;
```

Append to `mobile/index.html` before `</body>`:

```html
<script>
  const { renderSection } = window.tripGuideRenderer;
  document.getElementById("overview").innerHTML = renderSection("每天安排总览", tripGuide.sections.overview);
  document.getElementById("recommended").innerHTML = renderSection("最推荐方案", tripGuide.sections.recommended);
  document.getElementById("options").innerHTML = renderSection("其他备选方案", tripGuide.sections.options);
  document.getElementById("attractions").innerHTML = renderSection("景点详解", tripGuide.sections.attractions);
  document.getElementById("food").innerHTML = renderSection("美食与店铺推荐", tripGuide.sections.food);
  document.getElementById("season").innerHTML = renderSection("最佳月份与当前月份情况", tripGuide.sections.season);
  document.getElementById("packing").innerHTML = renderSection("当前月份穿衣与必备物品", tripGuide.sections.packing);
  document.getElementById("transport").innerHTML = renderSection("交通方式", tripGuide.sections.transport);
  document.getElementById("sources").innerHTML = renderSection("信息源", tripGuide.sections.sources);
</script>
```

- [ ] **Step 4: Run the regression script and verify it passes**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected: PASS with `travel guide regression checks passed`.

- [ ] **Step 5: Commit the mobile guide**

```bash
git add trips/jilin-yanji-changbaishan/mobile/index.html trips/jilin-yanji-changbaishan/mobile/mobile.css trips/jilin-yanji-changbaishan/assets/render-guide.js
git commit -m "feat: add mobile paginated jilin travel guide"
```

### Task 7: Run Render QA And Final Polish

**Files:**
- Modify: `tests/playwright_trip_render_check.py`
- Modify: `trips/jilin-yanji-changbaishan/desktop/index.html`
- Modify: `trips/jilin-yanji-changbaishan/mobile/index.html`
- Modify: `trips/jilin-yanji-changbaishan/desktop/desktop.css`
- Modify: `trips/jilin-yanji-changbaishan/mobile/mobile.css`
- Test: `tests/travel-guide-regression.ps1`
- Test: `tests/playwright_trip_render_check.py`

- [ ] **Step 1: Extend the Playwright checker with expected section IDs**

Add this assertion block inside `inspect_page` usage after the report is collected:

```python
required_sections = {"overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources"}

for page_name, page_results in report.items():
    for label, result in page_results.items():
        found_ids = {section["id"] for section in result["sections"] if section["id"]}
        missing = sorted(required_sections - found_ids)
        if missing:
            raise AssertionError(f"{page_name} {label} missing sections: {missing}")
        if result["docScrollWidth"] > result["viewportWidth"] + 1:
            raise AssertionError(f"{page_name} {label} has horizontal overflow")
```

- [ ] **Step 2: Run the static regression and the render check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\travel-guide-regression.ps1 -Root .
```

Expected:

```text
travel guide regression checks passed
```

Run:

```powershell
python .\tests\playwright_trip_render_check.py
```

Expected: JSON output with entries for both:

```text
desktop\index.html
mobile\index.html
```

- [ ] **Step 3: Fix any overflow, missing-section, or pagination issues**

If the render report shows horizontal overflow or weak section heights, apply these fixes:

```css
img,
table,
.card-grid,
.nav-strip{
  max-width:100%;
}

table{
  display:block;
  overflow:auto;
}

@media (max-width:720px){
  .nav-strip{
    overflow-x:auto;
    flex-wrap:nowrap;
  }
}
```

Keep the content parity intact while adjusting layout only.

- [ ] **Step 4: Run whitespace and diff sanity checks**

Run:

```powershell
git diff --check -- travel-planning-playbook.md tests/travel-guide-regression.ps1 tests/playwright_trip_render_check.py trips/jilin-yanji-changbaishan
```

Expected: no output.

- [ ] **Step 5: Commit final QA and polish**

```bash
git add travel-planning-playbook.md tests/travel-guide-regression.ps1 tests/playwright_trip_render_check.py trips/jilin-yanji-changbaishan
git commit -m "fix: finalize travel playbook and jilin guide outputs"
```

## Self-Review

### Spec coverage

- Playbook rewritten as an execution manual: Task 2
- Required intake, research order, itinerary generation, HTML order, image rules, checklist: Task 2
- Separate Jilin output directory with desktop/mobile/notes: Task 3
- Shared content source to keep desktop/mobile aligned: Task 3 and Task 4
- Daily itinerary near the front: Task 5 and Task 6 via `overview` and `recommended`
- Multiple plans with one explicitly recommended: Task 4, Task 5, Task 6
- Image-placement plan as a separate artifact: Task 3 and Task 4
- Regression and browser validation: Task 1 and Task 7

No spec gaps found.

### Placeholder scan

Searched mentally for `TODO`, `TBD`, “implement later,” or vague “add validation” language. The plan uses exact file paths, headings, commands, and starter content. No unresolved placeholder wording remains.

### Type consistency

- Shared content object is always `tripGuide`
- Shared renderer namespace is always `window.tripGuideRenderer`
- Required section IDs are always `overview`, `recommended`, `options`, `attractions`, `food`, `season`, `packing`, `transport`, `sources`
- Desktop and mobile both consume the same section keys

No naming conflicts found.

