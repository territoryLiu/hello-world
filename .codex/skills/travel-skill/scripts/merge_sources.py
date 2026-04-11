from datetime import datetime
from pathlib import Path
import argparse
import json


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


def merge(entries: list[dict]) -> dict:
    groups: dict[tuple[str, str, str, str], list[dict]] = {}
    for raw in entries:
        entry = raw if isinstance(raw, dict) else {}
        place = str(entry.get("place", ""))
        topic = str(entry.get("topic", entry.get("category", "")))
        url = str(entry.get("url", ""))
        platform = str(entry.get("platform", ""))
        groups.setdefault((place, topic, url, platform), []).append(entry)

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
                "checked_at": str(newest.get("checked_at", "")),
                "title": _prefer_latest_non_empty(records_sorted, "title"),
                "source_type": _prefer_latest_non_empty(records_sorted, "source_type"),
                "facts": facts,
            }
        )

    ordered = sorted(merged_entries, key=lambda item: (item["topic"], item["place"], item["url"], item["title"]))
    normalized: dict[str, dict[str, list[dict]]] = {}
    for entry in ordered:
        normalized.setdefault(entry["place"], {}).setdefault(entry["topic"], []).append(entry)
    summary = {
        "places": sorted({entry["place"] for entry in ordered if entry["place"]}),
        "topics": sorted({entry["topic"] for entry in ordered if entry["topic"]}),
        "platforms": sorted({entry["platform"] for entry in ordered if entry["platform"]}),
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
