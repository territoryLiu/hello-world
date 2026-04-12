from pathlib import Path
import argparse
import json


SITE_COVERAGE_TARGETS = {
    "food": ["meituan", "dianping", "xiaohongshu"],
    "attractions": ["official", "xiaohongshu", "douyin", "bilibili"],
    "risks": ["xiaohongshu", "douyin", "bilibili"],
}


def build_runs(payload: dict) -> dict:
    runs = []
    tasks = payload.get("tasks", [])
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        runs.append(
            {
                "skill": "web-access",
                "task": task,
                "prompt": (
                    "Use web-access to collect travel evidence for this task. "
                    f"Search site={task.get('site')} with query={task.get('site_query')} "
                    f"and capture {', '.join(task.get('must_capture_fields', []))}."
                ),
            }
        )
    return {
        "runner": "web-access",
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
