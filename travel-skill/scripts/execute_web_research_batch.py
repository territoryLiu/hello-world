from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from aggregate_web_research_batch import _manifest_payload, aggregate_manifest
from finalize_web_research_run import finalize
from generate_review_packet import build_html, build_markdown


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(base_dir: Path, value: object) -> Path:
    path = Path(str(value or ""))
    if path.is_absolute():
        return path
    return base_dir / path


def _run_items(payload: dict) -> list[dict]:
    runs = payload.get("runs")
    if not isinstance(runs, list):
        return []
    return [run for run in runs if isinstance(run, dict)]


def _resolved_manifest(runs_payload: dict, runs_base_dir: Path) -> dict:
    manifest = _manifest_payload(runs_payload if isinstance(runs_payload, dict) else {})
    if not isinstance(manifest, dict):
        return {}
    resolved = dict(manifest)
    bundle_paths = manifest.get("bundle_paths")
    if isinstance(bundle_paths, list):
        resolved["bundle_paths"] = [
            str(_resolve_path(runs_base_dir, path))
            for path in bundle_paths
            if isinstance(path, str) and path.strip()
        ]
    runs = manifest.get("runs")
    if isinstance(runs, dict):
        resolved_runs = {}
        for run_id, item in runs.items():
            if not isinstance(item, dict):
                continue
            resolved_item = dict(item)
            if item.get("bundle_path"):
                resolved_item["bundle_path"] = str(_resolve_path(runs_base_dir, item.get("bundle_path")))
            if item.get("coverage_path"):
                resolved_item["coverage_path"] = str(_resolve_path(runs_base_dir, item.get("coverage_path")))
            resolved_runs[str(run_id)] = resolved_item
        resolved["runs"] = resolved_runs
    return resolved


def execute_batch(
    runs_payload: dict,
    runs_base_dir: Path,
    web_results_dir: Path,
    output_root: Path,
    batch_bundle_output: Path,
    batch_coverage_output: Path,
    review_output_dir: Path,
) -> dict:
    runs = _run_items(runs_payload)
    missing_results = []
    finalized = []

    output_root.mkdir(parents=True, exist_ok=True)
    web_results_dir.mkdir(parents=True, exist_ok=True)

    for run in runs:
        run_id = str(run.get("run_id") or "").strip()
        if not run_id:
            continue
        web_result_path = web_results_dir / f"{run_id}.json"
        if not web_result_path.exists():
            missing_results.append({"run_id": run_id, "web_result_path": str(web_result_path)})
            continue

        bundle_output = _resolve_path(runs_base_dir, run.get("expected_bundle_path"))
        coverage_output = _resolve_path(runs_base_dir, run.get("expected_coverage_path"))
        web_result = _load_json(web_result_path)
        bundle, coverage = finalize(run, web_result, output_root)

        bundle_output.parent.mkdir(parents=True, exist_ok=True)
        bundle_output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

        coverage_output.parent.mkdir(parents=True, exist_ok=True)
        coverage_output.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")

        finalized.append(
            {
                "run_id": run_id,
                "bundle_path": str(bundle_output),
                "coverage_path": str(coverage_output),
            }
        )

    if missing_results:
        raise FileNotFoundError(f"Missing web result files for {len(missing_results)} runs: {missing_results}")

    manifest = _resolved_manifest(runs_payload, runs_base_dir)
    batch_bundle, batch_coverage = aggregate_manifest(manifest)

    batch_bundle_output.parent.mkdir(parents=True, exist_ok=True)
    batch_bundle_output.write_text(json.dumps(batch_bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    batch_coverage_output.parent.mkdir(parents=True, exist_ok=True)
    batch_coverage_output.write_text(json.dumps(batch_coverage, ensure_ascii=False, indent=2), encoding="utf-8")

    review_output_dir.mkdir(parents=True, exist_ok=True)
    structured = batch_bundle.get("structured", {})
    review_payload = structured if isinstance(structured, dict) else {}
    (review_output_dir / "research-packet.md").write_text(build_markdown(review_payload), encoding="utf-8")
    (review_output_dir / "research-packet.html").write_text(build_html(review_payload), encoding="utf-8")

    return {
        "trip_slug": str(runs_payload.get("trip_slug") or ""),
        "batch_id": str(runs_payload.get("batch_id") or ""),
        "total_runs": len(runs),
        "finalized_runs": len(finalized),
        "missing_results": missing_results,
        "finalized": finalized,
        "batch_bundle_output": str(batch_bundle_output),
        "batch_coverage_output": str(batch_coverage_output),
        "review_output_dir": str(review_output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-file", required=True)
    parser.add_argument("--web-results-dir", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--batch-bundle-output", required=True)
    parser.add_argument("--batch-coverage-output", required=True)
    parser.add_argument("--review-output-dir", required=True)
    parser.add_argument("--execution-report-output", required=True)
    args = parser.parse_args()

    runs_file = Path(args.runs_file)
    runs_payload = _load_json(runs_file)
    report = execute_batch(
        runs_payload if isinstance(runs_payload, dict) else {},
        runs_file.parent,
        Path(args.web_results_dir),
        Path(args.output_root),
        Path(args.batch_bundle_output),
        Path(args.batch_coverage_output),
        Path(args.review_output_dir),
    )

    report_output = Path(args.execution_report_output)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
