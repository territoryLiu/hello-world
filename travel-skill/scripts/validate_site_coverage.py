from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import SITE_COVERAGE_TARGETS as REQUIRED_SITE_MATRIX


def validate(payload: dict) -> dict:
    facts = payload.get("facts", [])
    seen_by_topic = {}
    for fact in facts if isinstance(facts, list) else []:
        if not isinstance(fact, dict):
            continue
        topic = str(fact.get("topic", ""))
        site = str(fact.get("site", ""))
        if not topic:
            continue
        seen_by_topic.setdefault(topic, set())
        if site:
            seen_by_topic[topic].add(site)

    by_topic = {}
    has_gaps = False
    for topic, required_sites in REQUIRED_SITE_MATRIX.items():
        seen = sorted(seen_by_topic.get(topic, set()))
        missing = [site for site in required_sites if site not in seen]
        if missing:
            has_gaps = True
        by_topic[topic] = {
            "seen_sites": seen,
            "missing_required_sites": missing,
        }
    return {"has_gaps": has_gaps, "by_topic": by_topic}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = validate(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
