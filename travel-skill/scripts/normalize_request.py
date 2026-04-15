from pathlib import Path
import argparse
import hashlib
import json
import re

DEFAULT_SHARE_MODE = "single-html"
DEFAULT_REVIEW_MODE = "manual-gate"
DEFAULT_SAMPLE_REFERENCE = {"path": "", "density_mode": ""}
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
FOLLOW_UP_BY_FIELD = {
    "title": "请补充这次行程的标题或核心主题。",
    "departure_city": "请补充出发城市。",
    "destinations": "请补充目的地城市或景区。",
    "date_range": "请补充预计出行日期范围。",
    "travelers": "请补充出行人数和同行人信息。",
    "budget": "请补充预算范围。",
}


def slugify(text: str) -> str:
    source_text = text or ""
    result = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", source_text.strip().lower())
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
            "density_mode": str(payload.get("sample_density_mode") or ""),
        }
    return dict(DEFAULT_SAMPLE_REFERENCE)


def build_gate(payload: dict) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    blocking_fields = [field for field in CORE_FIELDS if not payload.get(field)]
    return {
        "can_proceed": not blocking_fields,
        "blocking_fields": blocking_fields,
        "warning_fields": [],
        "follow_up_questions": [FOLLOW_UP_BY_FIELD[field] for field in blocking_fields if field in FOLLOW_UP_BY_FIELD],
        "traveler_constraints": traveler_constraints(payload.get("travelers", {})),
    }


def normalize(payload: dict) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    gate = build_gate(payload)
    trip_slug = slugify(payload.get("title", ""))
    normalized_travelers = payload.get("travelers", {})
    blocking_fields = gate["blocking_fields"]
    return {
        "title": payload.get("title", ""),
        "trip_slug": trip_slug,
        "departure_city": payload.get("departure_city", ""),
        "destinations": payload.get("destinations", []),
        "date_range": payload.get("date_range", {}),
        "travelers": normalized_travelers,
        "traveler_profile": traveler_profile(payload.get("travelers", {})),
        "traveler_constraints": traveler_constraints(payload.get("travelers", {})),
        "budget": payload.get("budget", {}),
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
        "intake_status": "blocked" if blocking_fields else "ready",
        "blocking_fields": blocking_fields,
        "warning_fields": gate["warning_fields"],
        "follow_up_questions": [],
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
