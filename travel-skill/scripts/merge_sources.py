from datetime import datetime
from pathlib import Path
import argparse
import json

PASSTHROUGH_FIELDS = [
    "author",
    "publish_time",
    "published_at",
    "summary",
    "page_body_full",
    "comment_threads_full",
    "comment_sample_size",
    "comment_highlights",
    "image_candidates",
    "transcript_segments",
    "visual_segments",
    "timeline",
    "shot_candidates",
    "selected_frames",
    "frame_scores",
    "shop_name",
    "address",
    "per_capita_range",
    "recommended_dishes",
    "queue_pattern",
    "review_themes",
    "pitfalls",
    "coverage_status",
    "failure_reason",
    "failure_detail",
    "missing_fields",
    "time_layer",
]


def _safe_json_key(value) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except TypeError:
        return json.dumps(str(value), ensure_ascii=False)


def _checked_at_rank(value: str) -> tuple[int, str]:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text)
        return (1, parsed.isoformat())
    except ValueError:
        return (0, text)


def _prefer_latest_non_empty(records: list[dict], field: str) -> str:
    for record in records:
        value = record.get(field)
        if str(value or "").strip():
            return str(value)
    return ""


def _prefer_latest_value(records: list[dict], field: str):
    for record in records:
        value = record.get(field)
        if isinstance(value, list) and value:
            return value
        if isinstance(value, dict) and value:
            return value
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        if value is True:
            return value
    return [] if field.endswith("s") else ""


def merge(entries: list[dict]) -> dict:
    groups: dict[tuple[str, str, str, str, str], list[dict]] = {}
    for raw in entries:
        entry = raw if isinstance(raw, dict) else {}
        place = str(entry.get("place", ""))
        topic = str(entry.get("topic", entry.get("category", "")))
        url = str(entry.get("url", ""))
        platform = str(entry.get("platform", ""))
        site = str(entry.get("site", platform or "unknown"))
        groups.setdefault((place, topic, url, platform, site), []).append(entry)

    merged_entries = []
    for key, records in groups.items():
        records_sorted = sorted(records, key=lambda item: _checked_at_rank(item.get("checked_at", "")), reverse=True)
        newest = records_sorted[0] if records_sorted else {}
        canonical_to_fact: dict[str, object] = {}
        for record in records:
            raw_facts = record.get("facts", [])
            if raw_facts is None:
                continue
            iterable = raw_facts if isinstance(raw_facts, list) else [raw_facts]
            for fact in iterable:
                canonical = _safe_json_key(fact)
                if canonical not in canonical_to_fact:
                    canonical_to_fact[canonical] = fact
        facts = [canonical_to_fact[key] for key in sorted(canonical_to_fact.keys())]

        merged_entries.append(
            {
                "place": str(key[0]),
                "topic": str(key[1]),
                "url": str(key[2]),
                "platform": str(key[3]),
                "site": str(key[4]),
                "checked_at": str(newest.get("checked_at", "")),
                "title": _prefer_latest_non_empty(records_sorted, "title"),
                "source_type": _prefer_latest_non_empty(records_sorted, "source_type"),
                "facts": facts,
            }
        )
        merged_entry = merged_entries[-1]
        for field in PASSTHROUGH_FIELDS:
            merged_entry[field] = _prefer_latest_value(records_sorted, field)

    ordered = sorted(merged_entries, key=lambda item: (item["topic"], item["place"], item["site"], item["url"], item["title"]))
    normalized: dict[str, dict[str, list[dict]]] = {}
    for entry in ordered:
        normalized.setdefault(entry["place"], {}).setdefault(entry["topic"], []).append(entry)
    summary = {
        "places": sorted({entry["place"] for entry in ordered if entry["place"]}),
        "topics": sorted({entry["topic"] for entry in ordered if entry["topic"]}),
        "platforms": sorted({entry["platform"] for entry in ordered if entry["platform"]}),
        "sites": sorted({entry["site"] for entry in ordered if entry["site"]}),
    }
    return {"entries": ordered, "normalized": normalized, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    merged = merge(payload if isinstance(payload, list) else [])
    output_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
