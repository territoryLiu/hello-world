# Travel Skill V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing repo-local `travel-skill` from the stage-one single-guide flow into the V2 multi-layer travel production system defined in the approved design spec.

**Architecture:** Extend the current scripts in `.codex/skills/travel-skill/scripts/` instead of creating a second pipeline. Keep the flow staged and file-based: intake produces a stricter request contract, research persists raw and normalized notes by place and topic, compose outputs three content models, render outputs desktop and mobile pages for all three layers, then share packaging builds portal and single-file exports on top of those generated artifacts.

**Tech Stack:** Python standard library, Markdown, JSON, HTML, CSS, vanilla JavaScript, repo-local Codex skill metadata, unittest, existing Playwright Python checker, existing conda environment (`py313`)

---

## File Structure

Planned file ownership before task breakdown:

- Modify: `.codex/skills/travel-skill/SKILL.md`
  Keep the skill entrypoint aligned with the V2 eight-stage workflow and updated artifact expectations.
- Modify: `.codex/skills/travel-skill/references/content-schema.md`
  Declare the V2 object contracts for request, research storage, layered content models, share outputs, and source records.
- Modify: `.codex/skills/travel-skill/references/research-checklists.md`
  Add required topic coverage for weather, clothing, packing, transport, attractions, food, seasonality, risks, and sources.
- Modify: `.codex/skills/travel-skill/references/sharing-modes.md`
  Document `portal.html`, single-file exports, ZIP bundle, and optional static URL.
- Modify: `.codex/skills/travel-skill/scripts/normalize_request.py`
  Enforce V2 intake fields, missing-field reporting, traveler profile structure, and output defaults.
- Modify: `.codex/skills/travel-skill/scripts/build_research_tasks.py`
  Expand research tasks by place, topic, and platform rather than only by coarse category.
- Modify: `.codex/skills/travel-skill/scripts/merge_sources.py`
  Persist normalized notes with place/topic grouping metadata and stable source identity.
- Modify: `.codex/skills/travel-skill/scripts/extract_structured_facts.py`
  Produce fact items that retain place, topic, source, checked date, and display-ready transport/store/scenic fields.
- Modify: `.codex/skills/travel-skill/scripts/generate_review_packet.py`
  Present V2 review packets with sectioned source summaries and explicit checked-at language.
- Modify: `.codex/skills/travel-skill/scripts/build_guide_model.py`
  Build three content models: `daily-overview`, `recommended`, and `comprehensive`.
- Modify: `.codex/skills/travel-skill/scripts/fill_missing_sections.py`
  Backfill required V2 sections without breaking layered output contracts.
- Modify: `.codex/skills/travel-skill/scripts/render_trip_site.py`
  Render six HTML outputs under `desktop/` and `mobile/`, with shared assets and theme hooks.
- Create: `.codex/skills/travel-skill/scripts/collect_media_candidates.py`
  Structure social/video notes into reusable media candidate JSON.
- Create: `.codex/skills/travel-skill/scripts/build_image_plan.py`
  Convert media candidates into page-level image recommendations.
- Create: `.codex/skills/travel-skill/scripts/build_portal.py`
  Generate the single-file portal entry and link all share artifacts.
- Modify: `.codex/skills/travel-skill/scripts/export_single_html.py`
  Support exporting `recommended.html` and `comprehensive.html` from layered outputs.
- Modify: `.codex/skills/travel-skill/scripts/package_trip.py`
  Include portal, single-file guides, notes, and summary manifest in the ZIP.
- Modify: `.codex/skills/travel-skill/scripts/verify_trip.py`
  Verify six rendered pages plus share artifacts.
- Modify: `.codex/skills/travel-skill/assets/templates/desktop-index.html`
- Modify: `.codex/skills/travel-skill/assets/templates/mobile-index.html`
- Modify: `.codex/skills/travel-skill/assets/templates/base.css`
- Modify: `.codex/skills/travel-skill/assets/templates/render-guide.js`
  Template set for V2 desktop/mobile layered rendering with theme slots.
- Create: `.codex/skills/travel-skill/assets/templates/portal.html`
  Portal page template linking layered outputs and share files.
- Modify: `tests/fixtures/travel_skill/trip_request_raw.json`
- Modify: `tests/fixtures/travel_skill/source_notes.json`
- Modify: `tests/fixtures/travel_skill/approved_research.json`
  Update fixtures to cover traveler ages, packing, transport variants, store metadata, and V2 layer expectations.
- Modify: `tests/travel_skill/test_contract.py`
- Modify: `tests/travel_skill/test_intake_research.py`
- Modify: `tests/travel_skill/test_research_packet.py`
- Modify: `tests/travel_skill/test_compose.py`
- Modify: `tests/travel_skill/test_render_package.py`
- Modify: `tests/travel_skill/test_verify.py`
  Regression suite for the upgraded contract.
- Modify: `tests/playwright_trip_render_check.py`
  Verify layered desktop/mobile outputs instead of one page per device.
- Modify: `docs/superpowers/plans/2026-04-11-travel-skill-v2-implementation.md`
  Record the migration of useful `docs/pipe` rules into travel-skill references and the runtime environment policy.

## Migrated From `docs/pipe`

Useful rules from `docs/pipe` are absorbed into `travel-skill` itself rather than kept as a separate folder:

- intake checklist for travelers, dates, budget, approvals, and output form
- research order and delivery notes structure
- stable HTML section order and ASCII section ids
- desktop/mobile/assets/notes output layout
- pre-delivery regression checks

`docs/pipe` can be removed after these rules are represented in `travel-skill` references and plan files.

## Python Runtime Policy

- Prefer an existing conda environment for travel-skill Python commands.
- Current preferred environment: `py313`
- Browser verification fallback environment: `paper2any`
- If a package is missing, install it from `https://pypi.tuna.tsinghua.edu.cn/simple`

### Task 1: Tighten The V2 Intake Contract And Research Planner

**Files:**
- Modify: `.codex/skills/travel-skill/references/content-schema.md`
- Modify: `.codex/skills/travel-skill/references/research-checklists.md`
- Modify: `.codex/skills/travel-skill/scripts/normalize_request.py`
- Modify: `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- Modify: `tests/fixtures/travel_skill/trip_request_raw.json`
- Modify: `tests/travel_skill/test_contract.py`
- Modify: `tests/travel_skill/test_intake_research.py`
- Test: `tests/travel_skill/test_contract.py`
- Test: `tests/travel_skill/test_intake_research.py`

- [ ] **Step 1: Write failing tests for the stricter V2 request and task contract**

Update `tests/travel_skill/test_intake_research.py` with assertions like:

```python
self.assertEqual(
    payload["missing_core_fields"],
    [],
)
self.assertEqual(
    payload["traveler_profile"],
    {
        "adults": 3,
        "children": 1,
        "age_notes": "1 位 7 岁儿童，2 位 60+ 长辈",
    },
)
self.assertEqual(
    payload["research_dimensions"],
    ["place", "topic", "platform"],
)
self.assertIn("city_transport", [task["topic"] for task in expanded["tasks"]])
self.assertIn("packing", [task["topic"] for task in expanded["tasks"]])
```

Update `tests/travel_skill/test_contract.py` with checks like:

```python
content_schema = (SKILL_DIR / "references" / "content-schema.md").read_text(encoding="utf-8")
for needle in ["trip_request", "research_task", "fact_item", "daily-overview", "comprehensive"]:
    self.assertIn(needle, content_schema)
```

- [ ] **Step 2: Run the intake and contract tests to verify they fail first**

Run: `python -m unittest discover -s tests/travel_skill -p test_intake_research.py -v`
Expected: FAIL because the current normalized request has no `missing_core_fields`, `traveler_profile`, or per-topic research tasks.

Run: `python -m unittest discover -s tests/travel_skill -p test_contract.py -v`
Expected: FAIL because the reference docs do not yet mention the V2 contracts and layer names.

- [ ] **Step 3: Implement the V2 intake shape and per-dimension research expansion**

In `.codex/skills/travel-skill/scripts/normalize_request.py`, move the normalized output toward:

```python
CORE_FIELDS = [
    "title",
    "departure_city",
    "destinations",
    "date_range",
    "travelers",
    "budget",
]

TOPIC_DEFAULTS = [
    "weather",
    "clothing",
    "packing",
    "long_distance_transport",
    "city_transport",
    "attractions",
    "tickets_and_booking",
    "food",
    "lodging_area",
    "seasonality",
    "risks",
    "sources",
]

normalized = {
    "title": payload["title"],
    "trip_slug": slugify(payload["title"]),
    "departure_city": payload["departure_city"],
    "destinations": payload.get("destinations", []),
    "date_range": payload["date_range"],
    "travelers": payload["travelers"],
    "traveler_profile": {
        "adults": payload["travelers"].get("adults", payload["travelers"].get("count", 0)),
        "children": payload["travelers"].get("children", 0),
        "age_notes": payload["travelers"].get("age_notes", ""),
    },
    "budget": payload["budget"],
    "preferences": {
        "transport": payload.get("transport_preference", ""),
        "stay": payload.get("stay_preference", ""),
        "pace": payload.get("pace_preference", ""),
    },
    "required_topics": payload.get("required_topics", TOPIC_DEFAULTS),
    "missing_core_fields": [field for field in CORE_FIELDS if field not in payload],
    "missing_preference_fields": [field for field in ["must_go", "transport_preference"] if field not in payload],
    "research_dimensions": ["place", "topic", "platform"],
    "share_mode": payload.get("share_mode", "single-html"),
    "review_mode": payload.get("review_mode", "manual-gate"),
}
```

In `.codex/skills/travel-skill/scripts/build_research_tasks.py`, expand tasks like:

```python
PLATFORM_MAP = {
    "weather": ["official", "history"],
    "clothing": ["history", "social"],
    "packing": ["official", "social"],
    "long_distance_transport": ["official", "platform"],
    "city_transport": ["official", "map"],
    "tickets_and_booking": ["official"],
    "attractions": ["official", "social"],
    "food": ["local-listing", "social"],
    "lodging_area": ["platform", "map"],
    "seasonality": ["official", "social"],
    "risks": ["official", "social"],
    "sources": ["official", "social"],
}
```

- [ ] **Step 4: Re-run the tests and verify the new contract passes**

Run: `python -m unittest discover -s tests/travel_skill -p test_intake_research.py -v`
Expected: PASS with normalized request and task expansion assertions succeeding.

Run: `python -m unittest discover -s tests/travel_skill -p test_contract.py -v`
Expected: PASS with updated schema keywords present.

- [ ] **Step 5: Commit the intake and planner upgrade**

```bash
git add .codex/skills/travel-skill/references/content-schema.md .codex/skills/travel-skill/references/research-checklists.md .codex/skills/travel-skill/scripts/normalize_request.py .codex/skills/travel-skill/scripts/build_research_tasks.py tests/fixtures/travel_skill/trip_request_raw.json tests/travel_skill/test_contract.py tests/travel_skill/test_intake_research.py
git commit -m "feat: 升级 travel skill intake 与 research 规划"
```

### Task 2: Persist Research By Place And Topic, Including Media Candidates

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/merge_sources.py`
- Modify: `.codex/skills/travel-skill/scripts/extract_structured_facts.py`
- Modify: `.codex/skills/travel-skill/scripts/generate_review_packet.py`
- Create: `.codex/skills/travel-skill/scripts/collect_media_candidates.py`
- Create: `.codex/skills/travel-skill/scripts/build_image_plan.py`
- Modify: `tests/fixtures/travel_skill/source_notes.json`
- Modify: `tests/travel_skill/test_research_packet.py`
- Test: `tests/travel_skill/test_research_packet.py`

- [ ] **Step 1: Write failing tests for place/topic storage and media extraction**

Update `tests/travel_skill/test_research_packet.py` to assert outputs like:

```python
self.assertEqual(payload["summary"]["topics"], ["food", "long_distance_transport", "risks"])
self.assertIn("yanji", payload["normalized"])
self.assertIn("food", payload["normalized"]["yanji"])
self.assertEqual(media_payload["items"][0]["platform"], "xiaohongshu")
self.assertIn("timeline", media_payload["items"][0])
self.assertIn("recommended_usage", media_payload["items"][0])
```

- [ ] **Step 2: Run the research packet tests and confirm the current pipeline is short of V2**

Run: `python -m unittest discover -s tests/travel_skill -p test_research_packet.py -v`
Expected: FAIL because the merged payload is still category-flat and there are no media candidate/image plan scripts yet.

- [ ] **Step 3: Implement grouped research storage, review output, and media planning helpers**

Refactor `.codex/skills/travel-skill/scripts/merge_sources.py` so each entry retains:

```python
entry = {
    "place": raw["place"],
    "topic": raw["topic"],
    "platform": raw["platform"],
    "title": raw["title"],
    "url": raw["url"],
    "checked_at": raw["checked_at"],
    "source_type": raw["source_type"],
    "facts": deduped_facts,
}
```

Refactor `.codex/skills/travel-skill/scripts/extract_structured_facts.py` toward:

```python
fact_item = {
    "place": entry["place"],
    "topic": entry["topic"],
    "text": fact_text,
    "source_url": entry["url"],
    "source_title": entry["title"],
    "source_type": entry["source_type"],
    "platform": entry["platform"],
    "checked_at": entry["checked_at"],
}
```

Create `.codex/skills/travel-skill/scripts/collect_media_candidates.py` with a contract like:

```python
media_item = {
    "platform": raw["platform"],
    "title": raw["title"],
    "author": raw.get("author", ""),
    "published_at": raw.get("published_at", ""),
    "summary": raw.get("summary", ""),
    "comment_highlights": raw.get("comment_highlights", []),
    "transcript": raw.get("transcript", ""),
    "timeline": raw.get("timeline", []),
    "shot_candidates": raw.get("shot_candidates", []),
    "recommended_usage": raw.get("recommended_usage", ""),
}
```

Create `.codex/skills/travel-skill/scripts/build_image_plan.py` to convert media items into:

```python
{
    "cover": {...},
    "section_images": [
        {"section": "recommended", "image_hint": "延吉清晨街景", "source_ref": "..."},
    ],
}
```

- [ ] **Step 4: Re-run research packet tests and verify V2 storage is stable**

Run: `python -m unittest discover -s tests/travel_skill -p test_research_packet.py -v`
Expected: PASS with grouped research, sanitized review packet output, media candidates, and image plan assertions succeeding.

- [ ] **Step 5: Commit the research storage and media layer**

```bash
git add .codex/skills/travel-skill/scripts/merge_sources.py .codex/skills/travel-skill/scripts/extract_structured_facts.py .codex/skills/travel-skill/scripts/generate_review_packet.py .codex/skills/travel-skill/scripts/collect_media_candidates.py .codex/skills/travel-skill/scripts/build_image_plan.py tests/fixtures/travel_skill/source_notes.json tests/travel_skill/test_research_packet.py
git commit -m "feat: 增加 place-topic 研究归档与媒体候选"
```

### Task 3: Compose Three V2 Guide Models From Approved Research

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Modify: `.codex/skills/travel-skill/scripts/fill_missing_sections.py`
- Modify: `tests/fixtures/travel_skill/approved_research.json`
- Modify: `tests/travel_skill/test_compose.py`
- Test: `tests/travel_skill/test_compose.py`

- [ ] **Step 1: Write failing composition tests for `daily-overview`, `recommended`, and `comprehensive`**

Update `tests/travel_skill/test_compose.py` with expectations like:

```python
self.assertEqual(sorted(payload["outputs"].keys()), ["comprehensive", "daily-overview", "recommended"])
self.assertIn("days", payload["outputs"]["daily-overview"])
self.assertIn("transport_options", payload["outputs"]["comprehensive"])
self.assertIn("packing_list", payload["outputs"]["recommended"])
self.assertEqual(payload["meta"]["checked_at"], "2026-04-11")
```

- [ ] **Step 2: Run the compose tests to capture the gap**

Run: `python -m unittest discover -s tests/travel_skill -p test_compose.py -v`
Expected: FAIL because the current model only emits one flat `sections` object.

- [ ] **Step 3: Implement layered guide composition with backward-safe helpers**

Extend `.codex/skills/travel-skill/scripts/build_guide_model.py` around a structure like:

```python
daily_overview = {
    "summary": summary_text,
    "days": daily_items,
    "wearing": wearing_items,
    "transport": transport_items,
    "alerts": alert_items,
    "sources": source_items,
}
recommended = {
    "overview": overview_items,
    "route": route_items,
    "days": day_plan_items,
    "attractions": attraction_items,
    "food": food_items,
    "packing_list": packing_items,
    "sources": source_items,
}
comprehensive = {
    "overview": overview_items,
    "transport_options": all_transport_items,
    "attractions": attraction_items,
    "food_options": all_food_items,
    "lodging": lodging_items,
    "seasonality": season_items,
    "risks": risk_items,
    "sources": source_items,
}

outputs = {
    "daily-overview": daily_overview,
    "recommended": recommended,
    "comprehensive": comprehensive,
}

return {
    "meta": meta,
    "outputs": outputs,
    "sources": source_items,
    "image_plan": payload.get("image_plan", {}),
}
```

Update `.codex/skills/travel-skill/scripts/fill_missing_sections.py` so it fills required subsections per layer, for example:

```python
REQUIRED_DAILY_KEYS = ["summary", "days", "wearing", "transport", "alerts", "sources"]
REQUIRED_RECOMMENDED_KEYS = ["overview", "route", "days", "attractions", "food", "packing_list", "sources"]
REQUIRED_COMPREHENSIVE_KEYS = ["overview", "transport_options", "attractions", "food_options", "lodging", "seasonality", "risks", "sources"]
```

- [ ] **Step 4: Re-run compose tests and verify all three models are emitted cleanly**

Run: `python -m unittest discover -s tests/travel_skill -p test_compose.py -v`
Expected: PASS with all required layer keys populated and placeholders only where allowed.

- [ ] **Step 5: Commit the layered composition model**

```bash
git add .codex/skills/travel-skill/scripts/build_guide_model.py .codex/skills/travel-skill/scripts/fill_missing_sections.py tests/fixtures/travel_skill/approved_research.json tests/travel_skill/test_compose.py
git commit -m "feat: 输出三层 travel guide content model"
```

### Task 4: Render Desktop And Mobile Outputs For All Three Layers

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Modify: `.codex/skills/travel-skill/assets/templates/desktop-index.html`
- Modify: `.codex/skills/travel-skill/assets/templates/mobile-index.html`
- Modify: `.codex/skills/travel-skill/assets/templates/base.css`
- Modify: `.codex/skills/travel-skill/assets/templates/render-guide.js`
- Modify: `tests/travel_skill/test_render_package.py`
- Test: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Write failing render tests for the six-page output structure**

Update `tests/travel_skill/test_render_package.py` to assert:

```python
required = [
    trip_root / "desktop" / "daily-overview" / "index.html",
    trip_root / "desktop" / "recommended" / "index.html",
    trip_root / "desktop" / "comprehensive" / "index.html",
    trip_root / "mobile" / "daily-overview" / "index.html",
    trip_root / "mobile" / "recommended" / "index.html",
    trip_root / "mobile" / "comprehensive" / "index.html",
    trip_root / "assets" / "base.css",
]
```

Add HTML-level checks such as:

```python
self.assertIn("data-layer=\"recommended\"", desktop_html)
self.assertIn("data-device=\"mobile\"", mobile_html)
self.assertIn("--theme-accent", css)
```

- [ ] **Step 2: Run the render/package tests and confirm current rendering is still one-page-per-device**

Run: `python -m unittest discover -s tests/travel_skill -p test_render_package.py -v`
Expected: FAIL because `render_trip_site.py` currently only emits `desktop/index.html` and `mobile/index.html`.

- [ ] **Step 3: Implement layered rendering with shared assets and theme variables**

Refactor `.codex/skills/travel-skill/scripts/render_trip_site.py` so it creates:

```python
for device in ["desktop", "mobile"]:
    for layer_name, layer_payload in payload["outputs"].items():
        output_dir = trip_root / device / layer_name
        output_dir.mkdir(parents=True, exist_ok=True)
        html_text = render_layer(device=device, layer_name=layer_name, payload=layer_payload, meta=payload["meta"])
        (output_dir / "index.html").write_text(html_text, encoding="utf-8")
```

Update `.codex/skills/travel-skill/assets/templates/base.css` to expose theme hooks like:

```css
:root {
  --theme-bg: #f4efe6;
  --theme-surface: #fffaf4;
  --theme-ink: #272117;
  --theme-accent: #9a4b2f;
}
```

Update the mobile template so content is page-grouped instead of content-trimmed:

```html
<section class="mobile-page" data-page="{{PAGE_ID}}">
  <header class="page-head">{{PAGE_TITLE}}</header>
  <div class="page-body">{{PAGE_CONTENT}}</div>
</section>
```

- [ ] **Step 4: Re-run the render/package tests and verify all layered pages exist**

Run: `python -m unittest discover -s tests/travel_skill -p test_render_package.py -v`
Expected: PASS for structure checks before single-file export assertions are expanded in the next task.

- [ ] **Step 5: Commit the V2 renderer and theme hooks**

```bash
git add .codex/skills/travel-skill/scripts/render_trip_site.py .codex/skills/travel-skill/assets/templates/desktop-index.html .codex/skills/travel-skill/assets/templates/mobile-index.html .codex/skills/travel-skill/assets/templates/base.css .codex/skills/travel-skill/assets/templates/render-guide.js tests/travel_skill/test_render_package.py
git commit -m "feat: 渲染三层桌面端与手机端攻略"
```

### Task 5: Build Portal And Share Packages For Recommended And Comprehensive Guides

**Files:**
- Create: `.codex/skills/travel-skill/scripts/build_portal.py`
- Create: `.codex/skills/travel-skill/assets/templates/portal.html`
- Modify: `.codex/skills/travel-skill/scripts/export_single_html.py`
- Modify: `.codex/skills/travel-skill/scripts/package_trip.py`
- Modify: `tests/travel_skill/test_render_package.py`
- Test: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Write failing share tests for `portal.html`, `recommended.html`, and `comprehensive.html`**

Extend `tests/travel_skill/test_render_package.py` with assertions like:

```python
self.assertTrue((dist / "portal.html").exists())
self.assertTrue((dist / "recommended.html").exists())
self.assertTrue((dist / "comprehensive.html").exists())
self.assertIn("recommended.html", names)
self.assertIn("comprehensive.html", names)
self.assertIn("portal.html", names)
```

- [ ] **Step 2: Run the render/package tests and verify the missing share artifacts**

Run: `python -m unittest discover -s tests/travel_skill -p test_render_package.py -v`
Expected: FAIL because the current export step only writes one single-file HTML and the ZIP only includes that file plus notes.

- [ ] **Step 3: Implement the portal builder, layered single-file export, and richer ZIP manifest**

Create `.codex/skills/travel-skill/scripts/build_portal.py` around:

```python
portal_links = {
    "desktop": {
        "daily-overview": "desktop/daily-overview/index.html",
        "recommended": "desktop/recommended/index.html",
        "comprehensive": "desktop/comprehensive/index.html",
    },
    "mobile": {
        "daily-overview": "mobile/daily-overview/index.html",
        "recommended": "mobile/recommended/index.html",
        "comprehensive": "mobile/comprehensive/index.html",
    },
    "share": {
        "recommended": "recommended.html",
        "comprehensive": "comprehensive.html",
    },
}
```

Extend `.codex/skills/travel-skill/scripts/export_single_html.py` to accept a layer selector:

```python
parser.add_argument("--layer", choices=["recommended", "comprehensive"], required=True)
layer_html = (guide_root / "desktop" / args.layer / "index.html").read_text(encoding="utf-8")
```

Extend `.codex/skills/travel-skill/scripts/package_trip.py` so the ZIP includes:

```python
archive.write(dist / "portal.html", arcname="portal.html")
archive.write(dist / "recommended.html", arcname="recommended.html")
archive.write(dist / "comprehensive.html", arcname="comprehensive.html")
archive.write(guide_root / "notes" / "sources.md", arcname="notes/sources.md")
```

- [ ] **Step 4: Re-run share tests and verify the distributable set is complete**

Run: `python -m unittest discover -s tests/travel_skill -p test_render_package.py -v`
Expected: PASS with all share artifacts present and ZIP contents expanded.

- [ ] **Step 5: Commit the share packaging upgrade**

```bash
git add .codex/skills/travel-skill/scripts/build_portal.py .codex/skills/travel-skill/assets/templates/portal.html .codex/skills/travel-skill/scripts/export_single_html.py .codex/skills/travel-skill/scripts/package_trip.py tests/travel_skill/test_render_package.py
git commit -m "feat: 增加攻略入口页与分享包"
```

### Task 6: Verify The V2 Artifact Set And Sync Operator Docs

**Files:**
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Modify: `.codex/skills/travel-skill/references/sharing-modes.md`
- Modify: `.codex/skills/travel-skill/scripts/verify_trip.py`
- Modify: `tests/playwright_trip_render_check.py`
- Modify: `tests/travel_skill/test_verify.py`
- Modify: `docs/pipe/travel-planning-playbook.md`
- Test: `tests/travel_skill/test_verify.py`
- Test: `tests/playwright_trip_render_check.py`

- [ ] **Step 1: Write failing verification and playbook assertions for the V2 output set**

Update `tests/travel_skill/test_verify.py` with checks such as:

```python
self.assertTrue(payload["static_checks"]["desktop_daily_exists"])
self.assertTrue(payload["static_checks"]["desktop_recommended_exists"])
self.assertTrue(payload["static_checks"]["desktop_comprehensive_exists"])
self.assertTrue(payload["static_checks"]["mobile_daily_exists"])
self.assertTrue(payload["static_checks"]["portal_exists"])
self.assertTrue(payload["static_checks"]["recommended_single_exists"])
self.assertTrue(payload["static_checks"]["comprehensive_single_exists"])
```

Update `tests/playwright_trip_render_check.py` to enumerate:

```python
return [
    guide_root / "desktop" / "daily-overview" / "index.html",
    guide_root / "desktop" / "recommended" / "index.html",
    guide_root / "desktop" / "comprehensive" / "index.html",
    guide_root / "mobile" / "daily-overview" / "index.html",
    guide_root / "mobile" / "recommended" / "index.html",
    guide_root / "mobile" / "comprehensive" / "index.html",
]
```

- [ ] **Step 2: Run verification tests to confirm they fail against the old artifact assumptions**

Run: `python -m unittest discover -s tests/travel_skill -p test_verify.py -v`
Expected: FAIL because `verify_trip.py` only checks `desktop/index.html` and `mobile/index.html`.

Run: `python .\tests\playwright_trip_render_check.py --guide-root .\trips\jilin-yanji-changbaishan`
Expected: FAIL until the checker understands the layered directory layout.

- [ ] **Step 3: Implement the V2 verification matrix and update operator docs**

Refactor `.codex/skills/travel-skill/scripts/verify_trip.py` so the static check matrix resembles:

```python
dist_root = guide_root.parent.parent / "dist"
static_checks = {
    "desktop_daily_exists": (guide_root / "desktop" / "daily-overview" / "index.html").exists(),
    "desktop_recommended_exists": (guide_root / "desktop" / "recommended" / "index.html").exists(),
    "desktop_comprehensive_exists": (guide_root / "desktop" / "comprehensive" / "index.html").exists(),
    "mobile_daily_exists": (guide_root / "mobile" / "daily-overview" / "index.html").exists(),
    "mobile_recommended_exists": (guide_root / "mobile" / "recommended" / "index.html").exists(),
    "mobile_comprehensive_exists": (guide_root / "mobile" / "comprehensive" / "index.html").exists(),
    "portal_exists": (dist_root / "portal.html").exists(),
    "recommended_single_exists": (dist_root / "recommended.html").exists(),
    "comprehensive_single_exists": (dist_root / "comprehensive.html").exists(),
    "sources_exists": (guide_root / "notes" / "sources.md").exists(),
}
```

Update `docs/pipe/travel-planning-playbook.md` so the documented flow is:

```markdown
1. intake
2. research-plan
3. research-run
4. review-gate
5. compose
6. render
7. package-share
8. verify
```

- [ ] **Step 4: Run the full regression suite and record the exact passing command set**

Run:

```bash
python -m unittest discover -s tests/travel_skill -p test_contract.py -v
python -m unittest discover -s tests/travel_skill -p test_intake_research.py -v
python -m unittest discover -s tests/travel_skill -p test_research_packet.py -v
python -m unittest discover -s tests/travel_skill -p test_compose.py -v
python -m unittest discover -s tests/travel_skill -p test_render_package.py -v
python -m unittest discover -s tests/travel_skill -p test_verify.py -v
python .\tests\playwright_trip_render_check.py --guide-root .\trips\jilin-yanji-changbaishan
```

Expected: all unittest suites PASS, and the Playwright checker exits with code `0`.

- [ ] **Step 5: Commit the verification and documentation sync**

```bash
git add .codex/skills/travel-skill/SKILL.md .codex/skills/travel-skill/references/sharing-modes.md .codex/skills/travel-skill/scripts/verify_trip.py tests/playwright_trip_render_check.py tests/travel_skill/test_verify.py docs/pipe/travel-planning-playbook.md
git commit -m "feat: 完成 travel skill V2 验证链路"
```

## Self-Review

### Spec Coverage

- V2 三层产物与双端输出: Task 3, Task 4
- 按地点 + 主题的研究落盘: Task 2
- 高时效信息与核对日期口径: Task 1, Task 2, Task 3
- 交通字段、景点字段、店铺字段扩展: Task 2, Task 3
- 手机端分页与桌面端一致性: Task 4
- 单文件分享、入口页、ZIP: Task 5
- skill 分工与操作手册同步: Task 6

### Placeholder Scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Every code-touching step includes explicit file targets, representative code, and test commands.

### Type Consistency

- Layer names are consistently `daily-overview`, `recommended`, `comprehensive`.
- Verification artifact names are consistently `portal.html`, `recommended.html`, and `comprehensive.html`.
- Research dimensions are consistently `place`, `topic`, `platform`.
