# Travel Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repo-local `travel-skill` that can normalize a trip request, generate research tasks and review packets, compose a guide content model, render a maintainable trip site, export a single-file HTML shareable, package a ZIP, and run static/browser verification for the first-stage Jilin workflow.

**Architecture:** Keep the skill inside `.codex/skills/travel-skill/` so it can be committed with the repo and evolve with the travel workflow. Use Python standard-library scripts as the orchestration/runtime layer, reuse the repo's existing HTML/CSS/vanilla-JS trip rendering patterns for generated output, and keep verification split between deterministic Python checks and the existing Playwright render checker. The first stage is intentionally local-first: it must work without adding `package.json`, `pyproject.toml`, or deployment credentials.

**Tech Stack:** Python standard library, Markdown, HTML, CSS, vanilla JavaScript, repo-local Codex skill metadata, existing PowerShell regression checks, existing Playwright Python render checks, Git

---

## File Structure

Planned file ownership before task breakdown:

- Create: `.codex/skills/travel-skill/SKILL.md`
  Repo-local travel skill entrypoint with the six-stage workflow and explicit delegation to `web-access`, `frontend-design`, and `playwright-skill`.
- Create: `.codex/skills/travel-skill/agents/openai.yaml`
  UI metadata for the skill chip and default prompt.
- Create: `.codex/skills/travel-skill/references/source-priority.md`
  Source ranking and writing rules for volatile travel facts.
- Create: `.codex/skills/travel-skill/references/research-checklists.md`
  Checklist for transport, weather, clothing, food, lodging, route pacing, and risk capture.
- Create: `.codex/skills/travel-skill/references/content-schema.md`
  Canonical content model, including required sections plus execution-layer fields.
- Create: `.codex/skills/travel-skill/references/sharing-modes.md`
  Rules for engineering output, single-file shareables, ZIP packaging, and optional static URLs.
- Create: `.codex/skills/travel-skill/references/sample-gap-checklist.md`
  Explicit checklist derived from `sample.html`.
- Create: `.codex/skills/travel-skill/assets/templates/desktop-index.html`
- Create: `.codex/skills/travel-skill/assets/templates/mobile-index.html`
- Create: `.codex/skills/travel-skill/assets/templates/base.css`
- Create: `.codex/skills/travel-skill/assets/templates/render-guide.js`
- Create: `.codex/skills/travel-skill/scripts/normalize_request.py`
- Create: `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- Create: `.codex/skills/travel-skill/scripts/merge_sources.py`
- Create: `.codex/skills/travel-skill/scripts/extract_structured_facts.py`
- Create: `.codex/skills/travel-skill/scripts/generate_review_packet.py`
- Create: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Create: `.codex/skills/travel-skill/scripts/fill_missing_sections.py`
- Create: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Create: `.codex/skills/travel-skill/scripts/export_single_html.py`
- Create: `.codex/skills/travel-skill/scripts/package_trip.py`
- Create: `.codex/skills/travel-skill/scripts/verify_trip.py`
- Create: `tests/travel_skill/helpers.py`
- Create: `tests/travel_skill/test_contract.py`
- Create: `tests/travel_skill/test_intake_research.py`
- Create: `tests/travel_skill/test_research_packet.py`
- Create: `tests/travel_skill/test_compose.py`
- Create: `tests/travel_skill/test_render_package.py`
- Create: `tests/travel_skill/test_verify.py`
- Create: `tests/fixtures/travel_skill/trip_request_raw.json`
- Create: `tests/fixtures/travel_skill/source_notes.json`
- Create: `tests/fixtures/travel_skill/approved_research.json`
- Modify: `tests/playwright_trip_render_check.py`
  Add `--guide-root` so browser verification can target generated guides, not only the hard-coded Jilin path.

### Task 1: Scaffold The Repo-Local Skill And Metadata Contract

**Files:**
- Create: `.codex/skills/travel-skill/SKILL.md`
- Create: `.codex/skills/travel-skill/agents/openai.yaml`
- Create: `.codex/skills/travel-skill/references/source-priority.md`
- Create: `.codex/skills/travel-skill/references/research-checklists.md`
- Create: `.codex/skills/travel-skill/references/content-schema.md`
- Create: `.codex/skills/travel-skill/references/sharing-modes.md`
- Create: `.codex/skills/travel-skill/references/sample-gap-checklist.md`
- Create: `tests/travel_skill/helpers.py`
- Create: `tests/travel_skill/test_contract.py`
- Test: `tests/travel_skill/test_contract.py`

- [ ] **Step 1: Write the failing contract test**

Create `tests/travel_skill/test_contract.py`:

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".codex" / "skills" / "travel-skill"


class TravelSkillContractTest(unittest.TestCase):
    def test_skill_metadata_and_references_exist(self):
        required = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "references" / "source-priority.md",
            SKILL_DIR / "references" / "research-checklists.md",
            SKILL_DIR / "references" / "content-schema.md",
            SKILL_DIR / "references" / "sharing-modes.md",
            SKILL_DIR / "references" / "sample-gap-checklist.md",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [], f"Missing travel skill files: {missing}")

    def test_skill_markdown_mentions_required_flow(self):
        skill_path = SKILL_DIR / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        for needle in ["review-gate", "single-file HTML", "web-access", "frontend-design", "playwright-skill"]:
            self.assertIn(needle, content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract test to verify it fails**

Run: `python -m unittest tests/travel_skill/test_contract.py -v`
Expected: FAIL with `Missing travel skill files`.

- [ ] **Step 3: Create the minimal skill metadata and reference files**

Create `.codex/skills/travel-skill/SKILL.md`:

```markdown
---
name: travel-skill
description: Create travel guides with staged intake, web research, review packets, guide composition, single-file HTML export, ZIP packaging, and verification.
---

# Travel Skill

Run this workflow:
1. `intake`
2. `research`
3. `review-gate`
4. `compose`
5. `render`
6. `package-share`
7. `verify`

Always use `web-access` for online collection, use `frontend-design` when rendering the final guide UI, and use `playwright-skill` or the repo render checker before claiming completion.

Default share target is a single-file HTML plus a ZIP bundle.
```

Create `.codex/skills/travel-skill/agents/openai.yaml`:

```yaml
display_name: Travel Skill
short_description: Build shareable travel guides from research to packaged output
default_prompt: Generate a staged travel guide workflow with research, review, rendering, single-file export, packaging, and verification.
```

Create the reference files with these exact contents:

```markdown
# Source Priority
1. 官方一手源
2. 正规平台公开页面
3. 本地生活平台页
4. 社媒经验内容
- 规则、票务、交通、营业、公告优先写一手源
- 社媒只补体感、避坑、拍照点、排队经验
- 高时效数字必须写核对日期
```

```markdown
# Research Checklists
## Transport
- 大交通主方案
- 大交通备选方案
- 城市内接驳
## Weather
- 历史天气
- 当前体感
- 不确定项复核口径
## Food
- 店名
- 地址片区
- 招牌菜
- 人均区间
```

```markdown
# Content Schema
- `meta`
- `sections.overview`
- `sections.recommended`
- `sections.options`
- `sections.attractions`
- `sections.food`
- `sections.season`
- `sections.packing`
- `sections.transport`
- `sections.sources`
- `execution.booking_order`
- `execution.daily_table`
- `execution.budget_bands`
```

```markdown
# Sharing Modes
- `engineered-site`
- `single-html`
- `zip-bundle`
- `static-url`
```

```markdown
# Sample Gap Checklist
- 订票顺序
- 逐段交通与备选
- 价格区间
- 历史天气体感
- 分层穿衣建议
- 店铺级清单
- 每日执行表
- 预算分档
- 风险与避坑
```

Create `tests/travel_skill/helpers.py`:

```python
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".codex" / "skills" / "travel-skill"
PYTHON = sys.executable


def run_script(*parts):
    cmd = [PYTHON, *(str(part) for part in parts)]
    return subprocess.run(cmd, check=True, capture_output=True, text=True)
```

- [ ] **Step 4: Re-run the contract test and verify it passes**

Run: `python -m unittest tests/travel_skill/test_contract.py -v`
Expected: PASS with two passing tests.

- [ ] **Step 5: Commit the skill scaffold**

```bash
git add .codex/skills/travel-skill tests/travel_skill/helpers.py tests/travel_skill/test_contract.py
git commit -m "feat: 初始化 travel skill 元数据与参考文件"
```

### Task 2: Implement Intake Normalization And Research Task Expansion

**Files:**
- Create: `.codex/skills/travel-skill/scripts/normalize_request.py`
- Create: `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- Create: `tests/fixtures/travel_skill/trip_request_raw.json`
- Create: `tests/travel_skill/test_intake_research.py`
- Test: `tests/travel_skill/test_intake_research.py`

- [ ] **Step 1: Write failing tests for request normalization and task expansion**

Create `tests/fixtures/travel_skill/trip_request_raw.json`:

```json
{
  "title": "五一延吉长白山",
  "departure_city": "南京",
  "date_range": { "start": "2026-04-30", "end": "2026-05-05" },
  "travelers": { "count": 4, "profile": "两男两女，28岁左右" },
  "budget": { "mode": "per_person", "min": 3000, "max": 5000 },
  "stay_preference": "汉庭优先",
  "pace_preference": "接受早起，但不想极限赶路"
}
```

Create `tests/travel_skill/test_intake_research.py`:

```python
from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class IntakeResearchTest(unittest.TestCase):
    def test_normalize_request_sets_defaults(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "normalized.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", output)
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["trip_slug"], "wuyi-yanji-changbaishan")
        self.assertEqual(payload["share_mode"], "single-html")
        self.assertEqual(payload["review_mode"], "manual-gate")
        self.assertEqual(payload["unknown_fields"], ["must_go", "transport_preference"])

    def test_build_research_tasks_expands_core_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks = Path(tmp) / "tasks.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks)
            payload = json.loads(tasks.read_text(encoding="utf-8"))
        categories = [item["category"] for item in payload["tasks"]]
        self.assertEqual(categories, ["transport", "weather", "clothing", "attractions", "food", "lodging", "risk"])
        self.assertEqual(payload["tasks"][0]["required_sources"][0], "official")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m unittest tests/travel_skill/test_intake_research.py -v`
Expected: FAIL because the scripts do not exist yet.

- [ ] **Step 3: Implement the two scripts with deterministic JSON output**

Create `.codex/skills/travel-skill/scripts/normalize_request.py`:

```python
from pathlib import Path
import argparse
import json
import re

DEFAULT_SHARE_MODE = "single-html"
DEFAULT_REVIEW_MODE = "manual-gate"
REQUIRED_OPTIONAL_FIELDS = ["must_go", "transport_preference"]


def slugify(text: str) -> str:
    ascii_map = {"五一": "wuyi", "延吉": "yanji", "长白山": "changbaishan"}
    result = text
    for source, target in ascii_map.items():
        result = result.replace(source, f" {target} ")
    result = re.sub(r"[^a-zA-Z0-9]+", "-", result.lower()).strip("-")
    return re.sub(r"-{2,}", "-", result)


def normalize(payload: dict) -> dict:
    return {
        "title": payload["title"],
        "trip_slug": slugify(payload["title"]),
        "departure_city": payload["departure_city"],
        "date_range": payload["date_range"],
        "travelers": payload["travelers"],
        "budget": payload["budget"],
        "stay_preference": payload.get("stay_preference", ""),
        "pace_preference": payload.get("pace_preference", ""),
        "must_go": payload.get("must_go", []),
        "transport_preference": payload.get("transport_preference", ""),
        "share_mode": payload.get("share_mode", DEFAULT_SHARE_MODE),
        "review_mode": payload.get("review_mode", DEFAULT_REVIEW_MODE),
        "unknown_fields": [key for key in REQUIRED_OPTIONAL_FIELDS if not payload.get(key)],
    }
```

Create `.codex/skills/travel-skill/scripts/build_research_tasks.py`:

```python
from pathlib import Path
import argparse
import json

TASKS = [
    ("transport", ["official", "platform"]),
    ("weather", ["official", "history"]),
    ("clothing", ["history", "social"]),
    ("attractions", ["official", "social"]),
    ("food", ["local-listing", "social"]),
    ("lodging", ["platform", "map"]),
    ("risk", ["official", "social"]),
]


def build_tasks(payload: dict) -> dict:
    tasks = []
    for category, required_sources in TASKS:
        tasks.append({
            "trip_slug": payload["trip_slug"],
            "category": category,
            "required_sources": required_sources,
            "query_hint": f"{payload['departure_city']} {payload['title']} {category}",
        })
    return {"trip_slug": payload["trip_slug"], "tasks": tasks}
```

Each script should read JSON from `--input`, write JSON to `--output`, and call the pure function above from `main()`.

- [ ] **Step 4: Re-run the tests and verify they pass**

Run: `python -m unittest tests/travel_skill/test_intake_research.py -v`
Expected: PASS with two passing tests.

- [ ] **Step 5: Commit intake and research task generation**

```bash
git add .codex/skills/travel-skill/scripts/normalize_request.py .codex/skills/travel-skill/scripts/build_research_tasks.py tests/fixtures/travel_skill/trip_request_raw.json tests/travel_skill/test_intake_research.py
git commit -m "feat: 增加 travel skill intake 与 research 任务编排"
```

### Task 3: Implement Source Merge, Fact Extraction, And Review Packet Generation

**Files:**
- Create: `.codex/skills/travel-skill/scripts/merge_sources.py`
- Create: `.codex/skills/travel-skill/scripts/extract_structured_facts.py`
- Create: `.codex/skills/travel-skill/scripts/generate_review_packet.py`
- Create: `tests/fixtures/travel_skill/source_notes.json`
- Create: `tests/travel_skill/test_research_packet.py`
- Test: `tests/travel_skill/test_research_packet.py`

- [ ] **Step 1: Write failing tests for dedupe, fact extraction, and review packet output**

Create `tests/fixtures/travel_skill/source_notes.json`:

```json
[
  {
    "category": "transport",
    "title": "12306 南京到延吉",
    "url": "https://www.12306.cn/",
    "checked_at": "2026-04-11",
    "source_type": "official",
    "facts": ["南京到延吉需中转或飞长春后转高铁"]
  },
  {
    "category": "transport",
    "title": "12306 南京到延吉",
    "url": "https://www.12306.cn/",
    "checked_at": "2026-04-11",
    "source_type": "official",
    "facts": ["南京到延吉需中转或飞长春后转高铁"]
  },
  {
    "category": "food",
    "title": "元奶奶包饭",
    "url": "https://example.com/yuan-nainai",
    "checked_at": "2026-04-11",
    "source_type": "local-listing",
    "facts": ["招牌菜: 包饭", "人均: 60-90"]
  }
]
```

Create `tests/travel_skill/test_research_packet.py`:

```python
from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class ResearchPacketTest(unittest.TestCase):
    def test_merge_sources_deduplicates_by_category_and_url(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "source_notes.json"
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.json"
            run_script(SKILL_DIR / "scripts" / "merge_sources.py", "--input", fixture, "--output", merged)
            payload = json.loads(merged.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["entries"]), 2)
        self.assertEqual([item["category"] for item in payload["entries"]], ["food", "transport"])

    def test_extract_and_review_packet_write_expected_sections(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "source_notes.json"
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.json"
            facts = Path(tmp) / "facts.json"
            packet_dir = Path(tmp) / "review"
            run_script(SKILL_DIR / "scripts" / "merge_sources.py", "--input", fixture, "--output", merged)
            run_script(SKILL_DIR / "scripts" / "extract_structured_facts.py", "--input", merged, "--output", facts)
            run_script(SKILL_DIR / "scripts" / "generate_review_packet.py", "--input", facts, "--output-dir", packet_dir)
            fact_payload = json.loads(facts.read_text(encoding="utf-8"))
            md = (packet_dir / "research-packet.md").read_text(encoding="utf-8")
            html = (packet_dir / "research-packet.html").read_text(encoding="utf-8")
        self.assertIn("transport", fact_payload["categories"])
        self.assertIn("food", fact_payload["categories"])
        self.assertIn("## 已核实", md)
        self.assertIn("<h2>待确认</h2>", html)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m unittest tests/travel_skill/test_research_packet.py -v`
Expected: FAIL because the scripts do not exist yet.

- [ ] **Step 3: Implement the three research packet scripts**

Create `.codex/skills/travel-skill/scripts/merge_sources.py`:

```python
from pathlib import Path
import argparse
import json


def merge(entries: list[dict]) -> dict:
    deduped = {}
    for entry in entries:
        deduped[(entry["category"], entry["url"])] = entry
    ordered = sorted(deduped.values(), key=lambda item: (item["category"], item["title"]))
    return {"entries": ordered}
```

Create `.codex/skills/travel-skill/scripts/extract_structured_facts.py`:

```python
from pathlib import Path
import argparse
import json


def extract(payload: dict) -> dict:
    categories = {}
    for entry in payload["entries"]:
        categories.setdefault(entry["category"], []).append({
            "title": entry["title"],
            "source_type": entry["source_type"],
            "checked_at": entry["checked_at"],
            "facts": entry.get("facts", []),
            "url": entry["url"],
        })
    return {"categories": categories}
```

Create `.codex/skills/travel-skill/scripts/generate_review_packet.py`:

```python
from pathlib import Path
import argparse
import json


def build_markdown(payload: dict) -> str:
    verified = []
    pending = []
    for category, entries in payload["categories"].items():
        target = verified if category in {"transport", "food"} else pending
        target.append(f"### {category}")
        for entry in entries:
            target.append(f"- {entry['title']} ({entry['source_type']}, 核对 {entry['checked_at']})")
    return "\n".join(["# Research Packet", "## 已核实", *verified, "", "## 待确认", *pending]) + "\n"


def build_html(payload: dict) -> str:
    return (
        "<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><title>Research Packet</title>"
        "<body><h1>Research Packet</h1><h2>已核实</h2><h2>待确认</h2>"
        f"<script type=\"application/json\" id=\"packet-data\">{json.dumps(payload, ensure_ascii=False)}</script></body></html>"
    )
```

Each script should expose a pure helper function plus a CLI `main()` that reads JSON from `--input` and writes to `--output` / `--output-dir`.

- [ ] **Step 4: Re-run the tests and verify they pass**

Run: `python -m unittest tests/travel_skill/test_research_packet.py -v`
Expected: PASS with two passing tests.

- [ ] **Step 5: Commit the research packet pipeline**

```bash
git add .codex/skills/travel-skill/scripts/merge_sources.py .codex/skills/travel-skill/scripts/extract_structured_facts.py .codex/skills/travel-skill/scripts/generate_review_packet.py tests/fixtures/travel_skill/source_notes.json tests/travel_skill/test_research_packet.py
git commit -m "feat: 增加 travel skill research packet 生成链路"
```

### Task 4: Implement Guide Model Composition And Sample Gap Enforcement

**Files:**
- Create: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Create: `.codex/skills/travel-skill/scripts/fill_missing_sections.py`
- Create: `tests/fixtures/travel_skill/approved_research.json`
- Create: `tests/travel_skill/test_compose.py`
- Test: `tests/travel_skill/test_compose.py`

- [ ] **Step 1: Write failing compose tests**

Create `tests/fixtures/travel_skill/approved_research.json`:

```json
{
  "trip_slug": "wuyi-yanji-changbaishan",
  "title": "五一延吉长白山",
  "meta": {
    "trip_slug": "wuyi-yanji-changbaishan",
    "date_range": "2026-04-30 至 2026-05-05",
    "departure_city": "南京",
    "travelers": "4 人"
  },
  "facts": {
    "transport": ["先锁长白山票，再锁二道白河住宿，再补城际交通"],
    "food": ["元奶奶包饭", "顺姬冷面"],
    "weather": ["延吉早晚温差大，北坡风感更冷"],
    "attractions": ["水上市场", "民俗园", "长白山北坡"]
  }
}
```

Create `tests/travel_skill/test_compose.py`:

```python
from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


REQUIRED_SECTIONS = ["overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources"]


class ComposePipelineTest(unittest.TestCase):
    def test_build_guide_model_writes_sections_and_execution_fields(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            payload = json.loads(model.read_text(encoding="utf-8"))
        self.assertEqual(sorted(payload["sections"].keys()), sorted(REQUIRED_SECTIONS))
        self.assertIn("booking_order", payload["execution"])
        self.assertIn("daily_table", payload["execution"])
        self.assertIn("budget_bands", payload["execution"])

    def test_fill_missing_sections_backfills_sample_html_gaps(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            completed = Path(tmp) / "guide-content.completed.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", completed)
            payload = json.loads(completed.read_text(encoding="utf-8"))
        self.assertIn("订票顺序", [item["title"] for item in payload["sections"]["transport"]])
        self.assertIn("价格区间", [item["title"] for item in payload["sections"]["transport"]])
        self.assertIn("历史体感与穿衣", [item["title"] for item in payload["sections"]["season"]])
```

- [ ] **Step 2: Run the compose tests and verify they fail**

Run: `python -m unittest tests/travel_skill/test_compose.py -v`
Expected: FAIL because the scripts do not exist yet.

- [ ] **Step 3: Implement guide model composition and gap filling**

Create `.codex/skills/travel-skill/scripts/build_guide_model.py` with:

```python
SECTION_KEYS = ["overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources"]


def build_model(payload: dict) -> dict:
    facts = payload["facts"]
    return {
        "meta": payload["meta"],
        "sections": {
            "overview": [{"title": "行程概览", "summary": payload["title"], "points": facts["attractions"]}],
            "recommended": [{"title": "最推荐方案", "summary": "延吉 3 晚 + 二道白河 2 晚", "points": facts["transport"]}],
            "options": [{"title": "备选方案", "summary": "保留机动日", "points": ["天气差时补北坡，否则回延吉"]}],
            "attractions": [{"title": "核心玩法", "summary": "按顺路程度安排", "points": facts["attractions"]}],
            "food": [{"title": "店铺清单", "summary": "先排顺路店", "points": facts["food"]}],
            "season": [{"title": "天气判断", "summary": "历史体感优先", "points": facts["weather"]}],
            "packing": [{"title": "打包建议", "summary": "分层穿衣", "points": ["外层防风", "山上带手套"]}],
            "transport": [{"title": "主交通逻辑", "summary": "先锁高风险票务", "points": facts["transport"]}],
            "sources": [{"title": "研究来源", "summary": "来源在 review 阶段附带", "entries": []}]
        },
        "execution": {
            "booking_order": facts["transport"],
            "daily_table": [{"day": "D1", "route": "南京 → 延吉"}, {"day": "D2", "route": "延吉水上市场 + 民俗园"}],
            "budget_bands": [{"title": "省心版", "range": "3200-4300/人"}, {"title": "升级版", "range": "4500-6800/人"}]
        }
    }
```

Create `.codex/skills/travel-skill/scripts/fill_missing_sections.py` with:

```python
def ensure_card(section: list, title: str, summary: str, points: list[str]) -> None:
    titles = {item["title"] for item in section}
    if title not in titles:
        section.append({"title": title, "summary": summary, "points": points})


def fill(payload: dict) -> dict:
    sections = payload["sections"]
    ensure_card(sections["transport"], "订票顺序", "高风险项目优先", payload["execution"]["booking_order"])
    ensure_card(sections["transport"], "价格区间", "保留预算区间而不是写死实时票价", ["大交通价格临近出发复核"])
    ensure_card(sections["season"], "历史体感与穿衣", "不要过早写死未来天气", ["优先写历史体感", "穿衣按分层处理"])
    ensure_card(sections["food"], "店铺级推荐", "写清店名和适合安排在哪一顿", ["元奶奶包饭", "顺姬冷面"])
    return payload
```

Each script should provide `main()` so tests can invoke it via CLI.

- [ ] **Step 4: Re-run the compose tests and verify they pass**

Run: `python -m unittest tests/travel_skill/test_compose.py -v`
Expected: PASS with two passing tests.

- [ ] **Step 5: Commit guide model composition**

```bash
git add .codex/skills/travel-skill/scripts/build_guide_model.py .codex/skills/travel-skill/scripts/fill_missing_sections.py tests/fixtures/travel_skill/approved_research.json tests/travel_skill/test_compose.py
git commit -m "feat: 增加 travel skill 攻略内容模型编排"
```

### Task 5: Implement Site Rendering, Single-File Export, And ZIP Packaging

**Files:**
- Create: `.codex/skills/travel-skill/assets/templates/desktop-index.html`
- Create: `.codex/skills/travel-skill/assets/templates/mobile-index.html`
- Create: `.codex/skills/travel-skill/assets/templates/base.css`
- Create: `.codex/skills/travel-skill/assets/templates/render-guide.js`
- Create: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Create: `.codex/skills/travel-skill/scripts/export_single_html.py`
- Create: `.codex/skills/travel-skill/scripts/package_trip.py`
- Create: `tests/travel_skill/test_render_package.py`
- Test: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Write failing render/package tests**

Create `tests/travel_skill/test_render_package.py`:

```python
from pathlib import Path
import tempfile
import unittest
import zipfile

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class RenderPackageTest(unittest.TestCase):
    def test_render_trip_site_creates_trip_structure(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            desktop = output_root / "trips" / "wuyi-yanji-changbaishan" / "desktop" / "index.html"
            mobile = output_root / "trips" / "wuyi-yanji-changbaishan" / "mobile" / "index.html"
        self.assertTrue(desktop.exists())
        self.assertTrue(mobile.exists())

    def test_export_single_html_and_package_trip_inline_assets(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            dist = output_root / "dist"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            run_script(SKILL_DIR / "scripts" / "export_single_html.py", "--guide-root", output_root / "trips" / "wuyi-yanji-changbaishan", "--output", dist / "wuyi-yanji-changbaishan.html")
            run_script(SKILL_DIR / "scripts" / "package_trip.py", "--guide-root", output_root / "trips" / "wuyi-yanji-changbaishan", "--single-html", dist / "wuyi-yanji-changbaishan.html", "--output", dist / "wuyi-yanji-changbaishan.zip")
            html = (dist / "wuyi-yanji-changbaishan.html").read_text(encoding="utf-8")
            with zipfile.ZipFile(dist / "wuyi-yanji-changbaishan.zip") as archive:
                names = sorted(archive.namelist())
        self.assertNotIn("href=\"../assets/base.css\"", html)
        self.assertNotIn("<script src=", html)
        self.assertIn("wuyi-yanji-changbaishan.html", names)
        self.assertIn("trip-summary.txt", names)
```

- [ ] **Step 2: Run the render/package tests and verify they fail**

Run: `python -m unittest tests/travel_skill/test_render_package.py -v`
Expected: FAIL because the templates and scripts do not exist yet.

- [ ] **Step 3: Implement templates and the three render/package scripts**

Create `.codex/skills/travel-skill/assets/templates/desktop-index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{{TITLE}}</title>
    <link rel="stylesheet" href="../assets/base.css" />
  </head>
  <body data-mode="desktop">
    <header class="hero"><h1>{{TITLE}}</h1><p>{{DATE_RANGE}}</p></header>
    {{SECTIONS}}
    <script src="../assets/guide-content.js"></script>
    <script src="../assets/render-guide.js"></script>
  </body>
</html>
```

Create `.codex/skills/travel-skill/assets/templates/mobile-index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{{TITLE}} / Mobile</title>
    <link rel="stylesheet" href="../assets/base.css" />
  </head>
  <body data-mode="mobile">
    {{SECTIONS}}
    <script src="../assets/guide-content.js"></script>
    <script src="../assets/render-guide.js"></script>
  </body>
</html>
```

Create `.codex/skills/travel-skill/assets/templates/base.css`:

```css
:root { color-scheme: light; --bg: #f7f1e8; --ink: #1f2933; --card: #fffaf3; --line: #d7c9b6; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Microsoft YaHei", sans-serif; background: var(--bg); color: var(--ink); }
.hero, section { width: min(1100px, calc(100% - 32px)); margin: 0 auto; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 20px; padding: 20px; margin-bottom: 16px; }
```

Create `.codex/skills/travel-skill/assets/templates/render-guide.js` by copying the reusable helper functions from `trips/jilin-yanji-changbaishan/assets/render-guide.js`.

Create `.codex/skills/travel-skill/scripts/render_trip_site.py` with these core helpers:

```python
SECTION_ORDER = ["overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources"]


def render_sections(section_order, mobile=False):
    parts = []
    for index, key in enumerate(section_order, start=1):
        page_attr = f' data-page="{index}"' if mobile else ""
        parts.append(f'<section id="{key}"{page_attr}><div class="card"><h2>{key}</h2><div data-cards="{key}"></div></div></section>')
    return "\n".join(parts)
```

The CLI should read `guide-content.json`, create `trips/<slug>/desktop/index.html`, `mobile/index.html`, `assets/base.css`, `assets/render-guide.js`, `assets/guide-content.js`, and `notes/sources.md` under `--output-root`.

Create `.codex/skills/travel-skill/scripts/export_single_html.py` with:

```python
def inline_assets(guide_root: Path) -> str:
    desktop = (guide_root / "desktop" / "index.html").read_text(encoding="utf-8")
    css = (guide_root / "assets" / "base.css").read_text(encoding="utf-8")
    data = (guide_root / "assets" / "guide-content.js").read_text(encoding="utf-8")
    render = (guide_root / "assets" / "render-guide.js").read_text(encoding="utf-8")
    html = desktop.replace('<link rel="stylesheet" href="../assets/base.css" />', f"<style>{css}</style>")
    html = html.replace('<script src="../assets/guide-content.js"></script>', f"<script>{data}</script>")
    html = html.replace('<script src="../assets/render-guide.js"></script>', f"<script>{render}</script>")
    return html
```

Create `.codex/skills/travel-skill/scripts/package_trip.py` so it writes a `trip-summary.txt` next to the output ZIP and packages the single HTML, summary text, and `notes/sources.md`.

- [ ] **Step 4: Re-run the render/package tests and verify they pass**

Run: `python -m unittest tests/travel_skill/test_render_package.py -v`
Expected: PASS with two passing tests.

- [ ] **Step 5: Commit rendering and packaging**

```bash
git add .codex/skills/travel-skill/assets/templates .codex/skills/travel-skill/scripts/render_trip_site.py .codex/skills/travel-skill/scripts/export_single_html.py .codex/skills/travel-skill/scripts/package_trip.py tests/travel_skill/test_render_package.py
git commit -m "feat: 增加 travel skill 渲染与单文件导出"
```

### Task 6: Implement Static Verification And Hook Into The Existing Browser Checker

**Files:**
- Create: `.codex/skills/travel-skill/scripts/verify_trip.py`
- Create: `tests/travel_skill/test_verify.py`
- Modify: `tests/playwright_trip_render_check.py`
- Test: `tests/travel_skill/test_verify.py`

- [ ] **Step 1: Write failing verification tests**

Create `tests/travel_skill/test_verify.py`:

```python
from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class VerifyPipelineTest(unittest.TestCase):
    def test_verify_trip_reports_required_files_without_browser(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            report = output_root / "verify" / "report.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            run_script(SKILL_DIR / "scripts" / "export_single_html.py", "--guide-root", output_root / "trips" / "wuyi-yanji-changbaishan", "--output", output_root / "dist" / "wuyi-yanji-changbaishan.html")
            run_script(SKILL_DIR / "scripts" / "verify_trip.py", "--guide-root", output_root / "trips" / "wuyi-yanji-changbaishan", "--single-html", output_root / "dist" / "wuyi-yanji-changbaishan.html", "--report", report, "--skip-browser")
            payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(payload["static_checks"]["desktop_exists"])
        self.assertTrue(payload["static_checks"]["mobile_exists"])
        self.assertTrue(payload["static_checks"]["single_html_exists"])
        self.assertEqual(payload["browser_check"], "skipped")
```

- [ ] **Step 2: Run the verification test and verify it fails**

Run: `python -m unittest tests/travel_skill/test_verify.py -v`
Expected: FAIL because `verify_trip.py` does not exist yet.

- [ ] **Step 3: Implement `verify_trip.py` and make the Playwright checker accept a dynamic guide root**

Create `.codex/skills/travel-skill/scripts/verify_trip.py`:

```python
from pathlib import Path
import argparse
import json
import subprocess
import sys


def collect_static(guide_root: Path, single_html: Path) -> dict:
    return {
        "desktop_exists": (guide_root / "desktop" / "index.html").exists(),
        "mobile_exists": (guide_root / "mobile" / "index.html").exists(),
        "single_html_exists": single_html.exists(),
        "sources_exists": (guide_root / "notes" / "sources.md").exists(),
    }
```

The CLI should write `{"static_checks": ..., "browser_check": "skipped" | "passed"}` to `--report`, and when `--skip-browser` is absent it must invoke:

```python
[
    sys.executable,
    str(Path(__file__).resolve().parents[3] / "tests" / "playwright_trip_render_check.py"),
    "--guide-root",
    str(guide_root),
]
```

Modify `tests/playwright_trip_render_check.py` so `argparse` accepts `--guide-root`, sets:

```python
guide_root = Path(args.guide_root) if args.guide_root else GUIDE_ROOT
pages = [
    guide_root / "desktop" / "index.html",
    guide_root / "mobile" / "index.html",
]
```

and passes `pages` into `collect_report()` instead of the previous hard-coded `PAGES`.

- [ ] **Step 4: Re-run the verification test and then run the browser checker once on the existing Jilin guide**

Run: `python -m unittest tests/travel_skill/test_verify.py -v`
Expected: PASS with one passing test.

Then run:

```powershell
python .\tests\playwright_trip_render_check.py --guide-root .\trips\jilin-yanji-changbaishan
```

Expected: PASS and write `trip-render-report.json` under `tests/artifacts/...`.

- [ ] **Step 5: Commit verification integration**

```bash
git add .codex/skills/travel-skill/scripts/verify_trip.py tests/playwright_trip_render_check.py tests/travel_skill/test_verify.py
git commit -m "feat: 增加 travel skill 校验链路"
```

## Self-Review

### Spec Coverage

- `intake`: Task 2 implements request normalization.
- `research`: Tasks 2 and 3 implement source-aware research planning, merge, extraction, and review packets.
- `review-gate`: Task 3 generates Markdown and HTML review packets.
- `compose`: Task 4 creates `guide-content.json` plus sample-gap enforcement.
- `render`: Task 5 creates `trips/<slug>/...` output and single-file HTML export.
- `package-share`: Task 5 creates ZIP bundles with summary text and sources.
- `verify`: Task 6 adds static verification plus optional Playwright browser validation.
- Skill packaging: Task 1 creates `.codex/skills/travel-skill/` metadata and references.
- Shareability: Task 5 covers single-file HTML and ZIP. Static URL remains deferred by spec.

### Placeholder Scan

- No `TODO`, `TBD`, or "implement later" markers remain.
- Every task names exact files and exact commands.
- Each code-changing step includes concrete code content.

### Type Consistency

- `trip_slug`, `share_mode`, `review_mode`, and `unknown_fields` are introduced in Task 2 and reused consistently later.
- `sections` and `execution` are introduced in Task 4 and consumed consistently in Tasks 5 and 6.
- `guide-root` is the CLI name used by export, package, verify, and the Playwright checker.
