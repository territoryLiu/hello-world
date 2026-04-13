# Travel Skill v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework `travel-skill` into a contract-first pipeline that blocks incomplete requests, generates true day-by-day primary and option routes, publishes the full artifact set by default, and enforces delivery-grade verification.

**Architecture:** Keep the existing research -> compose -> render -> package skeleton, but insert a real request gate, a planning-first content path, a localization pass, stricter publish isolation, and stronger verification. Migrate in-place with tests guarding each contract so the existing skill remains usable during the refactor.

**Tech Stack:** Python scripts, `pytest`, JSON contracts, HTML templates, Playwright verification, ZIP packaging

---

## File Map

**Modify**

- `.codex/skills/travel-skill/SKILL.md`
- `.codex/skills/travel-skill/scripts/normalize_request.py`
- `.codex/skills/travel-skill/scripts/build_trip_planning.py`
- `.codex/skills/travel-skill/scripts/build_guide_model.py`
- `.codex/skills/travel-skill/scripts/render_trip_site.py`
- `.codex/skills/travel-skill/scripts/build_portal.py`
- `.codex/skills/travel-skill/scripts/export_single_html.py`
- `.codex/skills/travel-skill/scripts/package_trip.py`
- `.codex/skills/travel-skill/scripts/build_image_plan.py`
- `.codex/skills/travel-skill/scripts/verify_trip.py`
- `tests/travel_skill/test_intake_research.py`
- `tests/travel_skill/test_planning.py`
- `tests/travel_skill/test_compose.py`
- `tests/travel_skill/test_render_package.py`
- `tests/travel_skill/test_verify.py`

**Create**

- `.codex/skills/travel-skill/scripts/validate_request_gate.py`
- `.codex/skills/travel-skill/scripts/localize_facts.py`
- `.codex/skills/travel-skill/scripts/verify_render_with_playwright.py`
- `tests/travel_skill/test_localize_facts.py`

### Task 1: Prepare Isolated Workspace and Add Request Gate Tests

**Files:**
- Create: `.worktrees/travel-skill-v2/`
- Modify: `tests/travel_skill/test_intake_research.py`
- Create: `.codex/skills/travel-skill/scripts/validate_request_gate.py`

- [ ] **Step 1: Create the dedicated worktree**

Run:

```powershell
git worktree add .worktrees/travel-skill-v2 -b feature/travel-skill-v2 HEAD
git -C .worktrees/travel-skill-v2 status --short
```

Expected:

```text
<no output>
```

- [ ] **Step 2: Add failing tests for blocked requests and follow-up questions**

Append to `tests/travel_skill/test_intake_research.py`:

```python
    def test_validate_request_gate_blocks_missing_core_fields(self):
        payload = {
            "title": "五一延吉长白山",
            "departure_city": "南京",
            "destinations": ["延吉", "长白山"],
            "travelers": {"count": 2, "adults": 2, "children": 0, "age_notes": ""},
            "budget": {"mode": "total", "min": 3000, "max": 6000},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "gate.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(
                SKILL_DIR / "scripts" / "validate_request_gate.py",
                "--input", input_path,
                "--output", output_path,
            )
            gate = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertFalse(gate["can_proceed"])
        self.assertIn("date_range", gate["blocking_fields"])
        self.assertTrue(gate["follow_up_questions"])

    def test_normalize_request_does_not_crash_when_core_fields_are_missing(self):
        payload = {
            "title": "测试行程",
            "departure_city": "南京",
            "destinations": ["延吉"],
            "travelers": {"count": 2, "adults": 2, "children": 0, "age_notes": ""},
            "budget": {"mode": "total", "min": 1000, "max": 2000},
        }
        normalized = self._normalize_payload(payload)
        self.assertEqual(normalized["intake_status"], "blocked")
        self.assertIn("date_range", normalized["blocking_fields"])
```

- [ ] **Step 3: Run the intake tests and confirm they fail**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_intake_research.py -q
```

Expected:

```text
FAIL for missing validate_request_gate.py and normalize_request KeyError behavior
```

- [ ] **Step 4: Implement the gate script and safe normalization**

Create `.codex/skills/travel-skill/scripts/validate_request_gate.py`:

```python
from pathlib import Path
import argparse
import json

CORE_FIELDS = ["title", "departure_city", "destinations", "date_range", "travelers", "budget"]


def build_gate(payload: dict) -> dict:
    blocking_fields = [field for field in CORE_FIELDS if not payload.get(field)]
    follow_up_questions = []
    if "date_range" in blocking_fields:
        follow_up_questions.append("请补充预计出行日期范围。")
    if "destinations" in blocking_fields:
        follow_up_questions.append("请补充目的地城市或景区。")
    return {
        "can_proceed": not blocking_fields,
        "blocking_fields": blocking_fields,
        "warning_fields": [],
        "follow_up_questions": follow_up_questions,
        "traveler_constraints": {},
    }
```

Update `.codex/skills/travel-skill/scripts/normalize_request.py` so `normalize()` uses `.get()` and emits:

```python
gate = {
    "blocking_fields": [key for key in CORE_FIELDS if not payload.get(key)],
    "warning_fields": [],
}
intake_status = "blocked" if gate["blocking_fields"] else "ready"
```

and returns:

```python
        "intake_status": intake_status,
        "blocking_fields": gate["blocking_fields"],
        "warning_fields": gate["warning_fields"],
        "follow_up_questions": [],
```

- [ ] **Step 5: Re-run tests and commit**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_intake_research.py -q
git -C .worktrees/travel-skill-v2 add tests/travel_skill/test_intake_research.py .codex/skills/travel-skill/scripts/validate_request_gate.py .codex/skills/travel-skill/scripts/normalize_request.py
git -C .worktrees/travel-skill-v2 commit -m "feat: 增加 travel request 门禁"
```

Expected:

```text
passed
```

### Task 2: Make Planning Output Independent Day-by-Day Routes

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/build_trip_planning.py`
- Modify: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Modify: `tests/travel_skill/test_planning.py`
- Modify: `tests/travel_skill/test_compose.py`

- [ ] **Step 1: Add failing tests for independent option plans**

Append to `tests/travel_skill/test_planning.py`:

```python
    def test_build_trip_planning_generates_independent_option_days(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "title": "短途测试",
            "departure_city": "长春",
            "destinations": ["吉林", "松花湖"],
            "distance_km": 120,
            "facts": [
                {"topic": "attractions", "place": "松花湖", "text": "适合半日到一日"},
                {"topic": "food", "place": "吉林", "shop_name": "乌拉火锅", "text": "适合晚餐"},
                {"topic": "long_distance_transport", "from": "长春", "to": "吉林", "schedule": "C123", "checked_at": "2026-04-13"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "approved.json"
            output_root = Path(tmp) / "travel-data"
            input_path.write_text(json.dumps(approved_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_trip_planning.py", "--input", input_path, "--output-root", output_root)
            route_options = json.loads((output_root / "trips" / "demo-trip" / "planning" / "route-options.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(route_options["plans"]), 2)
        self.assertNotEqual(route_options["plans"][0]["days"], route_options["plans"][1]["days"])
```

Append to `tests/travel_skill/test_compose.py`:

```python
    def test_build_guide_model_uses_planning_route_options_instead_of_transport_cards_only(self):
        payload = compose({
            "trip_slug": "demo-trip",
            "title": "短途测试",
            "planning": {
                "route_main": {"days": []},
                "route_options": {
                    "plans": [
                        {"title": "高铁优先方案", "fit_for": "稳妥", "tradeoffs": ["早起"], "days": [{"day": 1, "base_city": "吉林", "theme": "市区线", "morning": ["高铁到达"], "afternoon": ["松花湖"], "evening": ["乌拉火锅"], "transport": ["C123"], "meals": ["乌拉火锅"], "backup_spots": ["北山"]}]},
                        {"title": "周边延伸方案", "fit_for": "想慢一点", "tradeoffs": ["多住一晚"], "days": [{"day": 1, "base_city": "吉林", "theme": "慢游线", "morning": ["午后出发"], "afternoon": ["江边散步"], "evening": ["地方菜"], "transport": ["城际列车"], "meals": ["地方菜"], "backup_spots": ["博物馆"]}]},
                    ]
                }
            },
            "facts": [],
        })
        titles = [item["title"] for item in payload["outputs"]["recommended"]["route_options"]]
        self.assertIn("高铁优先方案", titles)
        self.assertIn("周边延伸方案", titles)
```

- [ ] **Step 2: Run planning and compose tests**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_planning.py tests/travel_skill/test_compose.py -q
```

Expected:

```text
FAIL because route options still reuse main days or are ignored by compose
```

- [ ] **Step 3: Rework `build_trip_planning.py`**

Update `.codex/skills/travel-skill/scripts/build_trip_planning.py` so `build_option_plans()` returns distinct day sets:

```python
def build_option_plans(payload: dict) -> dict:
    return {
        "plans": [
            {
                "plan_id": "rail-first",
                "title": "高铁优先方案",
                "fit_for": "节奏稳定，适合先把大交通锁死",
                "tradeoffs": ["到达时间更早，需要更早出门"],
                "days": build_rail_days(payload),
            },
            {
                "plan_id": "extended-nearby",
                "title": "周边延伸方案",
                "fit_for": "想放慢节奏并补一个周边点",
                "tradeoffs": ["总时长更长，住宿切换更多"],
                "days": build_extended_days(payload),
            },
        ]
    }
```

and add `build_rail_days()` / `build_extended_days()` helpers instead of copying `build_main_plan(payload)["days"]`.

- [ ] **Step 4: Rework `build_guide_model.py` to consume planning route options**

Add:

```python
def _route_option_cards_from_planning(planning: dict) -> list[dict]:
    route_options = planning.get("route_options") if isinstance(planning, dict) else {}
    plans = route_options.get("plans") if isinstance(route_options, dict) else []
    cards = []
    for plan in plans if isinstance(plans, list) else []:
        day_lines = [f"D{day['day']}：{day['theme']}" for day in plan.get("days", []) if isinstance(day, dict)]
        cards.append(
            _content_item(
                plan.get("title", "备选方案"),
                plan.get("fit_for", ""),
                [*plan.get("tradeoffs", []), *day_lines],
            )
        )
    return cards
```

Then replace:

```python
    route_options = _route_option_cards(payload, transport_facts)
```

with:

```python
    planning_payload = payload.get("planning") if isinstance(payload.get("planning"), dict) else {}
    route_options = _route_option_cards_from_planning(planning_payload) or _route_option_cards(payload, transport_facts)
```

- [ ] **Step 5: Re-run tests and commit**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_planning.py tests/travel_skill/test_compose.py -q
git -C .worktrees/travel-skill-v2 add tests/travel_skill/test_planning.py tests/travel_skill/test_compose.py .codex/skills/travel-skill/scripts/build_trip_planning.py .codex/skills/travel-skill/scripts/build_guide_model.py
git -C .worktrees/travel-skill-v2 commit -m "feat: 打通逐日规划与备选方案发布链路"
```

Expected:

```text
passed
```

### Task 3: Add Localization Pass Before Compose

**Files:**
- Create: `.codex/skills/travel-skill/scripts/localize_facts.py`
- Modify: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Create: `tests/travel_skill/test_localize_facts.py`

- [ ] **Step 1: Add failing localization tests**

Create `tests/travel_skill/test_localize_facts.py`:

```python
from pathlib import Path
import json
import tempfile

from tests.travel_skill.helpers import SKILL_DIR, run_script


def test_localize_facts_normalizes_english_transport_copy():
    payload = {
        "facts": [
            {"topic": "long_distance_transport", "text": "ticket: 225 CNY", "source_title": "Official notice"},
            {"topic": "risks", "text": "arrive before 08:30 for smoother queue", "source_title": "social note"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "input.json"
        output_path = Path(tmp) / "output.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        run_script(SKILL_DIR / "scripts" / "localize_facts.py", "--input", input_path, "--output", output_path)
        localized = json.loads(output_path.read_text(encoding="utf-8"))
    assert "票价" in localized["facts"][0]["text_zh"]
    assert "错峰" in localized["facts"][1]["text_zh"]
```

- [ ] **Step 2: Run localization test**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_localize_facts.py -q
```

Expected:

```text
FAIL for missing localize_facts.py
```

- [ ] **Step 3: Implement `localize_facts.py`**

Create `.codex/skills/travel-skill/scripts/localize_facts.py`:

```python
from pathlib import Path
import argparse
import json

REPLACEMENTS = [
    ("ticket:", "票价参考："),
    ("CNY", "元"),
    ("arrive before", "建议在"),
    ("smoother queue", "错峰到达会更从容"),
]


def localize_text(text: str) -> str:
    localized = str(text or "").strip()
    for source, target in REPLACEMENTS:
        localized = localized.replace(source, target)
    return " ".join(localized.split())
```

and write back `text_zh` for each fact.

- [ ] **Step 4: Wire compose to prefer `text_zh`**

Update `_with_common_fields()` in `.codex/skills/travel-skill/scripts/build_guide_model.py`:

```python
    fact["text"] = _normalize_copy(raw.get("text_zh") or raw.get("text", ""))
```

- [ ] **Step 5: Re-run tests and commit**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_localize_facts.py tests/travel_skill/test_compose.py -q
git -C .worktrees/travel-skill-v2 add tests/travel_skill/test_localize_facts.py .codex/skills/travel-skill/scripts/localize_facts.py .codex/skills/travel-skill/scripts/build_guide_model.py
git -C .worktrees/travel-skill-v2 commit -m "feat: 增加事实中文化整理层"
```

Expected:

```text
passed
```

### Task 4: Fix Publish Isolation and Default Full Artifact Rendering

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Modify: `.codex/skills/travel-skill/scripts/build_portal.py`
- Modify: `.codex/skills/travel-skill/scripts/export_single_html.py`
- Modify: `.codex/skills/travel-skill/scripts/package_trip.py`
- Modify: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Add failing tests for sample isolation and default full rendering**

Append to `tests/travel_skill/test_render_package.py`:

```python
    def test_render_trip_site_default_emits_all_five_templates(self):
        model_payload = {
            "meta": {"trip_slug": "render-default-demo", "title": "Render Default Demo", "checked_at": "2026-04-13", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            desktop_dirs = sorted(p.name for p in (output_root / "guides" / "render-default-demo" / "desktop").iterdir() if p.is_dir())
        self.assertEqual(desktop_dirs, ["decision-first", "destination-first", "lifestyle-first", "route-first", "transport-first"])

    def test_render_trip_site_never_renders_sample_reference_chip(self):
        model_payload = {
            "meta": {
                "trip_slug": "sample-leak-demo",
                "title": "Sample Leak Demo",
                "checked_at": "2026-04-13",
                "source_count": 0,
                "sample_reference": {"path": "sample.html", "density_mode": "match-sample"},
            },
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            html = (output_root / "guides" / "sample-leak-demo" / "desktop" / "route-first" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("对标样本", html)
        self.assertNotIn("sample.html", html)
```

- [ ] **Step 2: Run render tests**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_render_package.py -q
```

Expected:

```text
FAIL because default render emits one template and sample chips still leak
```

- [ ] **Step 3: Update render defaults and meta chip behavior**

In `.codex/skills/travel-skill/scripts/render_trip_site.py`:

```python
def _meta_chips(meta: dict) -> str:
    traveler_constraints = meta.get("traveler_constraints") if isinstance(meta.get("traveler_constraints"), dict) else {}
    chips = [
        ("核对日期", _safe_text(meta.get("checked_at")) or "待补充"),
        ("来源数量", str(meta.get("source_count", 0))),
    ]
```

Remove the block that appends `sample_reference`.

Also change:

```python
selected_templates = RENDER_TEMPLATES if style in {"all", "", None, "route-first"} else [style]
```

to:

```python
selected_templates = RENDER_TEMPLATES if not style or style == "all" or style == "default" else [style]
```

and set the CLI default:

```python
parser.add_argument("--style", default="all")
```

- [ ] **Step 4: Keep share/package aligned with the default artifact set**

Confirm `.codex/skills/travel-skill/scripts/build_portal.py`, `export_single_html.py`, and `package_trip.py` still target:

- `portal.html`
- `recommended.html`
- `share.html`
- `notes/sources.md`
- `notes/sources.html`
- ZIP summary

If needed, adjust template assumptions to work when 5 templates are always present.

- [ ] **Step 5: Re-run tests and commit**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_render_package.py -q
git -C .worktrees/travel-skill-v2 add tests/travel_skill/test_render_package.py .codex/skills/travel-skill/scripts/render_trip_site.py .codex/skills/travel-skill/scripts/build_portal.py .codex/skills/travel-skill/scripts/export_single_html.py .codex/skills/travel-skill/scripts/package_trip.py
git -C .worktrees/travel-skill-v2 commit -m "feat: 固定完整发布产物并隔离样本引用"
```

Expected:

```text
passed
```

### Task 5: Strengthen Verify and Add Browser Check Hook

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/verify_trip.py`
- Create: `.codex/skills/travel-skill/scripts/verify_render_with_playwright.py`
- Modify: `tests/travel_skill/test_verify.py`

- [ ] **Step 1: Add failing verification tests for missing mobile and missing artifacts**

Append to `tests/travel_skill/test_verify.py`:

```python
    def test_verify_trip_fails_when_mobile_output_is_missing(self):
        module = load_verify_trip_module()
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "guides" / "demo-trip"
            for template_id in ["decision-first", "destination-first", "lifestyle-first", "route-first", "transport-first"]:
                (guide_root / "desktop" / template_id).mkdir(parents=True)
                (guide_root / "desktop" / template_id / "index.html").write_text("中文页面", encoding="utf-8")
            payload = module.verify_trip(guide_root)
        self.assertEqual(payload["status"], "fail")
        self.assertFalse(payload["content_checks"]["mobile_templates_complete"])
```

- [ ] **Step 2: Run verify tests**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_verify.py -q
```

Expected:

```text
FAIL because verify does not inspect mobile output or artifact completeness
```

- [ ] **Step 3: Expand `verify_trip.py`**

Add checks:

```python
desktop_templates = sorted(...)
mobile_templates = sorted(...)
content_checks = {
    "desktop_templates_complete": desktop_templates == EXPECTED_TEMPLATES,
    "mobile_templates_complete": mobile_templates == EXPECTED_TEMPLATES,
    "share_artifacts_present": all((guide_root / "notes" / name).exists() for name in ["sources.md", "sources.html"]),
    "no_sample_reference_in_publish": ...,
    "no_fake_media_blocks": ...,
}
status = "pass" if all(content_checks.values()) else "fail"
```

and add a `warnings` array for non-blocking browser-skip cases.

- [ ] **Step 4: Add Playwright verification hook**

Create `.codex/skills/travel-skill/scripts/verify_render_with_playwright.py`:

```python
from pathlib import Path
import argparse
import json


def verify_render(guide_root: Path) -> dict:
    return {
        "checked": False,
        "reason": "Playwright check not executed in unit-test mode",
        "status": "warn",
    }
```

Later integration can replace the stub, but `verify_trip.py` should know how to merge its output.

- [ ] **Step 5: Re-run tests and commit**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_verify.py -q
git -C .worktrees/travel-skill-v2 add tests/travel_skill/test_verify.py .codex/skills/travel-skill/scripts/verify_trip.py .codex/skills/travel-skill/scripts/verify_render_with_playwright.py
git -C .worktrees/travel-skill-v2 commit -m "feat: 强化 travel delivery 校验"
```

Expected:

```text
passed
```

### Task 6: Tighten Media Gate, Update Skill Docs, and Run Full Suite

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/build_image_plan.py`
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Modify: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Add failing test for `text-citation-only` media exclusion**

Append to `tests/travel_skill/test_render_package.py` if not already covered:

```python
    def test_build_image_plan_preserves_publish_state_for_render_gate(self):
        payload = {
            "items": [
                {
                    "title": "B站攻略",
                    "publish_state": "text-citation-only",
                    "recommended_usage": "attractions.hero",
                    "shot_candidates": [{"label": "无真实图片"}],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "output.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_image_plan.py", "--input", input_path, "--output", output_path)
            image_plan = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(image_plan["cover"]["publish_state"], "text-citation-only")
        self.assertEqual(image_plan["cover"]["image_url"], "")
```

- [ ] **Step 2: Run the render and image-plan tests**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill/test_render_package.py -q
```

Expected:

```text
FAIL if build_image_plan still leaks fake visual slots
```

- [ ] **Step 3: Preserve publish state in `build_image_plan.py` and update skill docs**

Ensure `_pick_visual()` returns:

```python
        return {
            "image_hint": "",
            "source_ref": item.get("title", ""),
            "image_url": "",
            "image_source_kind": "",
            "publish_state": "text-citation-only",
        }
```

and section records keep:

```python
                "publish_state": visual.get("publish_state", ""),
```

Update `.codex/skills/travel-skill/SKILL.md` output layout and verify section to describe:

- gate before research
- planning-first route generation
- default five-template publishing
- browser-aware verification

- [ ] **Step 4: Run the full suite**

Run:

```powershell
$env:PYTHONPATH='d:\vscode\hello-world'; python -m pytest tests/travel_skill -q
```

Expected:

```text
56+ passed
```

- [ ] **Step 5: Commit the integration pass**

Run:

```powershell
git -C .worktrees/travel-skill-v2 add .codex/skills/travel-skill/SKILL.md .codex/skills/travel-skill/scripts/build_image_plan.py tests/travel_skill
git -C .worktrees/travel-skill-v2 commit -m "feat: 收紧媒体门禁并更新 skill 合同"
```

Expected:

```text
commit created
```

---

## Self-Review

**Spec coverage**

- Gate 与 blocked request：Task 1
- 独立逐日主方案和备选方案：Task 2
- 中文化整理层：Task 3
- 默认完整发布与样本隔离：Task 4
- verify 强化与浏览器检查挂点：Task 5
- 媒体门禁和 skill 文档同步：Task 6

**Placeholder scan**

- No `TODO`
- No `TBD`
- No “similar to Task N”
- Each task includes exact files, commands, and expected outcomes

**Type consistency**

- Gate contract uses `can_proceed`, `blocking_fields`, `warning_fields`
- Planning contract uses `route_main`, `route_options`, and `days`
- Publish checks use `desktop_templates_complete`, `mobile_templates_complete`, `share_artifacts_present`
- Media gate uses `publish_state`
