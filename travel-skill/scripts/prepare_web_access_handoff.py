from pathlib import Path
import argparse
import json

from build_web_access_batch_request import build_request


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare_handoff(runs_payload: dict, output_dir: Path, web_results_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    request_payload = build_request(runs_payload if isinstance(runs_payload, dict) else {}, web_results_dir)
    _write_json(output_dir / "web-access-batch.json", request_payload)
    _write_json(output_dir / "runs.json", runs_payload)

    packets_dir = output_dir / "web-access-packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    for item in request_payload.get("requests", []):
        if not isinstance(item, dict):
            continue
        _write_json(packets_dir / f"{item['run_id']}.json", item)

    expected = {
        "trip_slug": str(runs_payload.get("trip_slug") or ""),
        "batch_id": str(runs_payload.get("batch_id") or ""),
        "expected_runs": len(request_payload.get("requests", [])),
        "run_ids": [item["run_id"] for item in request_payload.get("requests", []) if isinstance(item, dict)],
        "response_paths": [item["response_path"] for item in request_payload.get("requests", []) if isinstance(item, dict)],
        "missing_results": [],
    }
    _write_json(output_dir / "web-access-expected-results.json", expected)

    lines = [
        "# Web Access Handoff",
        "",
        f"- trip_slug: `{expected['trip_slug']}`",
        f"- batch_id: `{expected['batch_id']}`",
        f"- expected_runs: `{expected['expected_runs']}`",
        "",
        "## Run IDs",
        "",
    ]
    for run_id in expected["run_ids"]:
        lines.append(f"- `{run_id}`")
    lines.extend(
        [
            "",
            "## Return Contract",
            "",
            "- Return one batch results JSON file with `batch_id` and `results`.",
            "- Each result item must contain `run_id` and `result`.",
            "- `result` should match the raw web-access return payload for that run.",
        ]
    )
    (output_dir / "handoff-readme.md").write_text("\n".join(lines), encoding="utf-8")
    return expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--web-results-dir", required=True)
    args = parser.parse_args()

    runs_payload = _load_json(Path(args.runs_file))
    prepare_handoff(
        runs_payload if isinstance(runs_payload, dict) else {},
        Path(args.output_dir),
        Path(args.web_results_dir),
    )


if __name__ == "__main__":
    main()
