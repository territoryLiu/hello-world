# Travel Skill Single-Template Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `travel-skill`'s old five-template render architecture with a single `editorial` template while keeping the existing `<device>/<template-id>/index.html` output directory contract.

**Architecture:** This refactor changes the render pipeline, shared template config, template assets, and downstream portal/package/verify logic together. The new steady state is one real template ID (`editorial`) rendered for desktop and mobile, with all former five-template assumptions removed from Python scripts, asset files, and sharing documentation.

**Tech Stack:** Python 3, Markdown, HTML, CSS, JavaScript, PowerShell, git, ripgrep

---

### Task 1: Collapse template configuration to `editorial`

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/travel_config.py`
- Test: `.codex/skills/travel-skill/scripts/travel_config.py`

- [ ] **Step 1: Inspect the current template config**

Run:

```powershell
Get-Content '.codex\skills\travel-skill\scripts\travel_config.py' -Encoding UTF8
```

Expected: the file still defines five template IDs and five section mappings.

- [ ] **Step 2: Rewrite the template constants to a single-template config**

Apply a patch to `.codex/skills/travel-skill/scripts/travel_config.py` so the template-related section becomes:

```python
TEMPLATE_IDS = [
    "editorial",
]
SORTED_TEMPLATE_IDS = sorted(TEMPLATE_IDS)

TEMPLATE_LABELS = {
    "editorial": "杂志版",
}

TEMPLATE_SECTIONS = {
    "editorial": [
        "recommended_route",
        "route_options",
        "clothing_guide",
        "attractions",
        "transport_details",
        "food_by_city",
        "tips",
        "sources",
    ],
}
```

- [ ] **Step 3: Verify there are no old template names left in the config**

Run:

```powershell
rg -n "route-first|decision-first|destination-first|transport-first|lifestyle-first" '.codex\skills\travel-skill\scripts\travel_config.py'
```

Expected: no matches.

- [ ] **Step 4: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/scripts/travel_config.py'
git commit -m "refactor: 收敛 travel-skill 模板配置为 editorial"
```

Expected: one commit recording the single-template config switch.

### Task 2: Replace five-template HTML assets with one editorial template

**Files:**
- Create: `.codex/skills/travel-skill/assets/templates/template-editorial.html`
- Modify: `.codex/skills/travel-skill/assets/templates/base.css`
- Modify: `.codex/skills/travel-skill/assets/templates/render-guide.js`
- Delete: `.codex/skills/travel-skill/assets/templates/template-route-first.html`
- Delete: `.codex/skills/travel-skill/assets/templates/template-decision-first.html`
- Delete: `.codex/skills/travel-skill/assets/templates/template-destination-first.html`
- Delete: `.codex/skills/travel-skill/assets/templates/template-transport-first.html`
- Delete: `.codex/skills/travel-skill/assets/templates/template-lifestyle-first.html`
- Test: `.codex/skills/travel-skill/assets/templates/template-editorial.html`
- Test: `.codex/skills/travel-skill/assets/templates/base.css`

- [ ] **Step 1: Create the new single-template HTML shell**

Create `.codex/skills/travel-skill/assets/templates/template-editorial.html` with a structure that keeps the `Guide Contract` section order intact. The file should look like:

```html
<header class="hero hero-editorial">{{ hero }}</header>
<main class="layout-editorial">
  <section class="editorial-lead">{{ daily_overview }}</section>
  <section class="editorial-section editorial-primary">{{ recommended_route }}</section>
  <section class="editorial-section">{{ route_options }}</section>
  <section class="editorial-section">{{ clothing_guide }}</section>
  <section class="editorial-section">{{ attractions }}</section>
  <section class="editorial-section">{{ transport_details }}</section>
  <section class="editorial-section">{{ food_by_city }}</section>
  <section class="editorial-section">{{ tips }}</section>
  <section class="editorial-section">{{ sources }}</section>
</main>
```

The important constraint is that the main section placeholders appear in the order above.

- [ ] **Step 2: Rewrite `base.css` for the editorial baseline**

Update `.codex/skills/travel-skill/assets/templates/base.css` so it no longer encodes five-template-specific layout classes. The stylesheet should include selectors for:

```css
.layout-editorial
.hero-editorial
.editorial-lead
.editorial-section
.page-shell
.section-nav
.section-block
.timeline-stack
.transport-matrix
.source-card
```

And it should not contain class names such as:

```text
.layout-route-first
.layout-decision-first
.layout-destination-first
.layout-transport-first
.layout-lifestyle-first
```

- [ ] **Step 3: Keep `render-guide.js` minimal and template-agnostic**

Review `.codex/skills/travel-skill/assets/templates/render-guide.js` and keep only generic helpers. If no five-template logic exists, do not bloat it; just ensure it remains template-agnostic and readable.

- [ ] **Step 4: Delete the five obsolete HTML template files**

Remove these files:

```text
.codex/skills/travel-skill/assets/templates/template-route-first.html
.codex/skills/travel-skill/assets/templates/template-decision-first.html
.codex/skills/travel-skill/assets/templates/template-destination-first.html
.codex/skills/travel-skill/assets/templates/template-transport-first.html
.codex/skills/travel-skill/assets/templates/template-lifestyle-first.html
```

- [ ] **Step 5: Verify the asset directory only contains the new template**

Run:

```powershell
Get-ChildItem '.codex\skills\travel-skill\assets\templates' | Select-Object Name
```

Expected: the directory contains `template-editorial.html`, `base.css`, `render-guide.js`, and any intentionally retained shared files, but none of the five deleted template HTML files.

- [ ] **Step 6: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/assets/templates'
git commit -m "refactor: 替换 travel-skill 五模板资产为 editorial"
```

Expected: one commit recording the asset replacement.

### Task 3: Rewrite `render_trip_site.py` to a single-template renderer

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Test: `.codex/skills/travel-skill/scripts/render_trip_site.py`

- [ ] **Step 1: Remove five-template style branching**

Edit `.codex/skills/travel-skill/scripts/render_trip_site.py` so `STYLE_THEMES` is replaced by a single `EDITORIAL_THEME`, for example:

```python
EDITORIAL_THEME = {
    "font": '"Source Han Serif SC", "STSong", serif',
    "accent": "#8c4b2e",
    "bg": "#f3ede3",
    "surface": "#fffaf4",
    "ink": "#241d16",
}
```

And update `_style_override_css()` to use `EDITORIAL_THEME` directly instead of looking up by template ID.

- [ ] **Step 2: Make template loading always target `template-editorial.html`**

Change `_apply_template()` so it no longer accepts arbitrary `template_id`. Replace:

```python
def _apply_template(template_id: str, replacements: dict[str, str]) -> str:
    template_html = _load_asset(f"template-{template_id}.html")
```

with:

```python
def _apply_template(replacements: dict[str, str]) -> str:
    template_html = _load_asset("template-editorial.html")
```

Update all callers accordingly.

- [ ] **Step 3: Restrict rendering to `editorial` only**

Rewrite the template-selection logic in `render_site()` so it becomes:

```python
selected_templates = ["editorial"]
if args_style := (style or "").strip():
    if args_style not in {"all", "default", "editorial"}:
        raise ValueError(f"unsupported render style: {args_style}")
```

Then generate only:

```python
guide_root / "desktop" / "editorial" / "index.html"
guide_root / "mobile" / "editorial" / "index.html"
```

- [ ] **Step 4: Keep section order aligned with `Guide Contract`**

In `_render_template_page()`, ensure `section_ids = TEMPLATE_SECTIONS["editorial"]` and that placeholder insertion still preserves:

```text
recommended_route
route_options
clothing_guide
attractions
transport_details
food_by_city
tips
sources
```

`daily_overview` may still appear as an introductory block, but not in a way that reorders the main section sequence.

- [ ] **Step 5: Run a syntax-level verification**

Run:

```powershell
python -m py_compile '.codex\skills\travel-skill\scripts\render_trip_site.py' '.codex\skills\travel-skill\scripts\travel_config.py'
```

Expected: command exits successfully with no output.

- [ ] **Step 6: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/scripts/render_trip_site.py' '.codex/skills/travel-skill/scripts/travel_config.py'
git commit -m "refactor: 改造 travel-skill 为单模板渲染"
```

Expected: one commit recording the render core rewrite.

### Task 4: Update portal, package, and verify for single-template output

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/build_portal.py`
- Modify: `.codex/skills/travel-skill/scripts/package_trip.py`
- Modify: `.codex/skills/travel-skill/scripts/verify_trip.py`
- Test: `.codex/skills/travel-skill/scripts/build_portal.py`
- Test: `.codex/skills/travel-skill/scripts/package_trip.py`
- Test: `.codex/skills/travel-skill/scripts/verify_trip.py`

- [ ] **Step 1: Rewrite the portal copy and template listing expectations**

Update `.codex/skills/travel-skill/scripts/build_portal.py` so:

```text
- no copy says "固定只发布五套模板版本"
- no copy says "路线优先单文件"
- desktop/mobile groups still enumerate existing template directories
- share copy describes `share.html` as the complete single-file share version
```

The hero paragraph should read like:

```text
这里汇总当前默认杂志版的桌面端、手机端、单文件分享页、来源说明和 ZIP 交付入口。
```

- [ ] **Step 2: Rewrite package summary language**

Update `.codex/skills/travel-skill/scripts/package_trip.py` so `build_summary()` emits:

```text
templates: editorial
- share.html 是优先转发的完整单文件分享版。
- recommended.html 是当前主推荐分享入口。
```

and no longer mentions a “路线优先阅读版本”.

- [ ] **Step 3: Rewrite verification for single-template expectations**

Update `.codex/skills/travel-skill/scripts/verify_trip.py` so the checks become:

```python
"desktop_template_complete": desktop_templates == ["editorial"],
"mobile_template_complete": mobile_templates == ["editorial"],
"single_template_is_editorial": desktop_templates == ["editorial"] and mobile_templates == ["editorial"],
```

Remove:

```python
"exactly_five_templates"
```

and any equality check against the old five-template list.

- [ ] **Step 4: Run syntax verification on the downstream scripts**

Run:

```powershell
python -m py_compile '.codex\skills\travel-skill\scripts\build_portal.py' '.codex\skills\travel-skill\scripts\package_trip.py' '.codex\skills\travel-skill\scripts\verify_trip.py'
```

Expected: command exits successfully with no output.

- [ ] **Step 5: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/scripts/build_portal.py' '.codex/skills/travel-skill/scripts/package_trip.py' '.codex/skills/travel-skill/scripts/verify_trip.py'
git commit -m "refactor: 同步单模板渲染下的 portal package verify"
```

Expected: one commit recording downstream script alignment.

### Task 5: Update sharing docs and validate old-template removal

**Files:**
- Modify: `.codex/skills/travel-skill/references/sharing-modes.md`
- Modify: `docs/superpowers/specs/2026-04-14-travel-skill-single-template-render-design.md`
- Test: `.codex/skills/travel-skill/references/sharing-modes.md`
- Test: `.codex/skills/travel-skill`

- [ ] **Step 1: Rewrite sharing documentation to the `editorial` paths**

Update `.codex/skills/travel-skill/references/sharing-modes.md` so its concrete examples use:

```text
guides/<slug>/desktop/editorial/index.html
guides/<slug>/mobile/editorial/index.html
```

and no longer list the five old template directories.

- [ ] **Step 2: Mark the render spec as implementation-ready**

Update `docs/superpowers/specs/2026-04-14-travel-skill-single-template-render-design.md`:

```md
状态：approved-for-implementation
```

- [ ] **Step 3: Run a repo-wide old-template search**

Run:

```powershell
rg -n "route-first|decision-first|destination-first|transport-first|lifestyle-first|固定只发布五套模板|exactly_five_templates" '.codex\skills\travel-skill' 'docs\superpowers\specs\2026-04-14-travel-skill-single-template-render-design.md'
```

Expected: no matches, except possibly historical references outside the files changed in this plan. If any live implementation file still matches, fix it before continuing.

- [ ] **Step 4: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/references/sharing-modes.md' 'docs/superpowers/specs/2026-04-14-travel-skill-single-template-render-design.md'
git commit -m "docs: 更新 travel-skill 单模板分享说明"
```

Expected: one commit recording the new sharing and spec status.

### Task 6: Run a minimal end-to-end render validation

**Files:**
- Test: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Test: `.codex/skills/travel-skill/scripts/build_portal.py`
- Test: `.codex/skills/travel-skill/scripts/package_trip.py`
- Test: `.codex/skills/travel-skill/scripts/verify_trip.py`

- [ ] **Step 1: Confirm available Python environments before running scripts**

Run:

```powershell
conda env list
```

Expected: list of available environments. Prefer an existing environment that already has Python and no extra package needs for these pure-stdlib scripts.

- [ ] **Step 2: Build a minimal fixture payload**

Create a temporary JSON file at `.tmp/travel-skill-editorial-fixture.json` with this content:

```json
{
  "meta": {
    "trip_slug": "editorial-fixture",
    "title": "杂志版渲染夹具",
    "checked_at": "2026-04-14",
    "source_count": 1
  },
  "outputs": {
    "daily-overview": {
      "summary": "用于单模板渲染最小验证。",
      "days": [{"title": "Day 1", "summary": "抵达与入城", "points": ["入住", "晚餐"]}],
      "wearing": [{"title": "穿衣", "summary": "早晚偏凉", "points": ["薄外套"]}],
      "transport": [{"title": "交通", "summary": "高铁进城", "points": ["地铁接驳"]}],
      "alerts": [{"title": "提醒", "summary": "提前预约", "points": ["核对天气"]}]
    },
    "recommended": {
      "recommended_route": [{"title": "主线", "summary": "轻松主线", "points": ["第一天核心动线"]}],
      "route_options": [{"title": "备选", "summary": "更省钱", "points": ["换乘方案"]}],
      "clothing_guide": [{"title": "装备", "summary": "分层穿着", "points": ["轻薄冲锋衣"]}],
      "attractions": [{"title": "景点", "summary": "主景点", "points": ["早到避峰"]}],
      "transport_details": [{"title": "交通细节", "summary": "站点与接驳", "points": ["出租车备用"]}],
      "food_by_city": [{"title": "美食", "summary": "本地馆子", "points": ["午餐店"]}],
      "tips": [{"title": "提示", "summary": "排队与预约", "points": ["提前 3 天"]}],
      "sources": [{"title": "官方来源", "site": "official", "topic": "transport", "type": "web", "checked_at": "2026-04-14", "url": "https://example.com"}]
    },
    "comprehensive": {}
  },
  "sources": [
    {"title": "官方来源", "site": "official", "topic": "transport", "type": "web", "checked_at": "2026-04-14", "url": "https://example.com"}
  ],
  "image_plan": {}
}
```

- [ ] **Step 3: Run the render script**

Use the selected existing Python environment to run:

```powershell
python '.codex\skills\travel-skill\scripts\render_trip_site.py' --input '.tmp\travel-skill-editorial-fixture.json' --output-root '.tmp\travel-render-output' --style editorial
```

Expected: output is created under:

```text
.tmp/travel-render-output/guides/editorial-fixture/desktop/editorial/index.html
.tmp/travel-render-output/guides/editorial-fixture/mobile/editorial/index.html
```

- [ ] **Step 4: Run portal and verify scripts**

Run:

```powershell
python '.codex\skills\travel-skill\scripts\build_portal.py' --guide-root '.tmp\travel-render-output\guides\editorial-fixture' --output '.tmp\travel-render-output\portal.html'
python '.codex\skills\travel-skill\scripts\verify_trip.py' --guide-root '.tmp\travel-render-output\guides\editorial-fixture' --output '.tmp\travel-render-output\verify.json'
```

Expected:
- portal builds successfully
- `verify.json` reports the single-template checks
- if Playwright downgrades to warn, the overall content checks should still reflect the new single-template logic

- [ ] **Step 5: Inspect the rendered file layout**

Run:

```powershell
Get-ChildItem -Recurse '.tmp\travel-render-output\guides\editorial-fixture' | Select-Object FullName
Get-Content '.tmp\travel-render-output\verify.json' -Encoding UTF8
```

Expected:
- only `desktop\editorial` and `mobile\editorial` template directories exist
- `sources.md` and `sources.html` exist
- verification output contains no `exactly_five_templates` field

- [ ] **Step 6: Commit**

Run:

```powershell
git add -- '.codex/skills/travel-skill/scripts' '.codex/skills/travel-skill/assets/templates' '.codex/skills/travel-skill/references/sharing-modes.md' 'docs/superpowers/specs/2026-04-14-travel-skill-single-template-render-design.md'
git commit -m "refactor: 拆除 travel-skill 五模板渲染体系"
```

Expected: final implementation commit after the end-to-end validation passes.

## Self-Review

### Spec coverage

- Spec sections 2 and 5 map to Task 1, Task 2, and Task 3.
- Spec section 6 file-level changes map to Task 1 through Task 5.
- Spec section 7 content-order constraints map to Task 2 and Task 3.
- Spec section 8 migration strategy maps to Task 2 through Task 5.
- Spec section 10 acceptance criteria map across all six tasks.

No spec requirement is left without a corresponding task.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- All file paths are explicit.
- All verification steps include exact commands and expected outcomes.

### Type consistency

- The only target template ID is consistently named `editorial`.
- Render, portal, verify, and package all refer to the same output directory contract.
- The fixture and verification expectations both assume `desktop/editorial` and `mobile/editorial`.

