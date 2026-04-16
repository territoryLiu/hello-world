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


def _bundle_records(payload, *paths: tuple[str, ...]) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    for path in paths:
        current = payload
        valid = True
        for key in path:
            if not isinstance(current, dict):
                valid = False
                break
            current = current.get(key)
        if valid and isinstance(current, list):
            return [item for item in current if isinstance(item, dict)]
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


def _group_record_ids(records: list[dict]) -> dict[tuple[str, str, str, str], list[str]]:
    grouped: dict[tuple[str, str, str, str], list[str]] = {}
    for record in records:
        key = (
            clean_text(record.get("place")),
            clean_text(record.get("topic")),
            clean_text(record.get("site")),
            clean_text(record.get("time_layer")) or "recent",
        )
        grouped.setdefault(key, []).append(clean_text(record.get("record_id")))
    return grouped


def _attach_source_record_ids(records: list[dict], grouped_ids: dict[tuple[str, str, str, str], list[str]]) -> list[dict]:
    counters: dict[tuple[str, str, str, str], int] = {}
    attached = []
    for record in records:
        key = (
            clean_text(record.get("place")),
            clean_text(record.get("topic")),
            clean_text(record.get("site")),
            clean_text(record.get("time_layer")) or "recent",
        )
        index = counters.get(key, 0)
        source_ids = grouped_ids.get(key, [])
        source_record_id = source_ids[index] if index < len(source_ids) else ""
        counters[key] = index + 1
        attached.append({**record, "source_record_id": source_record_id})
    return attached


def _stable_record_id(place_slug: str, item: dict, index: int) -> str:
    topic = _place_slug(clean_text(item.get("topic")) or "unknown")
    site = _place_slug(clean_text(item.get("site")) or "unknown")
    time_layer = _place_slug(clean_text(item.get("time_layer")) or "recent")
    return f"{place_slug}-{topic}-{site}-{time_layer}-{index:03d}"


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
    raw_records = _iter_records(raw_payload, "records") or _bundle_records(raw_payload, ("raw_items",), ("merged", "entries"))
    approved_facts = _iter_records(approved_payload, "facts") or _bundle_records(approved_payload, ("structured", "facts"))
    normalized_site_records = _iter_records(approved_payload, "normalized_records") or _bundle_records(approved_payload, ("structured", "normalized_records"))
    knowledge_points = _iter_records(approved_payload, "knowledge_points") or _bundle_records(approved_payload, ("structured", "knowledge_points"))
    media_records = _iter_records(media_payload, "items") or _bundle_records(media_payload, ("media_candidates", "items"))
    places_from_facts, corridors = split_facts(approved_facts)
    coverage_by_topic = coverage_payload.get("by_topic") if isinstance(coverage_payload, dict) else {}
    coverage_by_topic = coverage_by_topic if isinstance(coverage_by_topic, dict) else {}

    places = _collect_places(raw_records, approved_facts, normalized_site_records, knowledge_points, media_records)
    trip_slug = ""
    for payload in (raw_payload, approved_payload, media_payload, coverage_payload):
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
        normalized_records = []
        for index, item in enumerate(place_raw, start=1):
            record_id = _stable_record_id(place_slug, item, index)
            raw_ref = f"raw/records/{record_id}.json"
            _write_json(place_root / raw_ref, {"trip_slug": trip_slug, "place": place, "record": item})
            normalized_records.append(
                {
                    **item,
                    "record_id": record_id,
                    "raw_ref": raw_ref,
                }
            )
        place_site_records = [item for item in normalized_site_records if item.get("place") == place]
        place_site_records = _attach_source_record_ids(place_site_records, _group_record_ids(normalized_records))
        place_knowledge_points = [item for item in knowledge_points if item.get("place") == place]
        recent_facts = [item for item in place_facts if item.get("time_layer") == "recent"]
        historical_facts = [item for item in place_facts if item.get("time_layer") == "last_year_same_period"]
        relevant_topics = sorted(
            {
                str(item.get("topic")).strip()
                for item in [*place_raw, *place_facts, *place_site_records, *place_knowledge_points]
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
            place_root / "raw" / "web-research.json",
            {"trip_slug": trip_slug, "place": place, "records": place_raw},
        )
        _write_json(
            place_root / "structured-facts.json",
            {"trip_slug": trip_slug, "place": place, "facts": place_facts or places_from_facts.get(place_slug, [])},
        )
        _write_json(
            place_root / "normalized" / "facts.json",
            {"trip_slug": trip_slug, "place": place, "facts": place_facts or places_from_facts.get(place_slug, [])},
        )
        _write_json(
            place_root / "normalized" / "records.json",
            {"trip_slug": trip_slug, "place": place, "records": normalized_records},
        )
        _write_json(
            place_root / "normalized" / "site-records.json",
            {"trip_slug": trip_slug, "place": place, "records": place_site_records},
        )
        _write_json(
            place_root / "knowledge" / "recent.json",
            {"trip_slug": trip_slug, "place": place, "facts": recent_facts},
        )
        _write_json(
            place_root / "knowledge" / "last-year-same-period.json",
            {"trip_slug": trip_slug, "place": place, "facts": historical_facts},
        )
        _write_json(
            place_root / "knowledge" / "merged-topics.json",
            {
                "trip_slug": trip_slug,
                "place": place,
                "topics": {
                    topic: [item for item in place_knowledge_points if item.get("topic") == topic]
                    for topic in relevant_topics
                },
            },
        )
        _write_json(
            place_root / "media-raw.json",
            {"trip_slug": trip_slug, "place": place, "items": place_media},
        )
        _write_json(
            place_root / "media" / "items.json",
            {"trip_slug": trip_slug, "place": place, "items": place_media},
        )
        _write_json(place_root / "site-coverage.json", place_coverage)
        _write_json(place_root / "coverage" / "site-coverage.json", place_coverage)

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
