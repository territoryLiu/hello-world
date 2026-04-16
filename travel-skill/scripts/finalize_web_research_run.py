from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from ingest_web_research_bundle import ingest


def _items(payload) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "entries"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _with_task_context(task: dict, item: dict) -> dict:
    merged = dict(item)
    for key in [
        "trip_slug",
        "place",
        "topic",
        "platform",
        "site",
        "time_layer",
        "collection_method",
        "raw_capture_policy",
        "media_policy",
        "normalized_schema",
        "sample_target",
        "retry_policy",
        "fallback_policy",
        "evidence_level",
    ]:
        if not merged.get(key) and task.get(key) is not None:
            merged[key] = task.get(key)
    return merged


def finalize(run_payload: dict, web_result, output_root: Path) -> tuple[dict, dict]:
    task = run_payload.get("task") if isinstance(run_payload.get("task"), dict) else {}
    trip_slug = str(task.get("trip_slug") or run_payload.get("trip_slug") or "")
    payload = {
        "trip_slug": trip_slug,
        "items": [_with_task_context(task, item) for item in _items(web_result)],
    }
    return ingest(payload, output_root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-file", required=True)
    parser.add_argument("--web-result", required=True)
    parser.add_argument("--bundle-output", required=True)
    parser.add_argument("--coverage-output", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()

    run_payload = json.loads(Path(args.run_file).read_text(encoding="utf-8"))
    web_result = json.loads(Path(args.web_result).read_text(encoding="utf-8"))
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    bundle, coverage = finalize(run_payload if isinstance(run_payload, dict) else {}, web_result, output_root)

    bundle_output = Path(args.bundle_output)
    bundle_output.parent.mkdir(parents=True, exist_ok=True)
    bundle_output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    coverage_output = Path(args.coverage_output)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
