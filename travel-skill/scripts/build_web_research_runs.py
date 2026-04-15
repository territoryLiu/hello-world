from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import SITE_COVERAGE_TARGETS


def _capture_contract(task: dict) -> str:
    site = str(task.get("site") or "").lower()
    method = str(task.get("collection_method") or "travel-skill")
    time_layer = str(task.get("time_layer") or "recent")
    sample_target = int(task.get("sample_target") or 1)
    required_fields = ", ".join(task.get("must_capture_fields", []))
    instructions = [
        f"time_layer={time_layer}.",
        f"sample_target={sample_target}.",
        "Open the concrete site result instead of citing generic platform summaries.",
        "Do page extraction first, capture the page body summary, and extract structured facts.",
        f"Record fields: {required_fields}.",
        "Record missing_fields when any required field is absent.",
        "Use retry_same_mode before degrade_or_fallback.",
    ]
    if site in {"xiaohongshu", "douyin", "bilibili"}:
        instructions.append("Read the comments section and capture comments, comment status, and sample size.")
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
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        runs.append(
            {
                "skill": "travel-skill",
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
    return {
        "runner": "travel-skill",
        "trip_slug": payload.get("trip_slug", ""),
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
