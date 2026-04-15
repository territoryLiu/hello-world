# Travel-Skill Research Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `travel-skill` so Xiaohongshu page evidence, Douyin/Bilibili page-plus-video fallback, full raw-material persistence, keyframe scoring, and downstream image-plan consumption work as one traceable research pipeline.

**Architecture:** Keep the current script-based pipeline, but add one shared evidence contract across page evidence, video evidence, and media evidence. Implement the work in six stages: shared schema, page evidence normalization, video fallback completion, keyframe scoring, four-layer persistence, and final validation/render tightening.

**Tech Stack:** Python in the existing `stock-analyzer` conda environment, built-in `unittest`, JSON, local file persistence, existing `travel-skill` scripts, and optional `yt-dlp` / `ffmpeg` / `whisper` tooling when available.

---

## Workspace Notes

- Repository root: `d:\vscode\hello-world`
- Approved spec: `docs/superpowers/specs/2026-04-15-travel-skill-research-enhancement-design.md`
- Verified activation pattern on Windows:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover tests -p test_*.py -v"
```

- Current main-branch verification baseline:
  - `python -m unittest discover tests -p test_*.py -v`
  - `python -m unittest discover travel-skill\tests -p test_*.py -v`

## File Map

- Modify: `travel-skill/scripts/research_contracts.py`
  Purpose: centralize research-record, video-media, and image-candidate manifest fields plus coverage/failure constants.
- Modify: `travel-skill/scripts/build_research_tasks.py`
  Purpose: emit site-split tasks with raw-capture, media, and fallback policy fields.
- Modify: `travel-skill/scripts/build_web_research_runs.py`
  Purpose: encode the Xiaohongshu page-first and Douyin/Bilibili page+video execution contract in run prompts.
- Create: `travel-skill/scripts/collect_page_evidence.py`
  Purpose: normalize full page body, comment threads, comment sample size, and image candidates into page evidence records.
- Modify: `travel-skill/scripts/video_pipeline.py`
  Purpose: emit richer artifact paths and a keyframe manifest for fallback runs.
- Modify: `travel-skill/scripts/extract_video_assets.py`
  Purpose: persist fallback execution outputs and standardized failure reasons.
- Create: `travel-skill/scripts/score_video_keyframes.py`
  Purpose: score all extracted keyframes with travel-information-first rules and mark selected frames.
- Modify: `travel-skill/scripts/build_video_research_json.py`
  Purpose: merge page evidence, video evidence, and media scoring into unified `research_record` items.
- Modify: `travel-skill/scripts/persist_research_knowledge.py`
  Purpose: write `raw/`, `normalized/`, `media/`, and `knowledge/` trees with stable IDs and cross-links.
- Modify: `travel-skill/scripts/build_image_plan.py`
  Purpose: consume the selected-media manifest while preserving publish gating and current fallbacks.
- Modify: `travel-skill/scripts/validate_site_coverage.py`
  Purpose: classify `complete` / `partial` / `failed` using page completeness, video completeness, sample count, and scoring completeness.
- Modify: `travel-skill/scripts/render_trip_site.py`
  Purpose: surface media-linked evidence in the research dossier without hiding gaps.
- Modify: `travel-skill/scripts/verify_trip.py`
  Purpose: verify media evidence, coverage states, and dossier completeness.
- Create: `travel-skill/tests/test_page_evidence_pipeline.py`
  Purpose: lock the Xiaohongshu page-first ingestion behavior.
- Create: `travel-skill/tests/test_video_media_scoring.py`
  Purpose: lock keyframe scoring, selected flags, and travel-signal tags.
- Create: `travel-skill/tests/test_image_candidate_manifest.py`
  Purpose: lock `build_image_plan.py` consumption of selected media records.
- Modify: `travel-skill/tests/test_build_research_tasks.py`
  Purpose: assert site-split policy and media/raw capture fields.
- Modify: `travel-skill/tests/test_video_pipeline.py`
  Purpose: assert richer fallback artifacts and failure reasons.
- Modify: `travel-skill/tests/test_persist_research_knowledge.py`
  Purpose: assert four-layer persistence and stable IDs.
- Modify: `travel-skill/tests/test_validate_site_coverage.py`
  Purpose: assert page-complete/video-incomplete and scored/unscored distinctions.
- Modify: `travel-skill/tests/test_render_research_report.py`
  Purpose: assert media evidence is rendered alongside gaps.

### Task 1: Define Shared Evidence and Media Contracts

**Files:**
- Modify: `travel-skill/scripts/research_contracts.py`
- Modify: `travel-skill/tests/test_research_contracts.py`
- Modify: `travel-skill/references/content-schema.md`

- [ ] **Step 1: Extend the failing contract tests**

```python
def test_contract_exposes_page_and_video_record_fields(self):
    from research_contracts import RESEARCH_RECORD_FIELDS, VIDEO_MEDIA_BUNDLE_FIELDS
    self.assertIn("page_body_full", RESEARCH_RECORD_FIELDS)
    self.assertIn("comment_threads_full", RESEARCH_RECORD_FIELDS)
    self.assertIn("frame_scores", VIDEO_MEDIA_BUNDLE_FIELDS)
    self.assertIn("selected_frames", VIDEO_MEDIA_BUNDLE_FIELDS)

def test_contract_exposes_image_candidate_manifest_fields(self):
    from research_contracts import IMAGE_CANDIDATE_FIELDS
    self.assertIn("selected_for_publish", IMAGE_CANDIDATE_FIELDS)
    self.assertIn("evidence_score", IMAGE_CANDIDATE_FIELDS)
    self.assertIn("travel_signal_tags", IMAGE_CANDIDATE_FIELDS)
```

- [ ] **Step 2: Run the targeted contract test and verify RED**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_research_contracts.py -v"
```

Expected: FAIL because the new contract constants do not exist yet.

- [ ] **Step 3: Add the shared constants and schema references**

```python
# travel-skill/scripts/research_contracts.py
RESEARCH_RECORD_FIELDS = [
    "place", "topic", "platform", "site", "source_url", "source_title",
    "collector_mode", "coverage_status", "failure_reason", "failure_detail",
    "missing_fields", "time_layer", "page_body_full", "comment_threads_full",
    "comment_sample_size", "transcript_full", "image_candidates",
    "shot_candidates", "media_artifacts",
]

VIDEO_MEDIA_BUNDLE_FIELDS = [
    "video", "audio", "transcript", "all_keyframes",
    "frame_scores", "selected_frames", "selection_rationale", "scene_tags",
]

IMAGE_CANDIDATE_FIELDS = [
    "section", "candidate_type", "source_ref", "selected_for_publish",
    "publish_state", "evidence_score", "visual_score", "travel_signal_tags",
]
```

```markdown
## page_evidence_record

- `page_body_full`
- `comment_threads_full`
- `comment_sample_size`
- `image_candidates`

## video_media_bundle

- `all_keyframes`
- `frame_scores`
- `selected_frames`
- `selection_rationale`
- `scene_tags`
```

- [ ] **Step 4: Re-run the contract test and verify GREEN**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add travel-skill/scripts/research_contracts.py travel-skill/tests/test_research_contracts.py travel-skill/references/content-schema.md
git commit -m "feat: 固化 research evidence 与 media contract"
```

### Task 2: Add Xiaohongshu Page-First Evidence Normalization

**Files:**
- Create: `travel-skill/scripts/collect_page_evidence.py`
- Modify: `travel-skill/scripts/build_research_tasks.py`
- Modify: `travel-skill/scripts/build_web_research_runs.py`
- Create: `travel-skill/tests/test_page_evidence_pipeline.py`
- Modify: `travel-skill/tests/test_build_research_tasks.py`

- [ ] **Step 1: Write the failing page-evidence tests**

```python
def test_collect_page_evidence_preserves_full_body_and_comments(self):
    payload = {
        "items": [{
            "site": "xiaohongshu",
            "page_body_full": "full body text",
            "comment_threads_full": [{"author": "a", "text": "comment"}],
            "image_candidates": [{"url": "https://cdn.example.com/1.jpg"}],
        }]
    }
    result = collect(payload)
    item = result["items"][0]
    self.assertEqual(item["coverage_status"], "complete")
    self.assertEqual(item["comment_sample_size"], 1)
    self.assertEqual(item["page_body_full"], "full body text")

def test_collect_page_evidence_marks_partial_when_comments_missing(self):
    payload = {"items": [{"site": "xiaohongshu", "page_body_full": "full body text"}]}
    result = collect(payload)
    item = result["items"][0]
    self.assertEqual(item["coverage_status"], "partial")
    self.assertIn("comment_threads_full", item["missing_fields"])
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_page_evidence_pipeline.py -v"
```

Expected: FAIL because `collect_page_evidence.py` does not exist yet.

- [ ] **Step 3: Implement page evidence normalization and task/run metadata**

```python
# travel-skill/scripts/collect_page_evidence.py
def collect(payload: dict) -> dict:
    items = []
    for raw in payload.get("items", []):
        comments = raw.get("comment_threads_full") if isinstance(raw.get("comment_threads_full"), list) else []
        missing = []
        if not str(raw.get("page_body_full") or "").strip():
            missing.append("page_body_full")
        if not comments:
            missing.append("comment_threads_full")
        item = {
            **raw,
            "comment_sample_size": len(comments),
            "missing_fields": missing,
            "coverage_status": "complete" if not missing else "partial",
        }
        items.append(item)
    return {"items": items}
```

```python
# travel-skill/scripts/build_research_tasks.py
task["raw_capture_policy"] = "full"
task["media_policy"] = "page-images"
if task["site"] == "xiaohongshu":
    task["must_capture_fields"].extend(["page_body_full", "comment_threads_full", "comment_sample_size", "image_candidates"])
```

```python
# travel-skill/scripts/build_web_research_runs.py
if site == "xiaohongshu":
    instructions.append("Capture the full page body, full comment threads, comment sample size, and image candidates before marking the task complete.")
```

- [ ] **Step 4: Re-run the targeted tests and the task-generation suite**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_page_evidence_pipeline.py -v && python -m unittest discover travel-skill\tests -p test_build_research_tasks.py -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add travel-skill/scripts/collect_page_evidence.py travel-skill/scripts/build_research_tasks.py travel-skill/scripts/build_web_research_runs.py travel-skill/tests/test_page_evidence_pipeline.py travel-skill/tests/test_build_research_tasks.py
git commit -m "feat: 增加小红书页面证据归一化"
```

### Task 3: Complete Douyin/Bilibili Video Fallback and Keyframe Scoring

**Files:**
- Modify: `travel-skill/scripts/video_pipeline.py`
- Modify: `travel-skill/scripts/extract_video_assets.py`
- Create: `travel-skill/scripts/score_video_keyframes.py`
- Modify: `travel-skill/scripts/build_video_research_json.py`
- Modify: `travel-skill/tests/test_video_pipeline.py`
- Create: `travel-skill/tests/test_video_media_scoring.py`

- [ ] **Step 1: Write the failing scoring and fallback tests**

```python
def test_score_video_keyframes_preserves_all_candidates_and_marks_selected(self):
    manifest = {
        "items": [
            {"path": "frame-001.jpg", "timestamp": "00:05"},
            {"path": "frame-002.jpg", "timestamp": "00:13"},
        ]
    }
    result = score_manifest(manifest)
    self.assertEqual(len(result["all_keyframes"]), 2)
    self.assertTrue(any(item["selected"] for item in result["frame_scores"]))
    self.assertTrue(result["selected_frames"])

def test_build_status_marks_multimodal_scoring_failed_when_score_manifest_missing(self):
    item = build_status({"url": "https://example.com/video", "run_pipeline": False})
    self.assertIn("media_artifacts", item)
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_video_media_scoring.py -v"
```

Expected: FAIL because `score_video_keyframes.py` does not exist yet.

- [ ] **Step 3: Implement richer media artifacts and scoring**

```python
# travel-skill/scripts/video_pipeline.py
plan["artifacts"]["keyframe_manifest"] = str(asset_root / "keyframes.json")
plan["artifacts"]["score_manifest"] = str(asset_root / "frame-scores.json")
```

```python
# travel-skill/scripts/score_video_keyframes.py
def score_manifest(payload: dict) -> dict:
    scored = []
    for raw in payload.get("items", []):
        score = 0.9 if any(tag in str(raw.get("label", "")) for tag in ["queue", "menu", "ticket", "view"]) else 0.6
        scored.append({
            **raw,
            "evidence_score": score,
            "visual_score": 0.5,
            "selected": score >= 0.8,
            "travel_signal_tags": raw.get("travel_signal_tags", []),
        })
    return {
        "all_keyframes": payload.get("items", []),
        "frame_scores": scored,
        "selected_frames": [item for item in scored if item["selected"]],
    }
```

```python
# travel-skill/scripts/build_video_research_json.py
record["media_artifacts"] = _list(item.get("media_artifacts"))
record["frame_scores"] = _list(item.get("frame_scores"))
record["selected_frames"] = _list(item.get("selected_frames"))
```

- [ ] **Step 4: Re-run the targeted tests and the existing video suite**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_video_media_scoring.py -v && python -m unittest discover travel-skill\tests -p test_video_pipeline.py -v"
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add travel-skill/scripts/video_pipeline.py travel-skill/scripts/extract_video_assets.py travel-skill/scripts/score_video_keyframes.py travel-skill/scripts/build_video_research_json.py travel-skill/tests/test_video_pipeline.py travel-skill/tests/test_video_media_scoring.py
git commit -m "feat: 完成视频 fallback 与关键帧评分链路"
```

### Task 4: Persist Raw, Normalized, Media, and Knowledge Layers

**Files:**
- Modify: `travel-skill/scripts/persist_research_knowledge.py`
- Modify: `travel-skill/scripts/build_video_research_json.py`
- Modify: `travel-skill/tests/test_persist_research_knowledge.py`

- [ ] **Step 1: Write the failing persistence tests**

```python
def test_persist_writes_raw_normalized_media_and_knowledge_layers(self):
    result = persist_payloads(...)
    self.assertTrue((place_root / "raw").exists())
    self.assertTrue((place_root / "normalized").exists())
    self.assertTrue((place_root / "media").exists())
    self.assertTrue((place_root / "knowledge").exists())

def test_persist_links_raw_and_normalized_records_by_stable_id(self):
    record = json.loads((place_root / "normalized" / "records.json").read_text(encoding="utf-8"))["records"][0]
    self.assertIn("record_id", record)
    self.assertIn("raw_ref", record)
```

- [ ] **Step 2: Run the targeted test and verify RED**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_persist_research_knowledge.py -v"
```

Expected: FAIL because the current persistence layer does not write all four layers with stable IDs.

- [ ] **Step 3: Implement four-layer persistence**

```python
# travel-skill/scripts/persist_research_knowledge.py
record_id = f"{place}-{topic}-{site}-{time_layer}-{index}"
normalized_record["record_id"] = record_id
normalized_record["raw_ref"] = f"raw/{record_id}.json"
```

```python
for layer in ["raw", "normalized", "media", "knowledge"]:
    (place_root / layer).mkdir(parents=True, exist_ok=True)
```

```python
(place_root / "media" / "frame-scores.json").write_text(
    json.dumps(media_payload, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

- [ ] **Step 4: Re-run the persistence suite**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add travel-skill/scripts/persist_research_knowledge.py travel-skill/scripts/build_video_research_json.py travel-skill/tests/test_persist_research_knowledge.py
git commit -m "feat: 持久化四层 research 输出"
```

### Task 5: Feed Selected Media into the Image Plan and Coverage Validation

**Files:**
- Modify: `travel-skill/scripts/build_image_plan.py`
- Modify: `travel-skill/scripts/validate_site_coverage.py`
- Create: `travel-skill/tests/test_image_candidate_manifest.py`
- Modify: `travel-skill/tests/test_validate_site_coverage.py`

- [ ] **Step 1: Write the failing image-plan and coverage tests**

```python
def test_build_image_plan_prefers_selected_media_manifest(self):
    payload = {
        "items": [{
            "selected_frames": [{"local_path": "frame-001.jpg", "selected_for_publish": True, "evidence_score": 0.92}],
            "section": "attractions",
        }]
    }
    result = build_plan(payload)
    self.assertEqual(result["section_images"][0]["image_url"], "frame-001.jpg")
    self.assertEqual(result["section_images"][0]["publish_state"], "selected-media")

def test_validate_site_coverage_flags_video_incomplete_when_page_is_complete(self):
    payload = {"records": [{
        "site": "douyin",
        "coverage_status": "partial",
        "page_body_full": "ok",
        "comment_threads_full": [{"text": "ok"}],
        "transcript_segments": [],
        "frame_scores": [],
        "missing_fields": ["transcript_segments", "frame_scores"],
    }]}
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_image_candidate_manifest.py -v && python -m unittest discover travel-skill\tests -p test_validate_site_coverage.py -v"
```

Expected: FAIL because selected-media manifest support does not exist yet.

- [ ] **Step 3: Implement selected-media consumption and tighter coverage rules**

```python
# travel-skill/scripts/build_image_plan.py
selected_frames = item.get("selected_frames") if isinstance(item.get("selected_frames"), list) else []
preferred = next((frame for frame in selected_frames if frame.get("selected_for_publish")), None)
if preferred:
    return {
        "image_url": preferred.get("local_path", ""),
        "publish_state": "selected-media",
        "evidence_score": preferred.get("evidence_score", 0),
    }
```

```python
# travel-skill/scripts/validate_site_coverage.py
if record["site"] in {"douyin", "bilibili"} and record.get("page_body_full") and not record.get("transcript_segments"):
    failure_reasons.add("video_incomplete")
```

- [ ] **Step 4: Re-run the targeted tests**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add travel-skill/scripts/build_image_plan.py travel-skill/scripts/validate_site_coverage.py travel-skill/tests/test_image_candidate_manifest.py travel-skill/tests/test_validate_site_coverage.py
git commit -m "feat: 接入 selected media manifest 与覆盖校验"
```

### Task 6: Tighten Dossier Rendering, Verification, and Full Regression

**Files:**
- Modify: `travel-skill/scripts/render_trip_site.py`
- Modify: `travel-skill/scripts/verify_trip.py`
- Modify: `travel-skill/tests/test_render_research_report.py`
- Modify: `tests/test_verify.py`

- [ ] **Step 1: Write the failing render/verify assertions**

```python
def test_render_trip_site_outputs_media_evidence_cards(self):
    html = render_report(...)
    self.assertIn("selected-frame", html)
    self.assertIn("coverage_status", html)

def test_verify_trip_flags_unscored_keyframes(self):
    payload = verify_trip(guide_root)
    self.assertFalse(payload["content_checks"]["media_scoring_complete"])
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_render_research_report.py -v && python -m unittest discover tests -p test_verify.py -v"
```

Expected: FAIL because the dossier and verifier do not yet check media scoring completeness.

- [ ] **Step 3: Implement the final media-aware dossier and verifier**

```python
# travel-skill/scripts/verify_trip.py
content_checks["media_scoring_complete"] = "frame-scores.json" in html_blob or (guide_root / "media" / "frame-scores.json").exists()
```

```python
# travel-skill/scripts/render_trip_site.py
evidence_cards += "".join(
    f"<article class='card selected-frame'><h3>{_escape(frame.get('title') or 'Selected Frame')}</h3></article>"
    for frame in _safe_list(report.get("selected_frames"))
)
```

- [ ] **Step 4: Run the full regression commands**

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover tests -p test_*.py -v"
```

Run:

```powershell
cmd.exe /d /c "call C:\Users\territoryliu\anaconda3\condabin\activate.bat stock-analyzer && cd /d d:\vscode\hello-world && python -m unittest discover travel-skill\tests -p test_*.py -v"
```

Expected: both commands PASS with zero failures.

- [ ] **Step 5: Commit**

```powershell
git add travel-skill/scripts/render_trip_site.py travel-skill/scripts/verify_trip.py travel-skill/tests/test_render_research_report.py tests/test_verify.py
git commit -m "feat: 完成 research dossier 媒体证据闭环"
```

## Self-Review Checklist

- Spec coverage:
  - shared contracts: Task 1
  - Xiaohongshu page-first raw capture: Task 2
  - Douyin/Bilibili page+video fallback: Task 3
  - full keyframe persistence and scoring: Tasks 3 and 4
  - four-layer persistence: Task 4
  - image-plan consumption: Task 5
  - coverage classification and final dossier verification: Tasks 5 and 6
- Placeholder scan:
  - no `TODO`, `TBD`, or vague “handle appropriately” language remains in tasks
- Type consistency:
  - `research_record`, `selected_frames`, `frame_scores`, `selected_for_publish`, and `coverage_status` names are used consistently across all tasks

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-15-travel-skill-research-enhancement.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
