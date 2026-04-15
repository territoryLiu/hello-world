# Travel-Skill Research Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `travel-skill` so domestic free-travel requests produce a heavy-sampling research dossier with dual time layers, source-specific coverage accounting, video fallback support, reusable knowledge files, and a research-report HTML artifact.

**Architecture:** Add a shared research-contract layer first, then thread those contracts through task planning, source collection, video fallback, knowledge persistence, coverage validation, and report rendering. Keep the existing script-oriented pipeline, but make every stage emit explicit `coverage_status`, `missing_fields`, `failure_reason`, `time_layer`, and source evidence so later guide generation can trust the data.

**Tech Stack:** Python 3.12 in `C:\Users\Lenovo\.conda\envs\stock-analyzer`, built-in `unittest`, JSON, existing `travel-skill` scripts, `yt-dlp`, `ffmpeg`, `whisper` tooling when available.

---

**Execution note:** `d:\vscode\video` is not a Git repository. Implement the plan in `C:\Users\Lenovo\.codex\skills\travel-skill\`, and use the verification steps below as checkpoints. If the skill directory is later moved into Git, add commits at the end of each task.

## File Map

- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\references\content-schema.md`
  Purpose: document the richer research task, normalized evidence, coverage report, and research dossier fields.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\research_contracts.py`
  Purpose: single source of truth for time layers, heavy sample targets, required fields, failure reasons, and topic groups.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\travel_config.py`
  Purpose: expose the source coverage matrix plus default heavy-sampling config used by task planning and validation.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_research_tasks.py`
  Purpose: generate heavy-sampling, dual-time-layer research tasks with explicit sample targets and retry policy.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_web_research_runs.py`
  Purpose: push richer prompt contracts into `web-access` runs, including time layer, sample target, and fallback guidance.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\video_pipeline.py`
  Purpose: centralize tool detection and video fallback command planning for `yt-dlp`, `ffmpeg`, and `whisper`.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_video_research_json.py`
  Purpose: normalize video evidence into timestamped transcript, visual segments, media artifacts, failure details, and time-layer metadata.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\extract_video_assets.py`
  Purpose: perform or plan real video fallback extraction instead of only reporting missing tools.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\extract_structured_facts.py`
  Purpose: turn raw entries into topic-grouped knowledge points with evidence refs and dual-layer metadata.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\persist_research_knowledge.py`
  Purpose: persist raw, normalized, knowledge, coverage, and media outputs into `travel-data\places\<place-slug>\raw|normalized|knowledge|coverage|media`.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\validate_site_coverage.py`
  Purpose: validate sample counts, required fields, missing fields, and final `coverage_status` per source and topic.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\verify_trip.py`
  Purpose: treat the research dossier as a first-class artifact and verify required sections and files.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\render_trip_site.py`
  Purpose: render `research-report.html` with coverage overview, dual-time-layer findings, evidence cards, and gaps.
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\assets\templates\render-guide.js`
  Purpose: teach the front-end renderer how to display research-report sections and evidence cards.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\__init__.py`
  Purpose: make the test directory importable.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_research_contracts.py`
  Purpose: lock the contract constants and coverage helper behavior.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_build_research_tasks.py`
  Purpose: verify heavy-sampling and dual-time-layer task generation.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_video_pipeline.py`
  Purpose: verify video fallback planning and video record normalization.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_persist_research_knowledge.py`
  Purpose: verify layered storage and knowledge persistence.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_validate_site_coverage.py`
  Purpose: verify hard coverage rules and gap reporting.
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_render_research_report.py`
  Purpose: verify the dossier HTML includes the required sections.

### Task 1: Establish Shared Research Contracts

**Files:**
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\research_contracts.py`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\__init__.py`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_research_contracts.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\references\content-schema.md`

- [ ] **Step 1: Write the failing contract tests**

```python
import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from research_contracts import (
    TIME_LAYERS,
    HEAVY_SAMPLE_TARGETS,
    FAILURE_REASONS,
    site_required_fields,
)


class ResearchContractsTest(unittest.TestCase):
    def test_time_layers_are_dual_layer(self):
        self.assertEqual(TIME_LAYERS, ("recent", "last_year_same_period"))

    def test_heavy_sampling_defaults_match_product_decisions(self):
        self.assertEqual(HEAVY_SAMPLE_TARGETS["xiaohongshu"], 20)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["douyin"], 10)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["bilibili"], 10)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["dianping"], 15)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["meituan"], 15)

    def test_failure_reasons_include_video_and_time_layer_cases(self):
        self.assertIn("video_download_failed", FAILURE_REASONS)
        self.assertIn("time_layer_not_determined", FAILURE_REASONS)

    def test_xiaohongshu_requires_comment_and_media_fields(self):
        required = site_required_fields("xiaohongshu")
        self.assertIn("comment_highlights", required)
        self.assertIn("comment_sample_size", required)
        self.assertIn("image_candidates", required)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_research_contracts.py' -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'research_contracts'`.

- [ ] **Step 3: Implement the shared contracts and update the schema reference**

```python
# C:\Users\Lenovo\.codex\skills\travel-skill\scripts\research_contracts.py
TIME_LAYERS = ("recent", "last_year_same_period")

HEAVY_SAMPLE_TARGETS = {
    "official": 1,
    "xiaohongshu": 20,
    "douyin": 10,
    "bilibili": 10,
    "dianping": 15,
    "meituan": 15,
}

FAILURE_REASONS = {
    "login_required",
    "anti_bot_blocked",
    "page_unreachable",
    "content_removed",
    "comment_not_loaded",
    "insufficient_sample_size",
    "video_download_failed",
    "audio_transcription_failed",
    "keyframe_extraction_failed",
    "schema_validation_failed",
    "time_layer_not_determined",
}

SITE_REQUIRED_FIELDS = {
    "xiaohongshu": [
        "title", "summary", "author", "publish_time", "source_url",
        "comment_highlights", "comment_sample_size", "image_candidates",
        "coverage_status", "failure_reason", "missing_fields", "time_layer",
    ],
    "douyin": [
        "title", "summary", "author", "publish_time", "source_url",
        "comment_highlights", "transcript_segments", "visual_segments",
        "timeline", "shot_candidates", "coverage_status", "failure_reason",
        "missing_fields", "time_layer",
    ],
    "bilibili": [
        "title", "summary", "author", "publish_time", "source_url",
        "comment_highlights", "transcript_segments", "visual_segments",
        "timeline", "shot_candidates", "coverage_status", "failure_reason",
        "missing_fields", "time_layer",
    ],
    "dianping": [
        "shop_name", "address", "per_capita_range", "recommended_dishes",
        "queue_pattern", "review_themes", "pitfalls", "coverage_status",
        "failure_reason", "missing_fields", "time_layer",
    ],
    "meituan": [
        "shop_name", "address", "per_capita_range", "recommended_dishes",
        "queue_pattern", "review_themes", "pitfalls", "coverage_status",
        "failure_reason", "missing_fields", "time_layer",
    ],
}


def site_required_fields(site: str) -> list[str]:
    return list(SITE_REQUIRED_FIELDS.get(site, []))
```

```markdown
<!-- C:\Users\Lenovo\.codex\skills\travel-skill\references\content-schema.md -->
## research_task

- `trip_slug`
- `place`
- `topic`
- `platform`
- `site`
- `required_sources`
- `query_hint`
- `site_query`
- `collection_method`
- `must_capture_fields`
- `evidence_level`
- `time_layer`
- `sample_target`
- `retry_policy`
- `fallback_policy`

## normalized_research_record

- `source_type`
- `collector_mode`
- `coverage_status`
- `failure_reason`
- `failure_detail`
- `missing_fields`
- `checked_at`
- `time_layer`
- `evidence_refs`
- `knowledge_points`

## coverage_report

- `site`
- `topic`
- `sample_target`
- `actual_sample_count`
- `complete_count`
- `partial_count`
- `failed_count`
- `missing_required_fields`
- `coverage_status`
- `failure_reason_counts`
```

- [ ] **Step 4: Run the contract tests again**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_research_contracts.py' -v
```

Expected: PASS with 4 passing tests.

### Task 2: Generate Heavy-Sampling, Dual-Layer Research Tasks

**Files:**
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\travel_config.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_research_tasks.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_web_research_runs.py`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_build_research_tasks.py`

- [ ] **Step 1: Write the failing task-generation tests**

```python
import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_research_tasks import build_tasks


class BuildResearchTasksTest(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "trip_slug": "hangzhou-spring-trip",
            "title": "杭州春季自由行",
            "departure_city": "上海",
            "destinations": ["杭州"],
            "required_topics": ["attractions", "food", "risks"],
        }

    def test_tasks_include_dual_layers_for_social_topics(self):
        tasks = build_tasks(self.payload)["tasks"]
        xhs_layers = {task["time_layer"] for task in tasks if task["site"] == "xiaohongshu"}
        self.assertEqual(xhs_layers, {"recent", "last_year_same_period"})

    def test_tasks_include_heavy_sample_targets(self):
        tasks = build_tasks(self.payload)["tasks"]
        douyin_targets = {task["sample_target"] for task in tasks if task["site"] == "douyin"}
        self.assertEqual(douyin_targets, {10})

    def test_web_runs_prompt_mentions_time_layer_and_sample_target(self):
        from build_web_research_runs import build_runs
        planned = build_runs({"trip_slug": "hangzhou-spring-trip", "tasks": build_tasks(self.payload)["tasks"]})
        prompt = planned["runs"][0]["prompt"]
        self.assertIn("time_layer=", prompt)
        self.assertIn("sample_target=", prompt)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the task-generation tests to verify they fail**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_build_research_tasks.py' -v
```

Expected: FAIL because the generated tasks do not yet contain `time_layer` or `sample_target`, and the prompt does not mention them.

- [ ] **Step 3: Implement dual-layer task planning and richer run prompts**

```python
# C:\Users\Lenovo\.codex\skills\travel-skill\scripts\travel_config.py
from research_contracts import HEAVY_SAMPLE_TARGETS

SITE_COVERAGE_TARGETS = {
    "food": ["meituan", "dianping", "xiaohongshu"],
    "attractions": ["official", "xiaohongshu", "douyin", "bilibili"],
    "risks": ["xiaohongshu", "douyin", "bilibili"],
}

TIME_LAYER_TOPICS = {
    "weather",
    "clothing",
    "packing",
    "attractions",
    "food",
    "seasonality",
    "risks",
}
```

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_research_tasks.py
from research_contracts import HEAVY_SAMPLE_TARGETS, TIME_LAYERS
from travel_config import TIME_LAYER_TOPICS


def _layers_for_topic(topic: str) -> list[str]:
    return list(TIME_LAYERS) if topic in TIME_LAYER_TOPICS else ["recent"]


def build_tasks(payload: dict) -> dict:
    tasks = []
    places = [item for item in payload.get("destinations", []) if isinstance(item, str) and item.strip()]
    topics = payload.get("required_topics", [])
    for place in places:
        for topic in topics:
            site_rules = TOPIC_SITE_RULES.get(topic, [{"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary"], "evidence_level": "primary"}])
            for time_layer in _layers_for_topic(topic):
                for rule in site_rules:
                    site = rule["site"]
                    tasks.append(
                        {
                            "trip_slug": payload["trip_slug"],
                            "place": place,
                            "topic": topic,
                            "platform": rule["platform"],
                            "site": site,
                            "required_sources": [item["site"] for item in site_rules],
                            "query_hint": f"{payload['departure_city']} {payload['title']} {place} {topic}",
                            "site_query": site_query(payload, place, topic, site),
                            "collection_method": rule["collection_method"],
                            "must_capture_fields": list(rule["must_capture_fields"]),
                            "evidence_level": rule["evidence_level"],
                            "time_layer": time_layer,
                            "sample_target": HEAVY_SAMPLE_TARGETS.get(site, 1),
                            "retry_policy": "retry_same_mode",
                            "fallback_policy": "page_first_then_fallback",
                        }
                    )
    return {
        "trip_slug": payload["trip_slug"],
        "research_dimensions": ["place", "topic", "platform", "site", "time_layer"],
        "places": places,
        "tasks": tasks,
    }
```

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_web_research_runs.py
def _capture_contract(task: dict) -> str:
    site = str(task.get("site") or "").lower()
    time_layer = str(task.get("time_layer") or "recent")
    sample_target = int(task.get("sample_target") or 1)
    instructions = [
        f"time_layer={time_layer}.",
        f"sample_target={sample_target}.",
        "Record missing_fields when any required field is absent.",
        "Use retry_same_mode before degrade_or_fallback.",
    ]
    if site in {"xiaohongshu", "douyin", "bilibili"}:
        instructions.append("Capture page body, comments, comment status, and comment sample size.")
    if site in {"douyin", "bilibili"}:
        instructions.append("When page evidence is insufficient, run video fallback and capture transcript_segments, timeline, visual_segments, and shot_candidates.")
    instructions.append("If collection still fails, set coverage_status to partial or failed and persist failure_reason plus failure_detail.")
    return " ".join(instructions)
```

- [ ] **Step 4: Run the task-generation tests again**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_build_research_tasks.py' -v
```

Expected: PASS with all tests green.

- [ ] **Step 5: Run the contract and task tests together**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_*.py' -v
```

Expected: PASS for `test_research_contracts.py` and `test_build_research_tasks.py`.

### Task 3: Build the Video Fallback Pipeline

**Files:**
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\video_pipeline.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_video_research_json.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\extract_video_assets.py`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_video_pipeline.py`

- [ ] **Step 1: Write the failing video-pipeline tests**

```python
import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_video_research_json import build_video_record
from video_pipeline import build_fallback_plan


class VideoPipelineTest(unittest.TestCase):
    def test_fallback_plan_contains_download_audio_keyframe_and_transcript_steps(self):
        plan = build_fallback_plan("https://example.com/video", Path("C:/tmp/assets"))
        stages = [step["stage"] for step in plan["steps"]]
        self.assertEqual(stages, ["download", "extract_audio", "keyframes", "transcribe"])

    def test_video_record_tracks_time_layer_and_missing_fields(self):
        item = build_video_record(
            {
                "url": "https://example.com/video",
                "platform": "douyin",
                "collector_mode": "video-fallback",
                "coverage_status": "partial",
                "time_layer": "recent",
                "missing_fields": ["transcript_segments"],
            }
        )
        self.assertEqual(item["time_layer"], "recent")
        self.assertEqual(item["missing_fields"], ["transcript_segments"])
        self.assertEqual(item["collector_mode"], "video-fallback")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the video-pipeline tests to verify they fail**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_video_pipeline.py' -v
```

Expected: FAIL because `video_pipeline.py` does not exist and `build_video_record()` does not emit the new fields.

- [ ] **Step 3: Implement video fallback planning and richer normalized records**

```python
# C:\Users\Lenovo\.codex\skills\travel-skill\scripts\video_pipeline.py
from pathlib import Path
import shutil


def detect_tools() -> dict[str, str]:
    return {
        "yt_dlp": shutil.which("yt-dlp") or "",
        "ffmpeg": shutil.which("ffmpeg") or "",
        "whisper": shutil.which("whisper") or "",
    }


def build_fallback_plan(url: str, asset_root: Path) -> dict:
    video_path = asset_root / "video.mp4"
    audio_path = asset_root / "audio.wav"
    keyframe_dir = asset_root / "keyframes"
    transcript_path = asset_root / "transcript.json"
    return {
        "tools": detect_tools(),
        "steps": [
            {"stage": "download", "command": ["yt-dlp", "-o", str(video_path), url]},
            {"stage": "extract_audio", "command": ["ffmpeg", "-y", "-i", str(video_path), str(audio_path)]},
            {"stage": "keyframes", "command": ["ffmpeg", "-y", "-i", str(video_path), "-vf", "fps=1/8", str(keyframe_dir / "frame-%03d.jpg")]},
            {"stage": "transcribe", "command": ["whisper", str(audio_path), "--output_format", "json", "--output_dir", str(asset_root)]},
        ],
        "artifacts": {
            "video": str(video_path),
            "audio": str(audio_path),
            "keyframe_dir": str(keyframe_dir),
            "transcript": str(transcript_path),
        },
    }
```

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\build_video_research_json.py
def build_video_record(item: dict) -> dict:
    return {
        "source_url": str(item.get("url") or ""),
        "platform": str(item.get("platform") or ""),
        "collected_at": str(item.get("collected_at") or ""),
        "collector_mode": str(item.get("collector_mode") or "page-only"),
        "coverage_status": str(item.get("coverage_status") or "partial"),
        "failure_reason": str(item.get("failure_reason") or ""),
        "failure_detail": str(item.get("failure_detail") or ""),
        "missing_fields": item.get("missing_fields") if isinstance(item.get("missing_fields"), list) else [],
        "time_layer": str(item.get("time_layer") or "recent"),
        "author": str(item.get("author") or ""),
        "title": str(item.get("title") or ""),
        "publish_time": str(item.get("published_at") or ""),
        "duration_sec": item.get("duration_sec") or 0,
        "page_text": str(item.get("summary") or ""),
        "comment_highlights": _list(item.get("comment_highlights")),
        "transcript_segments": _list(item.get("transcript_segments")),
        "visual_segments": _list(item.get("visual_segments")),
        "timeline": _list(item.get("timeline")),
        "shot_candidates": _list(item.get("shot_candidates")),
        "media_artifacts": _list(item.get("media_artifacts")),
    }
```

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\extract_video_assets.py
from pathlib import Path
from video_pipeline import build_fallback_plan


def build_status(item: dict) -> dict:
    asset_root = Path(item.get("asset_root") or Path.cwd() / "video-assets")
    plan = build_fallback_plan(str(item.get("url") or ""), asset_root)
    item = dict(item)
    item["fallback_plan"] = plan
    item["media_artifacts"] = [{"kind": key, "path": value} for key, value in plan["artifacts"].items()]
    tools = plan["tools"]
    missing = [name for name, value in tools.items() if not value]
    item["missing_fields"] = list(item.get("missing_fields") or [])
    if missing:
        item["coverage_status"] = "partial"
        item["failure_reason"] = "video_download_failed" if "yt_dlp" in missing else "audio_transcription_failed"
        item["failure_detail"] = f"Missing tools: {', '.join(missing)}"
    return item
```

- [ ] **Step 4: Run the video-pipeline tests again**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_video_pipeline.py' -v
```

Expected: PASS with 2 passing tests.

### Task 4: Persist Dual-Layer Knowledge and Layered Storage

**Files:**
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\extract_structured_facts.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\persist_research_knowledge.py`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_persist_research_knowledge.py`

- [ ] **Step 1: Write the failing persistence tests**

```python
import tempfile
import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from persist_research_knowledge import persist


class PersistResearchKnowledgeTest(unittest.TestCase):
    def test_persist_writes_recent_and_last_year_layers(self):
        raw_payload = {"records": [{"place": "杭州", "site": "xiaohongshu", "topic": "attractions", "time_layer": "recent"}]}
        approved_payload = {"facts": [{"place": "杭州", "topic": "attractions", "site": "xiaohongshu", "text": "西湖早晨人少", "time_layer": "last_year_same_period"}]}
        media_payload = {"items": [{"place": "杭州", "kind": "keyframe", "path": "frame-001.jpg"}]}
        coverage_payload = {"trip_slug": "hangzhou", "by_topic": {"attractions": {"coverage_status": "complete"}}}

        with tempfile.TemporaryDirectory() as tmp:
            persist(raw_payload, approved_payload, media_payload, coverage_payload, Path(tmp))
            place_root = Path(tmp) / "places" / "hangzhou"
            self.assertTrue((place_root / "knowledge" / "recent.json").exists())
            self.assertTrue((place_root / "knowledge" / "last-year-same-period.json").exists())
            self.assertTrue((place_root / "coverage" / "site-coverage.json").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the persistence test to verify it fails**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_persist_research_knowledge.py' -v
```

Expected: FAIL because the current persistence layout does not create `knowledge/recent.json` or `knowledge/last-year-same-period.json`.

- [ ] **Step 3: Implement topic-grouped knowledge points and layered storage**

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\extract_structured_facts.py
def extract(payload: dict) -> dict:
    by_place: dict[str, dict[str, list[dict]]] = {}
    facts = []
    knowledge_points = []
    for raw_entry in payload.get("entries", []):
        entry = raw_entry if isinstance(raw_entry, dict) else {}
        place = str(entry.get("place", ""))
        topic = str(entry.get("topic", entry.get("category", "")))
        platform = str(entry.get("platform", ""))
        site = str(entry.get("site", platform or "unknown"))
        source_url = str(entry.get("url", ""))
        checked_at = str(entry.get("checked_at", ""))
        source_type = str(entry.get("source_type", ""))
        source_title = str(entry.get("title", ""))
        raw_facts = entry.get("facts", [])
        if raw_facts is None:
            raw_facts = []
        facts_iterable = raw_facts if isinstance(raw_facts, list) else [raw_facts]
        time_layer = str(entry.get("time_layer", "recent"))
        for fact in facts_iterable:
            text = _fact_to_text(fact).strip()
            if not text:
                continue
            fact_item = {
                "place": place,
                "topic": topic,
                "platform": platform,
                "site": site,
                "text": text,
                "source_url": source_url,
                "checked_at": checked_at,
                "source_type": source_type,
                "source_title": source_title,
                "time_layer": time_layer,
            }
            knowledge_points.append(
                {
                    "place": place,
                    "topic": topic,
                    "time_layer": time_layer,
                    "claim": text,
                    "evidence_refs": [source_url] if source_url else [],
                }
            )
            by_place.setdefault(place, {}).setdefault(topic, []).append(fact_item)
            facts.append(fact_item)
    return {"by_place": by_place, "facts": facts, "knowledge_points": knowledge_points}
```

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\persist_research_knowledge.py
def persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root: Path) -> None:
    raw_records = _iter_records(raw_payload, "records")
    approved_facts = _iter_records(approved_payload, "facts")
    media_records = _iter_records(media_payload, "items")
    coverage_by_topic = coverage_payload.get("by_topic") if isinstance(coverage_payload, dict) else {}
    coverage_by_topic = coverage_by_topic if isinstance(coverage_by_topic, dict) else {}
    trip_slug = str(coverage_payload.get("trip_slug") or "")
    places = _collect_places(raw_records, approved_facts, media_records)
    for place in places:
        place_slug = _place_slug(place)
        place_root = output_root / "places" / place_slug
        place_raw = [item for item in raw_records if item.get("place") == place]
        place_facts = [item for item in approved_facts if item.get("place") == place]
        place_media = [item for item in media_records if item.get("place") == place]

        recent_facts = [item for item in place_facts if item.get("time_layer") == "recent"]
        historical_facts = [item for item in place_facts if item.get("time_layer") == "last_year_same_period"]

        _write_json(place_root / "raw" / "web-research.json", {"trip_slug": trip_slug, "place": place, "records": place_raw})
        _write_json(place_root / "normalized" / "facts.json", {"trip_slug": trip_slug, "place": place, "facts": place_facts})
        _write_json(place_root / "knowledge" / "recent.json", {"trip_slug": trip_slug, "place": place, "facts": recent_facts})
        _write_json(place_root / "knowledge" / "last-year-same-period.json", {"trip_slug": trip_slug, "place": place, "facts": historical_facts})
        _write_json(place_root / "media" / "items.json", {"trip_slug": trip_slug, "place": place, "items": place_media})
        _write_json(place_root / "coverage" / "site-coverage.json", {"trip_slug": trip_slug, "place": place, "site_coverage": coverage_by_topic})
```

- [ ] **Step 4: Run the persistence test again**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_persist_research_knowledge.py' -v
```

Expected: PASS with the layered files present.

### Task 5: Harden Coverage Validation and Verification

**Files:**
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\validate_site_coverage.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\verify_trip.py`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_validate_site_coverage.py`

- [ ] **Step 1: Write the failing coverage-validation tests**

```python
import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_site_coverage import validate


class ValidateSiteCoverageTest(unittest.TestCase):
    def test_marks_partial_when_sample_target_is_not_met(self):
        payload = {
            "records": [
                {"topic": "attractions", "site": "xiaohongshu", "coverage_status": "complete", "missing_fields": [], "time_layer": "recent"}
            ]
        }
        report = validate(payload)
        self.assertEqual(report["by_site"]["xiaohongshu"]["coverage_status"], "partial")
        self.assertIn("insufficient_sample_size", report["by_site"]["xiaohongshu"]["failure_reasons"])

    def test_topic_report_keeps_missing_sites(self):
        payload = {"records": [{"topic": "food", "site": "xiaohongshu", "coverage_status": "complete", "missing_fields": []}]}
        report = validate(payload)
        self.assertIn("dianping", report["by_topic"]["food"]["missing_required_sites"])
        self.assertIn("meituan", report["by_topic"]["food"]["missing_required_sites"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the coverage-validation tests to verify they fail**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_validate_site_coverage.py' -v
```

Expected: FAIL because the current validator only reports seen vs missing sites and does not compute `by_site`, sample targets, or failure reasons.

- [ ] **Step 3: Implement hard coverage evaluation and dossier verification**

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\validate_site_coverage.py
from research_contracts import HEAVY_SAMPLE_TARGETS


def validate(payload: dict) -> dict:
    records = payload.get("records", [])
    by_topic = {}
    by_site = {}
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        site = str(record.get("site", ""))
        topic = str(record.get("topic", ""))
        site_bucket = by_site.setdefault(site, {"sample_target": HEAVY_SAMPLE_TARGETS.get(site, 1), "actual_sample_count": 0, "failure_reasons": set(), "missing_required_fields": set()})
        site_bucket["actual_sample_count"] += 1
        for missing in record.get("missing_fields", []) if isinstance(record.get("missing_fields"), list) else []:
            site_bucket["missing_required_fields"].add(missing)
        if record.get("failure_reason"):
            site_bucket["failure_reasons"].add(str(record["failure_reason"]))
        topic_bucket = by_topic.setdefault(topic, {"seen_sites": set(), "missing_required_sites": []})
        if site:
            topic_bucket["seen_sites"].add(site)
    for site, bucket in by_site.items():
        bucket["coverage_status"] = "complete" if bucket["actual_sample_count"] >= bucket["sample_target"] and not bucket["missing_required_fields"] else "partial"
        if bucket["actual_sample_count"] < bucket["sample_target"]:
            bucket["failure_reasons"].add("insufficient_sample_size")
        bucket["failure_reasons"] = sorted(bucket["failure_reasons"])
        bucket["missing_required_fields"] = sorted(bucket["missing_required_fields"])
    for topic, required_sites in REQUIRED_SITE_MATRIX.items():
        topic_bucket = by_topic.setdefault(topic, {"seen_sites": set(), "missing_required_sites": []})
        topic_bucket["missing_required_sites"] = sorted(site for site in required_sites if site not in topic_bucket["seen_sites"])
        topic_bucket["seen_sites"] = sorted(topic_bucket["seen_sites"])
    return {"has_gaps": any(bucket["coverage_status"] != "complete" for bucket in by_site.values()), "by_topic": by_topic, "by_site": by_site}
```

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\verify_trip.py
def verify_trip(guide_root: Path) -> dict:
    html_blob = scan_html_text(guide_root)
    content_checks = {
        "research_report_present": (guide_root / "research-report.html").exists(),
        "coverage_overview_present": "覆盖总览" in html_blob,
        "dual_time_layer_present": "最新现状" in html_blob and "去年同期经验" in html_blob,
        "gaps_section_present": "缺口与失败" in html_blob,
        "source_appendix_present": "来源附录" in html_blob,
        "notes_sources_present": all((guide_root / "notes" / name).exists() for name in ["sources.md", "sources.html"]),
    }
    browser_check = verify_render_with_playwright(guide_root)
    warnings = []
    if browser_check.get("status") == "warn":
        warnings.append(browser_check.get("reason", "browser verification skipped"))
    status = "pass" if all(content_checks.values()) else "fail"
    return {
        "content_checks": content_checks,
        "status": status,
        "warnings": warnings,
        "playwright_check": browser_check,
    }
```

- [ ] **Step 4: Run the coverage-validation tests again**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_validate_site_coverage.py' -v
```

Expected: PASS with both tests green.

### Task 6: Render the Research Dossier HTML

**Files:**
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\scripts\render_trip_site.py`
- Modify: `C:\Users\Lenovo\.codex\skills\travel-skill\assets\templates\render-guide.js`
- Create: `C:\Users\Lenovo\.codex\skills\travel-skill\tests\test_render_research_report.py`

- [ ] **Step 1: Write the failing dossier-render tests**

```python
import tempfile
import unittest
import sys
from pathlib import Path

SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from render_trip_site import render_trip_site


class RenderResearchReportTest(unittest.TestCase):
    def test_render_trip_site_outputs_research_report_sections(self):
        payload = {
            "trip_slug": "hangzhou-spring-trip",
            "research_report": {
                "coverage_overview": [{"site": "xiaohongshu", "coverage_status": "complete"}],
                "quick_findings": ["西湖工作日早晨更适合拍照"],
                "theme_blocks": [{"title": "景观与季节性", "recent": ["柳树已绿"], "historical": ["去年同期花期稳定"]}],
                "evidence_cards": [{"title": "小红书帖子 A", "platform": "xiaohongshu", "time_layer": "recent"}],
                "gaps": [{"site": "douyin", "reason": "insufficient_sample_size"}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            render_trip_site(payload, Path(tmp))
            html_text = (Path(tmp) / "research-report.html").read_text(encoding="utf-8")
            self.assertIn("覆盖总览", html_text)
            self.assertIn("最新现状", html_text)
            self.assertIn("去年同期经验", html_text)
            self.assertIn("缺口与失败", html_text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the dossier-render test to verify it fails**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_render_research_report.py' -v
```

Expected: FAIL because `render_trip_site.py` does not yet emit a `research-report.html` dossier with the required sections.

- [ ] **Step 3: Implement research-report rendering**

```python
# inside C:\Users\Lenovo\.codex\skills\travel-skill\scripts\render_trip_site.py
def _render_research_report(report: dict) -> str:
    coverage_cards = "".join(
        f"<li><strong>{_escape(item.get('site'))}</strong> · {_escape(item.get('coverage_status'))}</li>"
        for item in _safe_list(report.get("coverage_overview"))
    )
    theme_cards = "".join(
        (
            '<section class="section-block">'
            f"<h3>{_escape(block.get('title'))}</h3>"
            '<div class="section-body">'
            f"<article class='card'><h4>最新现状</h4><ul>{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(block.get('recent')))}</ul></article>"
            f"<article class='card'><h4>去年同期经验</h4><ul>{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(block.get('historical')))}</ul></article>"
            "</div></section>"
        )
        for block in _safe_list(report.get("theme_blocks"))
    )
    gap_items = "".join(
        f"<li><strong>{_escape(item.get('site'))}</strong> · {_escape(item.get('reason'))}</li>"
        for item in _safe_list(report.get("gaps"))
    )
    return (
        '<section class="section-block"><h2>覆盖总览</h2><ul class="card-points">'
        f"{coverage_cards}</ul></section>"
        '<section class="section-block"><h2>快速结论</h2><ul class="card-points">'
        f"{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(report.get('quick_findings')))}</ul></section>"
        f"{theme_cards}"
        '<section class="section-block"><h2>缺口与失败</h2><ul class="card-points">'
        f"{gap_items}</ul></section>"
        '<section class="section-block"><h2>来源附录</h2><div id="sources-root"></div></section>'
    )
```

```javascript
// inside C:\Users\Lenovo\.codex\skills\travel-skill\assets\templates\render-guide.js
if (guide.research_report) {
  document.querySelector("#research-report-root").innerHTML = guide.research_report_html || "";
}
```

- [ ] **Step 4: Run the dossier-render test again**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_render_research_report.py' -v
```

Expected: PASS with the four required section checks succeeding.

- [ ] **Step 5: Run the full Phase 1 test suite**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' -m unittest discover 'C:\Users\Lenovo\.codex\skills\travel-skill\tests' -p 'test_*.py' -v
```

Expected: PASS across contract, task-planning, video-pipeline, persistence, coverage, and rendering tests.

- [ ] **Step 6: Run the report verifier against a generated guide root**

Run:

```powershell
& 'C:\Users\Lenovo\.conda\envs\stock-analyzer\python.exe' 'C:\Users\Lenovo\.codex\skills\travel-skill\scripts\verify_trip.py' --guide-root 'C:\Users\Lenovo\.codex\skills\travel-skill\travel-data\guides\sample-trip' --output 'C:\Users\Lenovo\.codex\skills\travel-skill\travel-data\guides\sample-trip\verify-report.json'
```

Expected: PASS once `research-report.html`, `notes/sources.md`, `notes/sources.html`, coverage sections, and dual-time-layer sections are present in the sample output.

## Self-Review

- Spec coverage: this plan covers the shared schema, heavy sampling, dual time layers, source-specific coverage, video fallback, layered persistence, coverage validation, and research-report rendering from the approved design doc.
- Placeholder scan: no deferred implementation markers remain.
- Type consistency: the plan uses `time_layer`, `sample_target`, `coverage_status`, `failure_reason`, `missing_fields`, `transcript_segments`, `visual_segments`, and `research_report` consistently across tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-15-travel-skill-research-enhancement.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
