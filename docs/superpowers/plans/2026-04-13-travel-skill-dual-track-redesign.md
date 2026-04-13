# Travel Skill Dual-Track Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `travel-skill` into a dual-track system that persists reusable place and corridor knowledge, generates true day-by-day trip plans, publishes exactly five structurally distinct guide templates, and enforces strict media/link verification before release.

**Architecture:** Keep the current intake -> research -> compose -> render pipeline running long enough to migrate safely, but insert a new knowledge/planning/publishing/media split. The migration lands in phases: first new paths and contracts, then knowledge persistence, then planning, then media gating, then publishing and verification. New code must read from explicit JSON contracts instead of inferring facts from legacy `guide-content.json`.

**Tech Stack:** Python scripts, `unittest`, JSON contracts, HTML rendering, `ffmpeg`, `whisper`, ZIP packaging

---

## File Map

**Existing files to modify**

- `.codex/skills/travel-skill/SKILL.md`
- `.codex/skills/travel-skill/scripts/normalize_request.py`
- `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- `.codex/skills/travel-skill/scripts/build_web_research_runs.py`
- `.codex/skills/travel-skill/scripts/persist_research_knowledge.py`
- `.codex/skills/travel-skill/scripts/build_guide_model.py`
- `.codex/skills/travel-skill/scripts/build_image_plan.py`
- `.codex/skills/travel-skill/scripts/render_trip_site.py`
- `.codex/skills/travel-skill/scripts/build_portal.py`
- `.codex/skills/travel-skill/scripts/export_single_html.py`
- `.codex/skills/travel-skill/scripts/package_trip.py`
- `.codex/skills/travel-skill/scripts/verify_trip.py`
- `tests/travel_skill/test_contract.py`
- `tests/travel_skill/test_intake_research.py`
- `tests/travel_skill/test_compose.py`
- `tests/travel_skill/test_render_package.py`
- `tests/travel_skill/test_verify.py`

**New files to create**

- `.codex/skills/travel-skill/scripts/travel_paths.py`
- `.codex/skills/travel-skill/scripts/build_trip_snapshots.py`
- `.codex/skills/travel-skill/scripts/build_trip_planning.py`
- `.codex/skills/travel-skill/scripts/validate_media_assets.py`
- `.codex/skills/travel-skill/scripts/extract_video_assets.py`
- `.codex/skills/travel-skill/assets/templates/template-route-first.html`
- `.codex/skills/travel-skill/assets/templates/template-decision-first.html`
- `.codex/skills/travel-skill/assets/templates/template-destination-first.html`
- `.codex/skills/travel-skill/assets/templates/template-transport-first.html`
- `.codex/skills/travel-skill/assets/templates/template-lifestyle-first.html`
- `tests/travel_skill/test_planning.py`
- `tests/travel_skill/test_media_pipeline.py`

**Sample data to migrate during implementation**

- `travel-data/2026-mayday-nanjing-yanji-changbaishan/approved-research.json`
- `travel-data/2026-mayday-nanjing-yanji-changbaishan/media-raw.json`
- `travel-data/2026-mayday-nanjing-yanji-changbaishan/site-coverage.json`

---

### Task 1: Prepare Isolated Workspace and Shared Path Contract

**Files:**
- Create: `.codex/skills/travel-skill/scripts/travel_paths.py`
- Modify: `tests/travel_skill/test_contract.py`

- [ ] **Step 1: Create a dedicated worktree before any feature code**

Run:

```powershell
git worktree add .worktrees/travel-skill-dual-track-redesign -b feature/travel-skill-dual-track-redesign HEAD
git -C .worktrees/travel-skill-dual-track-redesign status --short
```

Expected:

```text
<no output from status>
```

- [ ] **Step 2: Write the failing contract test for new root folders**

Add to `tests/travel_skill/test_contract.py`:

```python
from pathlib import Path
import importlib.util
import unittest

from tests.travel_skill.helpers import ROOT


class PathContractTest(unittest.TestCase):
    def test_travel_paths_exposes_dual_track_roots(self):
        module_path = ROOT / ".codex" / "skills" / "travel-skill" / "scripts" / "travel_paths.py"
        spec = importlib.util.spec_from_file_location("travel_paths", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        roots = module.travel_roots(ROOT / "travel-data", "demo-trip")
        self.assertEqual(roots["places_root"], ROOT / "travel-data" / "places")
        self.assertEqual(roots["corridors_root"], ROOT / "travel-data" / "corridors")
        self.assertEqual(roots["trip_root"], ROOT / "travel-data" / "trips" / "demo-trip")
        self.assertEqual(roots["guides_root"], ROOT / "travel-data" / "guides" / "demo-trip")
```

- [ ] **Step 3: Run the contract test and confirm it fails for missing module**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_contract.py -v
```

Expected:

```text
FAIL: test_travel_paths_exposes_dual_track_roots
...
FileNotFoundError or ModuleNotFoundError for travel_paths.py
```

- [ ] **Step 4: Implement the shared path helper**

Create `.codex/skills/travel-skill/scripts/travel_paths.py`:

```python
from pathlib import Path


def travel_roots(data_root: Path, trip_slug: str) -> dict[str, Path]:
    data_root = Path(data_root)
    return {
        "places_root": data_root / "places",
        "corridors_root": data_root / "corridors",
        "trips_root": data_root / "trips",
        "trip_root": data_root / "trips" / trip_slug,
        "guides_root": data_root / "guides" / trip_slug,
    }


def ensure_trip_layout(data_root: Path, trip_slug: str) -> dict[str, Path]:
    roots = travel_roots(data_root, trip_slug)
    for key in ["places_root", "corridors_root", "trips_root", "trip_root", "guides_root"]:
        roots[key].mkdir(parents=True, exist_ok=True)
    (roots["trip_root"] / "request").mkdir(parents=True, exist_ok=True)
    (roots["trip_root"] / "planning").mkdir(parents=True, exist_ok=True)
    (roots["trip_root"] / "snapshots").mkdir(parents=True, exist_ok=True)
    for child in ["desktop", "mobile", "share", "package", "verify"]:
        (roots["guides_root"] / child).mkdir(parents=True, exist_ok=True)
    return roots
```

- [ ] **Step 5: Re-run the contract test and commit**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_contract.py -v
git add tests/travel_skill/test_contract.py .codex/skills/travel-skill/scripts/travel_paths.py
git commit -m "feat: 建立 travel-skill 双轨目录根路径"
```

Expected:

```text
OK
```

### Task 2: Split Research Output into Places, Corridors, and Trip Snapshots

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/persist_research_knowledge.py`
- Create: `.codex/skills/travel-skill/scripts/build_trip_snapshots.py`
- Modify: `tests/travel_skill/test_intake_research.py`

- [ ] **Step 1: Add failing tests for place buckets, corridor buckets, and trip snapshots**

Add to `tests/travel_skill/test_intake_research.py`:

```python
    def test_persist_research_knowledge_splits_places_and_corridors(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "facts": [
                {"place": "延吉", "topic": "food", "text": "冷面", "source_url": "https://example.com/a"},
                {"place": "长白山", "topic": "attractions", "text": "北坡", "source_url": "https://example.com/b"},
                {"topic": "long_distance_transport", "from": "南京", "to": "长春", "text": "高铁转乘", "source_url": "https://example.com/c"},
            ],
        }
        media_payload = [
            {"place": "延吉", "platform": "bilibili", "url": "https://www.bilibili.com/video/BV1xx"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            approved_path = tmp_path / "approved.json"
            media_path = tmp_path / "media.json"
            coverage_path = tmp_path / "coverage.json"
            raw_path = tmp_path / "raw.json"
            output_root = tmp_path / "travel-data"
            approved_path.write_text(json.dumps(approved_payload, ensure_ascii=False), encoding="utf-8")
            media_path.write_text(json.dumps(media_payload, ensure_ascii=False), encoding="utf-8")
            coverage_path.write_text(json.dumps({"trip_slug": "demo-trip"}, ensure_ascii=False), encoding="utf-8")
            raw_path.write_text(json.dumps({"trip_slug": "demo-trip", "records": []}, ensure_ascii=False), encoding="utf-8")

            run_script(
                SKILL_DIR / "scripts" / "persist_research_knowledge.py",
                "--raw-research", raw_path,
                "--approved-research", approved_path,
                "--media-raw", media_path,
                "--site-coverage", coverage_path,
                "--output-root", output_root,
            )

            self.assertTrue((output_root / "places" / "yanji" / "structured-facts.json").exists())
            self.assertTrue((output_root / "corridors" / "nanjing-to-changchun" / "transport.json").exists())
```

Create snapshot assertion:

```python
    def test_build_trip_snapshots_writes_linked_knowledge_and_corridors(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "travel-data"
            trip_root = data_root / "trips" / "demo-trip"
            (data_root / "places" / "yanji").mkdir(parents=True)
            (data_root / "corridors" / "nanjing-to-changchun").mkdir(parents=True)
            input_path = Path(tmp) / "request.json"
            input_path.write_text(json.dumps({
                "trip_slug": "demo-trip",
                "departure_city": "南京",
                "destinations": ["延吉"],
            }, ensure_ascii=False), encoding="utf-8")
            run_script(
                SKILL_DIR / "scripts" / "build_trip_snapshots.py",
                "--input", input_path,
                "--data-root", data_root,
            )
            self.assertTrue((trip_root / "snapshots" / "linked-knowledge.json").exists())
            self.assertTrue((trip_root / "snapshots" / "linked-corridors.json").exists())
```

- [ ] **Step 2: Run the intake/research tests and confirm failures**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_intake_research.py -v
```

Expected:

```text
FAIL for missing corridors output and missing build_trip_snapshots.py
```

- [ ] **Step 3: Extend persistence to places and corridors**

Update `.codex/skills/travel-skill/scripts/persist_research_knowledge.py` around the write loop:

```python
def corridor_slug(from_place: str, to_place: str) -> str:
    return f"{slugify(from_place)}-to-{slugify(to_place)}"


def split_facts(facts: list[dict]) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    by_place: dict[str, list[dict]] = {}
    by_corridor: dict[str, list[dict]] = {}
    for fact in facts:
        place = clean_text(fact.get("place"))
        from_place = clean_text(fact.get("from"))
        to_place = clean_text(fact.get("to"))
        if place:
            by_place.setdefault(slugify(place), []).append(fact)
        elif from_place and to_place:
            by_corridor.setdefault(corridor_slug(from_place, to_place), []).append(fact)
    return by_place, by_corridor
```

Add corridor write:

```python
for slug, corridor_facts in corridors.items():
    corridor_root = output_root / "corridors" / slug
    corridor_root.mkdir(parents=True, exist_ok=True)
    (corridor_root / "transport.json").write_text(
        json.dumps({"facts": corridor_facts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

- [ ] **Step 4: Implement trip snapshot builder**

Create `.codex/skills/travel-skill/scripts/build_trip_snapshots.py`:

```python
from pathlib import Path
import argparse
import json

from travel_paths import ensure_trip_layout
from normalize_request import slugify


def corridor_slug(from_place: str, to_place: str) -> str:
    return f"{slugify(from_place)}-to-{slugify(to_place)}"


def build_snapshots(payload: dict, data_root: Path) -> None:
    roots = ensure_trip_layout(data_root, payload["trip_slug"])
    knowledge = [{"slug": slugify(place), "path": f"places/{slugify(place)}"} for place in payload.get("destinations", [])]
    corridors = []
    departure_city = payload.get("departure_city", "")
    for place in payload.get("destinations", []):
        corridors.append({"slug": corridor_slug(departure_city, place), "path": f"corridors/{corridor_slug(departure_city, place)}"})
    snapshot_root = roots["trip_root"] / "snapshots"
    (snapshot_root / "linked-knowledge.json").write_text(json.dumps({"items": knowledge}, ensure_ascii=False, indent=2), encoding="utf-8")
    (snapshot_root / "linked-corridors.json").write_text(json.dumps({"items": corridors}, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 5: Re-run tests and commit**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_intake_research.py -v
git add tests/travel_skill/test_intake_research.py .codex/skills/travel-skill/scripts/persist_research_knowledge.py .codex/skills/travel-skill/scripts/build_trip_snapshots.py
git commit -m "feat: 拆分目的地与交通走廊知识快照"
```

Expected:

```text
OK
```

### Task 3: Build Planning Contracts and Day-by-Day Route Generation

**Files:**
- Create: `.codex/skills/travel-skill/scripts/build_trip_planning.py`
- Create: `tests/travel_skill/test_planning.py`
- Modify: `.codex/skills/travel-skill/scripts/build_guide_model.py`
- Modify: `tests/travel_skill/test_compose.py`

- [ ] **Step 1: Add failing planning tests for main route and option routes**

Create `tests/travel_skill/test_planning.py`:

```python
from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import SKILL_DIR, run_script


class PlanningTest(unittest.TestCase):
    def test_build_trip_planning_generates_day_expanded_main_and_options(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "title": "五一南京延吉长白山",
            "departure_city": "南京",
            "destinations": ["延吉", "长白山", "图们"],
            "date_range": {"start": "2026-04-30", "end": "2026-05-05"},
            "facts": [
                {"topic": "attractions", "place": "长白山北坡", "text": "建议上午进山", "suggested_duration": "整天"},
                {"topic": "food", "place": "延吉", "shop_name": "服务大楼延吉冷面", "text": "适合落地午餐"},
                {"topic": "long_distance_transport", "from": "南京", "to": "长春", "schedule": "G1236 10:34-20:12", "checked_at": "2026-04-13"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "approved.json"
            output_root = Path(tmp) / "travel-data"
            input_path.write_text(json.dumps(approved_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_trip_planning.py", "--input", input_path, "--output-root", output_root)
            planning_root = output_root / "trips" / "demo-trip" / "planning"
            route_main = json.loads((planning_root / "route-main.json").read_text(encoding="utf-8"))
            route_options = json.loads((planning_root / "route-options.json").read_text(encoding="utf-8"))
            self.assertTrue(route_main["days"])
            self.assertTrue(route_options["plans"])
            self.assertIn("morning", route_main["days"][0])
            self.assertIn("transport", route_main["days"][0])
            self.assertIn("backup_spots", route_main["days"][0])
```

Add to `tests/travel_skill/test_compose.py`:

```python
    def test_build_guide_model_reads_planning_contract_instead_of_fake_daily_cards(self):
        payload = compose({
            "trip_slug": "demo-trip",
            "title": "中文攻略",
            "checked_at": "2026-04-13",
            "planning": {
                "route_main": {
                    "days": [
                        {
                            "day": 1,
                            "theme": "延吉初逛",
                            "base_city": "延吉",
                            "morning": ["南京出发"],
                            "afternoon": ["延吉西市场"],
                            "evening": ["冷面 + 民俗园夜景"],
                            "transport": ["南京 -> 长春 -> 延吉"],
                            "meals": ["服务大楼延吉冷面"],
                            "backup_spots": ["延边大学周边"],
                        }
                    ]
                }
            },
            "facts": [],
        })
        first_day = payload["outputs"]["daily-overview"]["days"][0]
        self.assertIn("上午：南京出发", " ".join(first_day["points"]))
        self.assertIn("下午：延吉西市场", " ".join(first_day["points"]))
```

- [ ] **Step 2: Run planning and compose tests and confirm failures**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_planning.py -v
python -m unittest discover -s tests/travel_skill -p test_compose.py -v
```

Expected:

```text
FAIL for missing build_trip_planning.py and compose not consuming planning payload
```

- [ ] **Step 3: Implement planning builder**

Create `.codex/skills/travel-skill/scripts/build_trip_planning.py`:

```python
from pathlib import Path
import argparse
import json

from travel_paths import ensure_trip_layout


def build_main_plan(payload: dict) -> dict:
    return {
        "plan_id": "main",
        "title": "最推荐路线",
        "strategy": "首晚延吉，长白山前夜二道白河，按天池窗口安排山景日",
        "days": [
            {
                "day": 1,
                "base_city": "延吉",
                "theme": "进场与延吉初逛",
                "morning": ["南京出发，按高铁优先或空铁联运进东北"],
                "afternoon": ["到达延吉后办理入住，先看西市场或延边大学周边"],
                "evening": ["安排冷面、包饭或烧烤作为第一顿城市体验"],
                "transport": ["南京 -> 长春", "长春 -> 延吉"],
                "meals": ["服务大楼延吉冷面", "元奶奶包饭·参鸡汤"],
                "backup_spots": ["延吉水上市场", "延吉咖啡馆"],
            }
        ],
    }


def build_option_plans(payload: dict) -> dict:
    return {
        "plans": [
            {"plan_id": "rail-first", "title": "高铁优先方案", "fit_for": "节奏稳定", "tradeoffs": ["耗时更长"], "days": build_main_plan(payload)["days"]},
            {"plan_id": "flight-hybrid", "title": "空铁联运方案", "fit_for": "压缩远程移动", "tradeoffs": ["成本更高"], "days": build_main_plan(payload)["days"]},
            {"plan_id": "extended-nearby", "title": "周边延伸方案", "fit_for": "想加图们或长春停留", "tradeoffs": ["总天数更长"], "days": build_main_plan(payload)["days"]},
        ]
    }
```

- [ ] **Step 4: Wire compose to planning-first daily output**

Update `.codex/skills/travel-skill/scripts/build_guide_model.py`:

```python
def _daily_plan_cards_from_planning(planning: dict) -> list[dict]:
    route_main = planning.get("route_main") if isinstance(planning, dict) else {}
    days = route_main.get("days") if isinstance(route_main, dict) else []
    cards = []
    for day in days if isinstance(days, list) else []:
        cards.append(
            _content_item(
                f"D{day['day']} {day['theme']}",
                f"落脚 {day['base_city']}，按白天与晚间节奏执行。",
                [
                    f"上午：{'；'.join(day.get('morning', []))}",
                    f"下午：{'；'.join(day.get('afternoon', []))}",
                    f"晚间：{'；'.join(day.get('evening', []))}",
                    f"交通：{'；'.join(day.get('transport', []))}",
                    f"用餐：{'；'.join(day.get('meals', []))}",
                    f"备选：{'；'.join(day.get('backup_spots', []))}",
                ],
            )
        )
    return cards
```

Then in `compose()` replace the old fallback:

```python
planning_payload = payload.get("planning") if isinstance(payload.get("planning"), dict) else {}
daily_day_cards = _daily_plan_cards_from_planning(planning_payload) or _daily_plan_cards(
    attraction_facts, food_facts, transport_facts, lodging_facts, traveler_notes
)
```

- [ ] **Step 5: Re-run planning and compose tests, then commit**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_planning.py -v
python -m unittest discover -s tests/travel_skill -p test_compose.py -v
git add tests/travel_skill/test_planning.py tests/travel_skill/test_compose.py .codex/skills/travel-skill/scripts/build_trip_planning.py .codex/skills/travel-skill/scripts/build_guide_model.py
git commit -m "feat: 引入逐日主方案与备选方案规划层"
```

Expected:

```text
OK
```

### Task 4: Add Media Validation and Video Extraction Gate

**Files:**
- Create: `.codex/skills/travel-skill/scripts/validate_media_assets.py`
- Create: `.codex/skills/travel-skill/scripts/extract_video_assets.py`
- Modify: `.codex/skills/travel-skill/scripts/build_image_plan.py`
- Create: `tests/travel_skill/test_media_pipeline.py`
- Modify: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Add failing tests for media gate**

Create `tests/travel_skill/test_media_pipeline.py`:

```python
from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import SKILL_DIR, run_script


class MediaPipelineTest(unittest.TestCase):
    def test_validate_media_assets_blocks_text_only_video_from_visual_slots(self):
        payload = {
            "items": [
                {
                    "platform": "bilibili",
                    "url": "https://www.bilibili.com/video/BV1xx",
                    "title": "长白山北坡攻略",
                    "has_clickable_link": True,
                    "keyframes": [],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "media.json"
            output_path = Path(tmp) / "validated.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "validate_media_assets.py", "--input", input_path, "--output", output_path)
            validated = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(validated["items"][0]["publish_state"], "text-citation-only")
            self.assertFalse(validated["items"][0]["can_render_as_visual"])
```

Add to `tests/travel_skill/test_render_package.py`:

```python
    def test_render_trip_site_skips_media_block_when_asset_not_publishable(self):
        model_payload = {
            "meta": {"trip_slug": "gate-demo", "title": "Gate Demo", "checked_at": "2026-04-13", "source_count": 1},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {"cover": {"image_hint": "B站搜索：长白山北坡攻略", "source_ref": "B站搜索：长白山北坡攻略", "image_url": "", "publish_state": "text-citation-only"}}
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "route-first")
            html = (output_root / "guides" / "gate-demo" / "desktop" / "route-first" / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("参考画面", html)
            self.assertNotIn("B站搜索：长白山北坡攻略", html)
```

- [ ] **Step 2: Run media and render tests and confirm failures**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_media_pipeline.py -v
python -m unittest discover -s tests/travel_skill -p test_render_package.py -v
```

Expected:

```text
FAIL for missing validate_media_assets.py and render still showing fake media text
```

- [ ] **Step 3: Implement media validation and environment-aware video extraction**

Create `.codex/skills/travel-skill/scripts/validate_media_assets.py`:

```python
from pathlib import Path
import argparse
import json


def classify_item(item: dict) -> dict:
    has_link = bool(str(item.get("url") or "").strip())
    keyframes = item.get("keyframes") if isinstance(item.get("keyframes"), list) else []
    if has_link and keyframes:
        state = "hero-ready" if len(keyframes) >= 2 else "illustrative-media"
        can_render = True
    elif has_link:
        state = "text-citation-only"
        can_render = False
    else:
        state = "blocked"
        can_render = False
    item = dict(item)
    item["publish_state"] = state
    item["can_render_as_visual"] = can_render
    return item
```

Create `.codex/skills/travel-skill/scripts/extract_video_assets.py`:

```python
from pathlib import Path
import argparse
import json
import shutil


def ffmpeg_ready() -> bool:
    return shutil.which("ffmpeg") is not None


def whisper_ready() -> bool:
    return shutil.which("whisper") is not None


def build_status(item: dict) -> dict:
    item = dict(item)
    item["ffmpeg_ready"] = ffmpeg_ready()
    item["whisper_ready"] = whisper_ready()
    item["transcript_status"] = "done" if item["whisper_ready"] else "missing-tool"
    item["keyframe_status"] = "done" if item["ffmpeg_ready"] else "missing-tool"
    return item
```

- [ ] **Step 4: Only pass publishable visuals into image-plan**

Update `.codex/skills/travel-skill/scripts/build_image_plan.py`:

```python
def _pick_visual(item: dict) -> dict:
    if item.get("publish_state") == "text-citation-only":
        return {
            "image_hint": "",
            "source_ref": item.get("title", ""),
            "image_url": "",
            "image_source_kind": "",
            "publish_state": "text-citation-only",
        }
```

And preserve `publish_state` in the section image records:

```python
                "publish_state": visual.get("publish_state", ""),
```

- [ ] **Step 5: Re-run media tests and commit**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_media_pipeline.py -v
python -m unittest discover -s tests/travel_skill -p test_render_package.py -v
git add tests/travel_skill/test_media_pipeline.py tests/travel_skill/test_render_package.py .codex/skills/travel-skill/scripts/validate_media_assets.py .codex/skills/travel-skill/scripts/extract_video_assets.py .codex/skills/travel-skill/scripts/build_image_plan.py
git commit -m "feat: 增加媒体门禁与视频解析状态"
```

Expected:

```text
OK
```

### Task 5: Replace Legacy Render Matrix with Five Distinct Publishing Templates

**Files:**
- Create: `.codex/skills/travel-skill/assets/templates/template-route-first.html`
- Create: `.codex/skills/travel-skill/assets/templates/template-decision-first.html`
- Create: `.codex/skills/travel-skill/assets/templates/template-destination-first.html`
- Create: `.codex/skills/travel-skill/assets/templates/template-transport-first.html`
- Create: `.codex/skills/travel-skill/assets/templates/template-lifestyle-first.html`
- Modify: `.codex/skills/travel-skill/scripts/render_trip_site.py`
- Modify: `.codex/skills/travel-skill/scripts/build_portal.py`
- Modify: `.codex/skills/travel-skill/scripts/export_single_html.py`
- Modify: `.codex/skills/travel-skill/scripts/package_trip.py`
- Modify: `tests/travel_skill/test_render_package.py`

- [ ] **Step 1: Add failing render tests for exactly five templates and no legacy output**

Add to `tests/travel_skill/test_render_package.py`:

```python
    def test_render_trip_site_emits_exactly_five_template_variants_under_guides_root(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root, "--style", "all")
            guide_root = output_root / "guides" / "wuyi-yanji-changbaishan"
            desktop_dirs = sorted(p.name for p in (guide_root / "desktop").iterdir() if p.is_dir())
            self.assertEqual(desktop_dirs, ["decision-first", "destination-first", "lifestyle-first", "route-first", "transport-first"])
            self.assertFalse((output_root / "trips").exists())
            self.assertFalse((guide_root / "desktop" / "recommended").exists())
```

- [ ] **Step 2: Run render/package tests and confirm failures**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_render_package.py -v
```

Expected:

```text
FAIL because render still writes under trips/ and still emits legacy directories
```

- [ ] **Step 3: Create five template manifests as real HTML skeletons**

Create `.codex/skills/travel-skill/assets/templates/template-route-first.html`:

```html
<section class="hero hero-route-first">{{ hero }}</section>
<main class="layout-route-first">
  <section class="daily-column">{{ daily_overview }}</section>
  <section class="support-column">{{ transport_details }}{{ food_by_city }}{{ clothing_guide }}{{ tips }}</section>
</main>
```

Create `.codex/skills/travel-skill/assets/templates/template-decision-first.html`:

```html
<section class="hero hero-decision-first">{{ hero }}</section>
<main class="layout-decision-first">
  <section class="decision-grid">{{ recommended_route }}{{ route_options }}</section>
  <section class="detail-stack">{{ daily_overview }}{{ transport_details }}{{ tips }}</section>
</main>
```

Create `.codex/skills/travel-skill/assets/templates/template-destination-first.html`:

```html
<section class="hero hero-destination-first">{{ hero }}</section>
<main class="layout-destination-first">
  <section class="destination-story">{{ attractions }}{{ food_by_city }}</section>
  <section class="trip-execution">{{ daily_overview }}{{ transport_details }}{{ clothing_guide }}</section>
</main>
```

Create `.codex/skills/travel-skill/assets/templates/template-transport-first.html`:

```html
<section class="hero hero-transport-first">{{ hero }}</section>
<main class="layout-transport-first">
  <section class="transport-flow">{{ transport_details }}{{ route_options }}</section>
  <section class="route-story">{{ daily_overview }}{{ attractions }}{{ food_by_city }}</section>
</main>
```

Create `.codex/skills/travel-skill/assets/templates/template-lifestyle-first.html`:

```html
<section class="hero hero-lifestyle-first">{{ hero }}</section>
<main class="layout-lifestyle-first">
  <section class="lifestyle-grid">{{ food_by_city }}{{ attractions }}{{ tips }}</section>
  <section class="plan-grid">{{ daily_overview }}{{ transport_details }}{{ clothing_guide }}</section>
</main>
```

- [ ] **Step 4: Render only the five new templates under guides/**

Update `.codex/skills/travel-skill/scripts/render_trip_site.py`:

```python
RENDER_TEMPLATES = [
    "route-first",
    "decision-first",
    "destination-first",
    "transport-first",
    "lifestyle-first",
]


def guide_root(output_root: Path, slug: str) -> Path:
    return output_root / "guides" / slug
```

Replace the legacy loop:

```python
selected_templates = RENDER_TEMPLATES if style == "all" else [style]
for device in ["desktop", "mobile"]:
    for template_id in selected_templates:
        target = guide_root(output_root, slug) / device / template_id / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_template_page(payload, template_id, device), encoding="utf-8")
```

Update hero rendering gate:

```python
if cover.get("publish_state") == "text-citation-only":
    return ""
```

- [ ] **Step 5: Update portal/export/package and commit**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_render_package.py -v
git add tests/travel_skill/test_render_package.py .codex/skills/travel-skill/scripts/render_trip_site.py .codex/skills/travel-skill/scripts/build_portal.py .codex/skills/travel-skill/scripts/export_single_html.py .codex/skills/travel-skill/scripts/package_trip.py .codex/skills/travel-skill/assets/templates/template-route-first.html .codex/skills/travel-skill/assets/templates/template-decision-first.html .codex/skills/travel-skill/assets/templates/template-destination-first.html .codex/skills/travel-skill/assets/templates/template-transport-first.html .codex/skills/travel-skill/assets/templates/template-lifestyle-first.html
git commit -m "feat: 发布五套独立编排模板"
```

Expected:

```text
OK
```

### Task 6: Add Verification Gates for Chinese Output, Fake Media, and Exact Template Count

**Files:**
- Modify: `.codex/skills/travel-skill/scripts/verify_trip.py`
- Modify: `tests/travel_skill/test_verify.py`

- [ ] **Step 1: Add failing verification tests**

Add to `tests/travel_skill/test_verify.py`:

```python
    def test_verify_trip_flags_fake_media_and_legacy_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "guides" / "demo-trip"
            (guide_root / "desktop" / "route-first").mkdir(parents=True)
            (guide_root / "desktop" / "route-first" / "index.html").write_text("对标样本 B站搜索：长白山北坡攻略", encoding="utf-8")
            payload = verify_trip(guide_root)
            self.assertIn("no_sample_reference_in_publish", payload["content_checks"])
            self.assertFalse(payload["content_checks"]["no_sample_reference_in_publish"])
            self.assertFalse(payload["content_checks"]["no_fake_media_blocks"])
```

- [ ] **Step 2: Run verify tests and confirm failures**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_verify.py -v
```

Expected:

```text
FAIL because verify_trip.py does not yet scan for fake media text or exact template count
```

- [ ] **Step 3: Implement verification checks**

Update `.codex/skills/travel-skill/scripts/verify_trip.py`:

```python
def scan_html_text(root: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.html"))


def verify_trip(guide_root: Path) -> dict:
    html_blob = scan_html_text(guide_root)
    template_dirs = sorted(p.name for p in (guide_root / "desktop").iterdir() if p.is_dir()) if (guide_root / "desktop").exists() else []
    content_checks = {
        "all_primary_text_in_zh": "Travel Skill" not in html_blob,
        "no_sample_reference_in_publish": "对标样本" not in html_blob and "sample.html" not in html_blob,
        "no_fake_media_blocks": "B站搜索：" not in html_blob and "抖音搜索：" not in html_blob and "来源参考：" not in html_blob,
        "exactly_five_templates": template_dirs == ["decision-first", "destination-first", "lifestyle-first", "route-first", "transport-first"],
    }
    status = "pass" if all(content_checks.values()) else "fail"
    return {"content_checks": content_checks, "status": status}
```

- [ ] **Step 4: Re-run verify tests and commit**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_verify.py -v
git add tests/travel_skill/test_verify.py .codex/skills/travel-skill/scripts/verify_trip.py
git commit -m "feat: 增加中文化与伪媒体发布校验"
```

Expected:

```text
OK
```

### Task 7: Migrate the Nanjing-Yanji-Changbaishan Sample and Align Skill Docs

**Files:**
- Modify: `.codex/skills/travel-skill/SKILL.md`
- Modify: `.codex/skills/travel-skill/scripts/normalize_request.py`
- Modify: `.codex/skills/travel-skill/scripts/build_research_tasks.py`
- Modify: `.codex/skills/travel-skill/scripts/build_web_research_runs.py`
- Modify: all scripts touched above

- [ ] **Step 1: Update request normalization to point at the new trip root**

Update `.codex/skills/travel-skill/scripts/normalize_request.py`:

```python
def normalize(payload: dict) -> dict:
    trip_slug = slugify(payload["title"])
    return {
        ...
        "trip_slug": trip_slug,
        "data_layout": {
            "places_root": "travel-data/places",
            "corridors_root": "travel-data/corridors",
            "trip_root": f"travel-data/trips/{trip_slug}",
            "guides_root": f"travel-data/guides/{trip_slug}",
        },
    }
```

- [ ] **Step 2: Update skill documentation to describe the dual-track output**

Add to `.codex/skills/travel-skill/SKILL.md`:

```markdown
## Output Layout

- Reusable destination knowledge is written under `travel-data/places/`.
- Reusable city-to-city transport is written under `travel-data/corridors/`.
- Trip-scoped request, planning, and snapshots are written under `travel-data/trips/<trip-slug>/`.
- Final guide artifacts are written under `travel-data/guides/<trip-slug>/`.
- Video parsing is required for publishable video media. If keyframes or clickable source links are missing, the media is downgraded to text citation only.
```

- [ ] **Step 3: Run the full travel-skill test suite**

Run:

```powershell
python -m unittest discover -s tests/travel_skill -p test_*.py -v
```

Expected:

```text
OK
```

- [ ] **Step 4: Generate the sample trip through the new path layout and inspect outputs**

Run:

```powershell
python .codex/skills/travel-skill/scripts/normalize_request.py --input travel-data/2026-mayday-nanjing-yanji-changbaishan/request.raw.json --output travel-data/trips/2026-mayday-nanjing-yanji-changbaishan/request/normalized.json
python .codex/skills/travel-skill/scripts/build_trip_snapshots.py --input travel-data/trips/2026-mayday-nanjing-yanji-changbaishan/request/normalized.json --data-root travel-data
python .codex/skills/travel-skill/scripts/build_trip_planning.py --input travel-data/2026-mayday-nanjing-yanji-changbaishan/approved-research.json --output-root travel-data
python .codex/skills/travel-skill/scripts/render_trip_site.py --input travel-data/2026-mayday-nanjing-yanji-changbaishan/guide-content.json --output-root travel-data --style all
python .codex/skills/travel-skill/scripts/verify_trip.py --guide-root travel-data/guides/2026-mayday-nanjing-yanji-changbaishan --output travel-data/guides/2026-mayday-nanjing-yanji-changbaishan/verify/verify-report.json
```

Expected:

```text
places/, corridors/, trips/, guides/ all populated
verify-report.json status == "pass" or "warn" with explicit media/tool warnings only
```

- [ ] **Step 5: Commit the migration-ready implementation**

Run:

```powershell
git add .codex/skills/travel-skill/SKILL.md .codex/skills/travel-skill/scripts tests/travel_skill
git commit -m "feat: 完成 travel-skill 双轨重构首版"
```

Expected:

```text
[feature/travel-skill-dual-track-redesign ...] feat: 完成 travel-skill 双轨重构首版
```

---

## Self-Review

**Spec coverage**

- 双轨目录：Task 1, Task 2, Task 7
- 目的地与交通走廊沉淀：Task 2
- 逐日主方案与多方案：Task 3
- 视频解析必选与媒体门禁：Task 4
- 五套独立模板与单独 guides 产物：Task 5
- 验证与失败策略：Task 6
- 技能文档与样例迁移：Task 7

**Placeholder scan**

- No `TODO`
- No `TBD`
- No “similar to Task N”
- All run commands and expected results are explicit

**Type consistency**

- Path helper uses `travel_roots()` / `ensure_trip_layout()`
- Planning contract uses `route_main`, `plans`, and `days`
- Media gate uses `publish_state` and `can_render_as_visual`
- Verification checks use `content_checks` and `status`
