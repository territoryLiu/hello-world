from pathlib import Path
import argparse
import json


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _run_items(payload: dict) -> list[dict]:
    runs = payload.get("runs")
    if not isinstance(runs, list):
        return []
    return [run for run in runs if isinstance(run, dict)]


def build_request(runs_payload: dict, web_results_dir: Path) -> dict:
    requests = []
    for run in _run_items(runs_payload):
        run_id = str(run.get("run_id") or "").strip()
        if not run_id:
            continue
        requests.append(
            {
                "run_id": run_id,
                "batch_id": str(run.get("batch_id") or runs_payload.get("batch_id") or ""),
                "prompt": str(run.get("prompt") or ""),
                "task": run.get("task") if isinstance(run.get("task"), dict) else {},
                "skill": str(run.get("skill") or "travel-skill"),
                "result_schema": str(run.get("result_schema") or ""),
                "response_path": str((web_results_dir / f"{run_id}.json").as_posix()),
            }
        )
    return {
        "trip_slug": str(runs_payload.get("trip_slug") or ""),
        "batch_id": str(runs_payload.get("batch_id") or ""),
        "requests": requests,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--packets-dir", required=True)
    parser.add_argument("--web-results-dir", required=True)
    args = parser.parse_args()

    runs_payload = _load_json(Path(args.runs_file))
    web_results_dir = Path(args.web_results_dir)
    request_payload = build_request(runs_payload if isinstance(runs_payload, dict) else {}, web_results_dir)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    packets_dir = Path(args.packets_dir)
    packets_dir.mkdir(parents=True, exist_ok=True)
    for item in request_payload["requests"]:
        (packets_dir / f"{item['run_id']}.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
