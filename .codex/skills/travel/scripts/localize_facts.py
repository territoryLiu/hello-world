from pathlib import Path
import argparse
import json

REPLACEMENTS = [
    ("ticket:", "票价参考："),
    ("CNY", "元"),
    ("arrive before", "建议在"),
    ("for smoother queue", "前到达会更利于错峰"),
    ("smoother queue", "错峰到达会更从容"),
]


def localize_text(text: str) -> str:
    localized = str(text or "").strip()
    for source, target in REPLACEMENTS:
        localized = localized.replace(source, target)
    return " ".join(localized.split())


def _localize_items(items: list) -> list:
    localized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        localized = dict(item)
        localized["text_zh"] = localize_text(item.get("text", ""))
        localized_items.append(localized)
    return localized_items


def localize_payload(payload: dict) -> dict:
    result = dict(payload if isinstance(payload, dict) else {})
    facts = result.get("facts")
    if isinstance(facts, list):
        result["facts"] = _localize_items(facts)
    categories = result.get("categories")
    if isinstance(categories, dict):
        localized_categories = {}
        for topic, items in categories.items():
            localized_categories[topic] = _localize_items(items if isinstance(items, list) else [])
        result["categories"] = localized_categories
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    localized = localize_payload(payload)
    Path(args.output).write_text(
        json.dumps(localized, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
