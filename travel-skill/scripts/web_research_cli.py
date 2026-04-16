from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_research_tasks import build_tasks
from build_web_access_batch_request import build_request
from build_web_research_runs import build_runs
from execute_web_research_batch import execute_batch
from materialize_web_access_batch_results import materialize
from normalize_request import normalize
from run_web_access_batch_smoke import run_smoke


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _cmd_build_runs(args) -> None:
    request_payload = _load_json(Path(args.request))
    normalized = normalize(request_payload if isinstance(request_payload, dict) else {})
    tasks = build_tasks(normalized)
    runs = build_runs(tasks)
    _write_json(Path(args.normalized_output), normalized)
    _write_json(Path(args.tasks_output), tasks)
    _write_json(Path(args.runs_output), runs)


def _cmd_export_request(args) -> None:
    runs_payload = _load_json(Path(args.runs_file))
    web_results_dir = Path(args.web_results_dir)
    request_payload = build_request(runs_payload if isinstance(runs_payload, dict) else {}, web_results_dir)
    _write_json(Path(args.output), request_payload)
    packets_dir = Path(args.packets_dir)
    packets_dir.mkdir(parents=True, exist_ok=True)
    for item in request_payload.get("requests", []):
        if not isinstance(item, dict):
            continue
        _write_json(packets_dir / f"{item['run_id']}.json", item)


def _cmd_materialize_results(args) -> None:
    payload = _load_json(Path(args.input))
    report = materialize(payload if isinstance(payload, dict) else {}, Path(args.web_results_dir))
    _write_json(Path(args.report_output), report)


def _cmd_execute_batch(args) -> None:
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
    _write_json(Path(args.execution_report_output), report)


def _cmd_smoke(args) -> None:
    run_smoke(Path(args.fixtures_root), Path(args.output_dir))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_runs_parser = subparsers.add_parser("build-runs")
    build_runs_parser.add_argument("--request", required=True)
    build_runs_parser.add_argument("--normalized-output", required=True)
    build_runs_parser.add_argument("--tasks-output", required=True)
    build_runs_parser.add_argument("--runs-output", required=True)
    build_runs_parser.set_defaults(func=_cmd_build_runs)

    export_request_parser = subparsers.add_parser("export-request")
    export_request_parser.add_argument("--runs-file", required=True)
    export_request_parser.add_argument("--output", required=True)
    export_request_parser.add_argument("--packets-dir", required=True)
    export_request_parser.add_argument("--web-results-dir", required=True)
    export_request_parser.set_defaults(func=_cmd_export_request)

    materialize_parser = subparsers.add_parser("materialize-results")
    materialize_parser.add_argument("--input", required=True)
    materialize_parser.add_argument("--web-results-dir", required=True)
    materialize_parser.add_argument("--report-output", required=True)
    materialize_parser.set_defaults(func=_cmd_materialize_results)

    execute_parser = subparsers.add_parser("execute-batch")
    execute_parser.add_argument("--runs-file", required=True)
    execute_parser.add_argument("--web-results-dir", required=True)
    execute_parser.add_argument("--output-root", required=True)
    execute_parser.add_argument("--batch-bundle-output", required=True)
    execute_parser.add_argument("--batch-coverage-output", required=True)
    execute_parser.add_argument("--review-output-dir", required=True)
    execute_parser.add_argument("--execution-report-output", required=True)
    execute_parser.set_defaults(func=_cmd_execute_batch)

    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--fixtures-root", required=True)
    smoke_parser.add_argument("--output-dir", required=True)
    smoke_parser.set_defaults(func=_cmd_smoke)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
