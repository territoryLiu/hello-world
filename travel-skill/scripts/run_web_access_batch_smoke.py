from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_web_access_batch_request import build_request
from execute_web_research_batch import execute_batch
from materialize_web_access_batch_results import materialize


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    fixtures_root = Path(args.fixtures_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    runs_payload = _load_json(fixtures_root / "runs.json")
    batch_results_payload = _load_json(fixtures_root / "web-access-batch-results.json")

    runs_file = output_dir / "runs.json"
    runs_file.write_text(json.dumps(runs_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    web_results_dir = output_dir / "web-results"
    packets_dir = output_dir / "web-access-packets"
    request_payload = build_request(runs_payload if isinstance(runs_payload, dict) else {}, web_results_dir)
    (output_dir / "web-access-batch.json").write_text(
        json.dumps(request_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    packets_dir.mkdir(parents=True, exist_ok=True)
    for item in request_payload["requests"]:
        (packets_dir / f"{item['run_id']}.json").write_text(
            json.dumps(item, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    materialize_report = materialize(
        batch_results_payload if isinstance(batch_results_payload, dict) else {},
        web_results_dir,
    )
    (output_dir / "web-results-materialize-report.json").write_text(
        json.dumps(materialize_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    execution_report = execute_batch(
        runs_payload if isinstance(runs_payload, dict) else {},
        runs_file.parent,
        web_results_dir,
        output_dir / "travel-data",
        output_dir / "batch-bundle.json",
        output_dir / "batch-coverage.json",
        output_dir / "review-packet",
    )
    (output_dir / "execution-report.json").write_text(
        json.dumps(execution_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
