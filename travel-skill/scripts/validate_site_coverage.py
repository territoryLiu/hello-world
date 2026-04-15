from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import SITE_COVERAGE_TARGETS as REQUIRED_SITE_MATRIX
from research_contracts import HEAVY_SAMPLE_TARGETS


def validate(payload: dict) -> dict:
    records = payload.get("records")
    if not isinstance(records, list):
        records = payload.get("facts", [])
    by_topic = {}
    by_site = {}
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        topic = str(record.get("topic", ""))
        site = str(record.get("site", ""))
        if not topic:
            continue
        topic_bucket = by_topic.setdefault(topic, {"seen_sites": set(), "missing_required_sites": []})
        if site:
            topic_bucket["seen_sites"].add(site)
        site_bucket = by_site.setdefault(
            site,
            {
                "sample_target": HEAVY_SAMPLE_TARGETS.get(site, 1),
                "actual_sample_count": 0,
                "failure_reasons": set(),
                "missing_required_fields": set(),
            },
        )
        site_bucket["actual_sample_count"] += 1
        for missing in record.get("missing_fields", []) if isinstance(record.get("missing_fields"), list) else []:
            site_bucket["missing_required_fields"].add(str(missing))
        if record.get("failure_reason"):
            site_bucket["failure_reasons"].add(str(record["failure_reason"]))

    for topic, required_sites in REQUIRED_SITE_MATRIX.items():
        topic_bucket = by_topic.setdefault(topic, {"seen_sites": set(), "missing_required_sites": []})
        seen = sorted(topic_bucket["seen_sites"])
        missing = [site for site in required_sites if site not in topic_bucket["seen_sites"]]
        topic_bucket["seen_sites"] = seen
        topic_bucket["missing_required_sites"] = missing

    for site, bucket in by_site.items():
        if bucket["actual_sample_count"] < bucket["sample_target"]:
            bucket["failure_reasons"].add("insufficient_sample_size")
        bucket["coverage_status"] = (
            "complete"
            if bucket["actual_sample_count"] >= bucket["sample_target"] and not bucket["missing_required_fields"]
            else "partial"
        )
        bucket["failure_reasons"] = sorted(bucket["failure_reasons"])
        bucket["missing_required_fields"] = sorted(bucket["missing_required_fields"])

    has_gaps = any(bucket["coverage_status"] != "complete" for bucket in by_site.values())
    has_gaps = has_gaps or any(topic["missing_required_sites"] for topic in by_topic.values())
    return {"has_gaps": has_gaps, "by_topic": by_topic, "by_site": by_site}


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
