from pathlib import Path
import argparse
import json

TASKS = [
    ("transport", ["official", "platform"]),
    ("weather", ["official", "history"]),
    ("clothing", ["history", "social"]),
    ("attractions", ["official", "social"]),
    ("food", ["local-listing", "social"]),
    ("lodging", ["platform", "map"]),
    ("risk", ["official", "social"]),
]


def build_tasks(payload: dict) -> dict:
    tasks = []
    for category, required_sources in TASKS:
        tasks.append(
            {
                "trip_slug": payload["trip_slug"],
                "category": category,
                "required_sources": required_sources,
                "query_hint": f"{payload['departure_city']} {payload['title']} {category}",
            }
        )
    return {"trip_slug": payload["trip_slug"], "tasks": tasks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    expanded = build_tasks(payload)
    output_path.write_text(
        json.dumps(expanded, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
