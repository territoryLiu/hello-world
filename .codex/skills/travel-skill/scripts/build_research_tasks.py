from pathlib import Path
import argparse
import json

PLATFORM_MAP = {
    "weather": ["official", "history"],
    "clothing": ["history", "social"],
    "packing": ["official", "social"],
    "long_distance_transport": ["official", "platform"],
    "city_transport": ["official", "map"],
    "tickets_and_booking": ["official"],
    "attractions": ["official", "social"],
    "food": ["local-listing", "social"],
    "lodging_area": ["platform", "map"],
    "seasonality": ["official", "social"],
    "risks": ["official", "social"],
    "sources": ["official", "social"],
}


def build_tasks(payload: dict) -> dict:
    tasks = []
    places = [item for item in payload.get("destinations", []) if isinstance(item, str) and item.strip()]
    topics = payload.get("required_topics", [])
    for place in places:
        for topic in topics:
            platforms = PLATFORM_MAP.get(topic, ["official"])
            for platform in platforms:
                tasks.append(
                    {
                        "trip_slug": payload["trip_slug"],
                        "place": place,
                        "topic": topic,
                        "platform": platform,
                        "required_sources": platforms,
                        "query_hint": f"{payload['departure_city']} {payload['title']} {place} {topic}",
                    }
                )
    return {
        "trip_slug": payload["trip_slug"],
        "research_dimensions": ["place", "topic", "platform"],
        "places": places,
        "tasks": tasks,
    }


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
