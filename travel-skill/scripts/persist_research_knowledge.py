from pathlib import Path
import argparse
import json

from normalize_request import slugify

def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _place_slug(place: str) -> str:
    text = place.strip() if isinstance(place, str) else ""
    if not text:
        return ""
    return slugify(text)


def _iter_records(payload, key: str) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _collect_places(*groups: list[dict]) -> list[str]:
    places: list[str] = []
    seen = set()
    for items in groups:
        for item in items:
            place = item.get("place")
            if isinstance(place, str) and place.strip() and place not in seen:
                seen.add(place)
                places.append(place)
    return places


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def corridor_slug(from_place: str, to_place: str) -> str:
    return f"{_place_slug(from_place)}-to-{_place_slug(to_place)}"


def split_facts(facts: list[dict]) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    by_place: dict[str, list[dict]] = {}
    by_corridor: dict[str, list[dict]] = {}
    for fact in facts:
        place = clean_text(fact.get("place"))
        from_place = clean_text(fact.get("from"))
        to_place = clean_text(fact.get("to"))
        if place:
            by_place.setdefault(_place_slug(place), []).append(fact)
        elif from_place and to_place:
            by_corridor.setdefault(corridor_slug(from_place, to_place), []).append(fact)
    return by_place, by_corridor


def persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root: Path) -> None:
    raw_records = _iter_records(raw_payload, "records")
    approved_facts = _iter_records(approved_payload, "facts")
    media_records = _iter_records(media_payload, "items")
    places_from_facts, corridors = split_facts(approved_facts)
    coverage_by_topic = coverage_payload.get("by_topic") if isinstance(coverage_payload, dict) else {}
    coverage_by_topic = coverage_by_topic if isinstance(coverage_by_topic, dict) else {}

    places = _collect_places(raw_records, approved_facts, media_records)
    trip_slug = ""
    for payload in (raw_payload, approved_payload, coverage_payload):
        if isinstance(payload, dict) and isinstance(payload.get("trip_slug"), str) and payload.get("trip_slug").strip():
            trip_slug = payload["trip_slug"].strip()
            break

    for place in places:
        place_slug = _place_slug(place)
        if not place_slug:
            continue
        place_root = output_root / "places" / place_slug
        place_raw = [item for item in raw_records if item.get("place") == place]
        place_facts = [item for item in approved_facts if item.get("place") == place]
        place_media = [
            item
            for item in media_records
            if item.get("place") == place or item.get("city") == place or item.get("destination") == place
        ]
        relevant_topics = sorted(
            {
                str(item.get("topic")).strip()
                for item in [*place_raw, *place_facts]
                if isinstance(item.get("topic"), str) and item.get("topic").strip()
            }
        )
        place_coverage = {
            "trip_slug": trip_slug,
            "place": place,
            "site_coverage": {
                topic: coverage_by_topic[topic]
                for topic in relevant_topics
                if topic in coverage_by_topic
            },
        }

        _write_json(
            place_root / "raw-web-research.json",
            {"trip_slug": trip_slug, "place": place, "records": place_raw},
        )
        _write_json(
            place_root / "structured-facts.json",
            {"trip_slug": trip_slug, "place": place, "facts": place_facts or places_from_facts.get(place_slug, [])},
        )
        _write_json(
            place_root / "media-raw.json",
            {"trip_slug": trip_slug, "place": place, "items": place_media},
        )
        _write_json(place_root / "site-coverage.json", place_coverage)

    for slug, corridor_facts in corridors.items():
        corridor_root = output_root / "corridors" / slug
        _write_json(
            corridor_root / "transport.json",
            {"trip_slug": trip_slug, "facts": corridor_facts},
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-research", required=True)
    parser.add_argument("--approved-research", required=True)
    parser.add_argument("--media-raw", required=True)
    parser.add_argument("--site-coverage", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()

    persist(
        _read_json(Path(args.raw_research)),
        _read_json(Path(args.approved_research)),
        _read_json(Path(args.media_raw)),
        _read_json(Path(args.site_coverage)),
        Path(args.output_root),
    )


if __name__ == "__main__":
    main()
