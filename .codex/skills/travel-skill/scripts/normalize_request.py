from pathlib import Path
import argparse
import hashlib
import json
import re

DEFAULT_SHARE_MODE = "single-html"
DEFAULT_REVIEW_MODE = "manual-gate"
DEFAULT_SAMPLE_REFERENCE = {"path": "sample.html", "density_mode": "match-sample"}
CORE_FIELDS = [
    "title",
    "departure_city",
    "destinations",
    "date_range",
    "travelers",
    "budget",
]
PREFERENCE_FIELDS = ["must_go", "transport_preference"]
TOPIC_DEFAULTS = [
    "weather",
    "clothing",
    "packing",
    "long_distance_transport",
    "city_transport",
    "attractions",
    "tickets_and_booking",
    "food",
    "lodging_area",
    "seasonality",
    "risks",
    "sources",
]


def slugify(text: str) -> str:
    source_text = text or ""
    ascii_map = {
        "五一": "wuyi",
        "端午": "duanwu",
        "南京": "nanjing",
        "延吉": "yanji",
        "长春": "changchun",
        "长白山": "changbaishan",
        "吉林": "jilin",
        "图们": "tumen",
    }
    result = source_text
    for source, target in ascii_map.items():
        result = result.replace(source, f" {target} ")
    result = re.sub(r"[^a-zA-Z0-9]+", "-", result.lower())
    result = re.sub(r"-{2,}", "-", result).strip("-")
    if result:
        return result
    digest = hashlib.sha1(source_text.encode("utf-8")).hexdigest()[:12]
    return f"trip-{digest}"


def traveler_profile(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {"adults": 0, "children": 0, "age_notes": ""}
    count = payload.get("count", 0)
    adults = payload.get("adults", count if isinstance(count, int) else 0)
    children = payload.get("children", 0)
    age_notes = payload.get("age_notes", "")
    return {
        "adults": adults if isinstance(adults, int) else 0,
        "children": children if isinstance(children, int) else 0,
        "age_notes": age_notes.strip() if isinstance(age_notes, str) else "",
    }


def traveler_constraints(payload: dict) -> dict:
    profile = traveler_profile(payload)
    notes = profile["age_notes"]
    has_seniors = any(token in notes for token in ["60+", "老人", "长辈", "闀胯緢"])
    has_children = profile["children"] > 0
    return {
        "has_children": has_children,
        "has_seniors": has_seniors,
        "requires_accessible_pace": has_children or has_seniors,
        "avoid_long_unbroken_walks": has_children or has_seniors,
    }


def sample_reference(payload: dict) -> dict:
    if isinstance(payload.get("sample_reference"), dict):
        incoming = payload["sample_reference"]
        return {
            "path": str(incoming.get("path") or DEFAULT_SAMPLE_REFERENCE["path"]),
            "density_mode": str(incoming.get("density_mode") or DEFAULT_SAMPLE_REFERENCE["density_mode"]),
        }
    if "sample_path" in payload:
        return {
            "path": str(payload.get("sample_path") or DEFAULT_SAMPLE_REFERENCE["path"]),
            "density_mode": DEFAULT_SAMPLE_REFERENCE["density_mode"],
        }
    return dict(DEFAULT_SAMPLE_REFERENCE)


def normalize(payload: dict) -> dict:
    trip_slug = slugify(payload["title"])
    normalized_travelers = payload["travelers"]
    return {
        "title": payload["title"],
        "trip_slug": trip_slug,
        "departure_city": payload["departure_city"],
        "destinations": payload.get("destinations", []),
        "date_range": payload["date_range"],
        "travelers": normalized_travelers,
        "traveler_profile": traveler_profile(payload.get("travelers", {})),
        "traveler_constraints": traveler_constraints(payload.get("travelers", {})),
        "budget": payload["budget"],
        "preferences": {
            "stay": payload.get("stay_preference", ""),
            "pace": payload.get("pace_preference", ""),
            "transport": payload.get("transport_preference", ""),
        },
        "sample_reference": sample_reference(payload),
        "required_topics": payload.get("required_topics", TOPIC_DEFAULTS),
        "share_mode": payload.get("share_mode", DEFAULT_SHARE_MODE),
        "review_mode": payload.get("review_mode", DEFAULT_REVIEW_MODE),
        "missing_core_fields": [key for key in CORE_FIELDS if key not in payload],
        "missing_preference_fields": [key for key in PREFERENCE_FIELDS if key not in payload],
        "research_dimensions": ["place", "topic", "platform", "site"],
        "data_layout": {
            "places_root": "travel-data/places",
            "corridors_root": "travel-data/corridors",
            "trip_root": f"travel-data/trips/{trip_slug}",
            "guides_root": f"travel-data/guides/{trip_slug}",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    normalized = normalize(payload)
    output_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
