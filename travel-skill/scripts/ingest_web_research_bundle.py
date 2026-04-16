from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from normalize_web_evidence import normalize_payload
from persist_research_knowledge import persist
from validate_site_coverage import validate


def ingest(payload: dict, output_root: Path) -> tuple[dict, dict]:
    bundle = normalize_payload(payload if isinstance(payload, dict) else {})
    coverage = validate(bundle)
    if bundle.get("trip_slug") and not coverage.get("trip_slug"):
        coverage["trip_slug"] = bundle["trip_slug"]
    persist(bundle, bundle, bundle, coverage, output_root)
    return bundle, coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--bundle-output", required=True)
    parser.add_argument("--coverage-output", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    bundle, coverage = ingest(payload if isinstance(payload, dict) else {}, output_root)

    bundle_output = Path(args.bundle_output)
    bundle_output.parent.mkdir(parents=True, exist_ok=True)
    bundle_output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    coverage_output = Path(args.coverage_output)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
