from pathlib import Path
import argparse
import json


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_run_ids(runs_payload: dict) -> list[str]:
    runs = runs_payload.get("runs")
    if not isinstance(runs, list):
        return []
    return [str(item.get("run_id") or "").strip() for item in runs if isinstance(item, dict) and str(item.get("run_id") or "").strip()]


def validate_batch_results(runs_payload: dict, batch_results_payload: dict) -> dict:
    expected = _expected_run_ids(runs_payload if isinstance(runs_payload, dict) else {})
    seen = []
    duplicates = []
    for item in batch_results_payload.get("results", []) if isinstance(batch_results_payload.get("results"), list) else []:
        if not isinstance(item, dict):
            continue
        run_id = str(item.get("run_id") or "").strip()
        if not run_id:
            continue
        if run_id in seen and run_id not in duplicates:
            duplicates.append(run_id)
        seen.append(run_id)
    missing = sorted(run_id for run_id in expected if run_id not in seen)
    extra = sorted(run_id for run_id in set(seen) if run_id not in expected)
    return {
        "batch_id": str(batch_results_payload.get("batch_id") or runs_payload.get("batch_id") or ""),
        "expected_run_ids": expected,
        "received_run_ids": seen,
        "missing_run_ids": missing,
        "extra_run_ids": extra,
        "duplicate_run_ids": sorted(duplicates),
        "can_materialize": not missing and not extra and not duplicates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-file", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--report-output", required=True)
    args = parser.parse_args()

    runs_payload = _load_json(Path(args.runs_file))
    batch_results_payload = _load_json(Path(args.input))
    report = validate_batch_results(
        runs_payload if isinstance(runs_payload, dict) else {},
        batch_results_payload if isinstance(batch_results_payload, dict) else {},
    )
    output = Path(args.report_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
