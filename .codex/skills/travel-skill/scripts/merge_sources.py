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
    groups: dict[tuple[str, str], list[dict]] = {}
    for raw in entries:
        entry = raw if isinstance(raw, dict) else {}
        category = str(entry.get("category", ""))
        url = str(entry.get("url", ""))
        groups.setdefault((category, url), []).append(entry)

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
                "category": str(key[0]),
                "url": str(key[1]),
                "checked_at": str(newest.get("checked_at", "")),
                "title": _prefer_latest_non_empty(records_sorted, "title"),
                "source_type": _prefer_latest_non_empty(records_sorted, "source_type"),
                "facts": facts,
            }
        )

    ordered = sorted(merged_entries, key=lambda item: (item["category"], item["url"], item["title"]))
    return {"entries": ordered}


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
