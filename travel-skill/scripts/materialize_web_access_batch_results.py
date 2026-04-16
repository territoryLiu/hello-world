from pathlib import Path
import argparse
import json


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def materialize(payload: dict, web_results_dir: Path) -> dict:
    web_results_dir.mkdir(parents=True, exist_ok=True)
    results = payload.get("results")
    saved = []
    skipped = []
    for item in results if isinstance(results, list) else []:
        if not isinstance(item, dict):
            continue
        run_id = str(item.get("run_id") or "").strip()
        result = item.get("result")
        if not run_id or not isinstance(result, (dict, list)):
            skipped.append({"item": item})
            continue
        output_path = web_results_dir / f"{run_id}.json"
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        saved.append({"run_id": run_id, "path": str(output_path)})
    return {
        "batch_id": str(payload.get("batch_id") or ""),
        "materialized_results": len(saved),
        "saved_results": saved,
        "skipped_results": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--web-results-dir", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args()

    payload = _load_json(Path(args.input))
    report = materialize(payload if isinstance(payload, dict) else {}, Path(args.web_results_dir))

    report_output = Path(args.report_output)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
