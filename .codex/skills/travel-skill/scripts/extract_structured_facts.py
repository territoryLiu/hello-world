from pathlib import Path
import argparse
import json


def _fact_to_text(fact) -> str:
    if isinstance(fact, dict):
        if str(fact.get("text", "")).strip():
            return str(fact.get("text"))
        return json.dumps(fact, ensure_ascii=False, sort_keys=True)
    if isinstance(fact, list):
        return json.dumps(fact, ensure_ascii=False)
    return str(fact or "")


def extract(payload: dict) -> dict:
    categories: dict[str, list[dict]] = {}
    for raw_entry in payload.get("entries", []):
        entry = raw_entry if isinstance(raw_entry, dict) else {}
        category = str(entry.get("category", ""))
        source_url = str(entry.get("url", ""))
        checked_at = str(entry.get("checked_at", ""))
        source_type = str(entry.get("source_type", ""))
        source_title = str(entry.get("title", ""))

        raw_facts = entry.get("facts", [])
        if raw_facts is None:
            raw_facts = []
        facts_iterable = raw_facts if isinstance(raw_facts, list) else [raw_facts]

        for fact in facts_iterable:
            text = _fact_to_text(fact).strip()
            if not text:
                continue
            categories.setdefault(category, []).append(
                {
                    "text": text,
                    "source_url": source_url,
                    "checked_at": checked_at,
                    "source_type": source_type,
                    "source_title": source_title,
                }
            )
    return {"categories": categories}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    extracted = extract(payload if isinstance(payload, dict) else {})
    output_path.write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
