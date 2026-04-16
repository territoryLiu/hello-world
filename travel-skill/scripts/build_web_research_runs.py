from pathlib import Path
import argparse
import json
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import SITE_COVERAGE_TARGETS


def _safe_segment(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "task"
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-_") or "task"


def _batch_id(trip_slug: object) -> str:
    return f"{_safe_segment(trip_slug)}-web-research"


def _run_id(trip_slug: object, index: int, task: dict) -> str:
    parts = [
        _safe_segment(trip_slug),
        f"{index:03d}",
        _safe_segment(task.get("place")),
        _safe_segment(task.get("topic")),
        _safe_segment(task.get("site")),
        _safe_segment(task.get("time_layer")),
    ]
    return "-".join(parts)


def _run_output_dir(trip_slug: object, run_id: str) -> Path:
    return Path("travel-data") / "trips" / str(trip_slug or "") / "research" / "web-runs" / run_id


def _capture_contract(task: dict) -> str:
    site = str(task.get("site") or "").lower()
    method = str(task.get("collection_method") or "travel-skill")
    time_layer = str(task.get("time_layer") or "recent")
    sample_target = int(task.get("sample_target") or 1)
    raw_capture_policy = str(task.get("raw_capture_policy") or "summary-only")
    media_policy = str(task.get("media_policy") or "none")
    normalized_schema = str(task.get("normalized_schema") or "generic-source-v1")
    required_fields = ", ".join(task.get("must_capture_fields", []))
    instructions = [
        f"time_layer={time_layer}.",
        f"sample_target={sample_target}.",
        f"raw_capture_policy={raw_capture_policy}.",
        f"media_policy={media_policy}.",
        f"normalized_schema={normalized_schema}.",
        "Open the concrete site result instead of citing generic platform summaries.",
        "Do page extraction first, capture the page body summary, and extract structured facts.",
        f"Record fields: {required_fields}.",
        "Record missing_fields when any required field is absent.",
        "Use retry_same_mode before degrade_or_fallback.",
    ]
    if site in {"xiaohongshu", "douyin", "bilibili"}:
        instructions.append("Read the comments section and capture comments, comment status, and sample size.")
    if site == "xiaohongshu":
        instructions.append("Capture the full page body, full comment threads, comment sample size, and image candidates before marking the task complete.")
    if site in {"douyin", "bilibili"}:
        instructions.append("For video pages, trigger video fallback when needed and capture transcript segments, timeline, visual segments, and screenshot candidates.")
    if task.get("topic") == "long_distance_transport" and site == "official":
        instructions.append(
            "If the target travel date is not yet on sale, collect the latest searchable schedule, keep the checked date context, and mark the fallback strategy."
        )
    instructions.append(
        f"If any required field cannot be collected with {method}, set coverage_status to partial or failed, record failure_reason and failure_detail, and do not assume coverage."
    )
    return " ".join(instructions)


def build_runs(payload: dict) -> dict:
    runs = []
    tasks = payload.get("tasks", [])
    trip_slug = payload.get("trip_slug", "")
    batch_id = _batch_id(trip_slug)
    batch_runs: dict[str, dict] = {}

    for index, task in enumerate(tasks if isinstance(tasks, list) else [], start=1):
        if not isinstance(task, dict):
            continue
        run_id = _run_id(trip_slug, index, task)
        run_output_dir = _run_output_dir(trip_slug, run_id)
        expected_bundle_path = (run_output_dir / "bundle.json").as_posix()
        expected_coverage_path = (run_output_dir / "coverage.json").as_posix()
        runs.append(
            {
                "skill": "travel-skill",
                "run_id": run_id,
                "batch_id": batch_id,
                "result_schema": "travel-skill-web-evidence-v1",
                "postprocess_script": "travel-skill/scripts/finalize_web_research_run.py",
                "expected_bundle_path": expected_bundle_path,
                "expected_coverage_path": expected_coverage_path,
                "task": task,
                "prompt": (
                    "Use the standalone web-access skill to collect travel evidence for this task. "
                    f"Search site={task.get('site')} with query={task.get('site_query')}. "
                    "Do not use any repo-local copy under .codex/skills/travel/web-access. "
                    "Use page extraction first and trigger video fallback when the page is insufficient. "
                    f"{_capture_contract(task)}"
                ),
            }
        )
        batch_runs[run_id] = {
            "bundle_path": expected_bundle_path,
            "coverage_path": expected_coverage_path,
            "site": str(task.get("site") or ""),
            "topic": str(task.get("topic") or ""),
            "time_layer": str(task.get("time_layer") or ""),
        }

    batch_manifest = {
        "trip_slug": trip_slug,
        "batch_id": batch_id,
        "aggregator_script": "travel-skill/scripts/aggregate_web_research_batch.py",
        "bundle_paths": [run["expected_bundle_path"] for run in runs],
        "runs": batch_runs,
    }
    return {
        "runner": "travel-skill",
        "trip_slug": trip_slug,
        "batch_id": batch_id,
        "batch_manifest": batch_manifest,
        "site_coverage_targets": SITE_COVERAGE_TARGETS,
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output = build_runs(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
