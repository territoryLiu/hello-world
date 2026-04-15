from pathlib import Path
import argparse
import json

from research_contracts import HEAVY_SAMPLE_TARGETS, TIME_LAYERS
from travel_config import TIME_LAYER_TOPICS


SOCIAL_COMMENT_FIELDS = ["comment_highlights", "comment_capture_status", "comment_sample_size"]
VIDEO_EVIDENCE_FIELDS = ["transcript_segments", "timeline", "visual_segments", "shot_candidates"]
EXPERIENCE_FIELDS = ["recent_experience", "high_frequency_comments", "queue_pattern", "scenery_status"]
FOOD_DETAIL_FIELDS = ["shop_name", "address", "recommended_dishes", "per_capita_range", "queue_pattern"]
FAILURE_HANDLING_FIELDS = ["coverage_status", "failure_reason", "user_alert_required"]


TOPIC_SITE_RULES = {
    "weather": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "checked_at"], "evidence_level": "primary"},
        {"platform": "history", "site": "history", "collection_method": "search+fetch", "must_capture_fields": ["summary", "temperature_range"], "evidence_level": "secondary"},
    ],
    "clothing": [
        {"platform": "history", "site": "history", "collection_method": "search+fetch", "must_capture_fields": ["summary", "temperature_range"], "evidence_level": "secondary"},
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "wearing_guidance", "practical_pitfalls", *SOCIAL_COMMENT_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
        {"platform": "social", "site": "douyin", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "wearing_guidance", "practical_pitfalls", *SOCIAL_COMMENT_FIELDS, *VIDEO_EVIDENCE_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "packing": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "facts"], "evidence_level": "primary"},
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "practical_pitfalls", *SOCIAL_COMMENT_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "long_distance_transport": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "schedule", "price_range", "latest_searchable_schedule", "fallback_strategy", "checked_date_context", "facts"], "evidence_level": "primary"},
        {"platform": "platform", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "practical_pitfalls", *SOCIAL_COMMENT_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "city_transport": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "facts"], "evidence_level": "primary"},
        {"platform": "map", "site": "map", "collection_method": "search+fetch", "must_capture_fields": ["summary", "facts"], "evidence_level": "primary"},
    ],
    "tickets_and_booking": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "reservation_rules", "checked_at"], "evidence_level": "primary"},
    ],
    "attractions": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "price_range", "reservation_rules", "facts"], "evidence_level": "primary"},
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", *EXPERIENCE_FIELDS, *SOCIAL_COMMENT_FIELDS, "shot_candidates", "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
        {"platform": "social", "site": "douyin", "collection_method": "travel-skill", "must_capture_fields": ["summary", *EXPERIENCE_FIELDS, *SOCIAL_COMMENT_FIELDS, *VIDEO_EVIDENCE_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
        {"platform": "social", "site": "bilibili", "collection_method": "travel-skill", "must_capture_fields": ["summary", *EXPERIENCE_FIELDS, *SOCIAL_COMMENT_FIELDS, *VIDEO_EVIDENCE_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "food": [
        {"platform": "local-listing", "site": "meituan", "collection_method": "travel-skill", "must_capture_fields": [*FOOD_DETAIL_FIELDS, "recent_experience", "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "primary"},
        {"platform": "local-listing", "site": "dianping", "collection_method": "travel-skill", "must_capture_fields": [*FOOD_DETAIL_FIELDS, "recent_experience", "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "primary"},
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "practical_pitfalls", *SOCIAL_COMMENT_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "lodging_area": [
        {"platform": "platform", "site": "platform", "collection_method": "search+fetch", "must_capture_fields": ["summary", "facts"], "evidence_level": "primary"},
        {"platform": "map", "site": "map", "collection_method": "search+fetch", "must_capture_fields": ["summary", "facts"], "evidence_level": "primary"},
    ],
    "seasonality": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary", "facts"], "evidence_level": "primary"},
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "scenery_status", *SOCIAL_COMMENT_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "risks": [
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "practical_pitfalls", "queue_pattern", "high_frequency_comments", *SOCIAL_COMMENT_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "primary"},
        {"platform": "social", "site": "douyin", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "practical_pitfalls", "queue_pattern", "scenery_status", "high_frequency_comments", *SOCIAL_COMMENT_FIELDS, *VIDEO_EVIDENCE_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
        {"platform": "social", "site": "bilibili", "collection_method": "travel-skill", "must_capture_fields": ["summary", "recent_experience", "practical_pitfalls", "queue_pattern", "scenery_status", "high_frequency_comments", *SOCIAL_COMMENT_FIELDS, *VIDEO_EVIDENCE_FIELDS, "facts", *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
    "sources": [
        {"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["url", "checked_at"], "evidence_level": "primary"},
        {"platform": "social", "site": "xiaohongshu", "collection_method": "travel-skill", "must_capture_fields": ["url", "summary", *SOCIAL_COMMENT_FIELDS, *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
        {"platform": "social", "site": "douyin", "collection_method": "travel-skill", "must_capture_fields": ["url", "summary", *SOCIAL_COMMENT_FIELDS, *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
        {"platform": "social", "site": "bilibili", "collection_method": "travel-skill", "must_capture_fields": ["url", "summary", *SOCIAL_COMMENT_FIELDS, *FAILURE_HANDLING_FIELDS], "evidence_level": "supporting"},
    ],
}


def site_query(payload: dict, place: str, topic: str, site: str) -> str:
    return f"{payload['departure_city']} {payload['title']} {place} {topic} {site}"


def _layers_for_topic(topic: str) -> list[str]:
    return list(TIME_LAYERS) if topic in TIME_LAYER_TOPICS else ["recent"]


def build_tasks(payload: dict) -> dict:
    tasks = []
    places = [item for item in payload.get("destinations", []) if isinstance(item, str) and item.strip()]
    topics = payload.get("required_topics", [])
    for place in places:
        for topic in topics:
            site_rules = TOPIC_SITE_RULES.get(topic, [{"platform": "official", "site": "official", "collection_method": "search+fetch", "must_capture_fields": ["summary"], "evidence_level": "primary"}])
            for time_layer in _layers_for_topic(topic):
                for rule in site_rules:
                    site = rule["site"]
                    tasks.append(
                        {
                            "trip_slug": payload["trip_slug"],
                            "place": place,
                            "topic": topic,
                            "platform": rule["platform"],
                            "site": site,
                            "required_sources": [item["site"] for item in site_rules],
                            "query_hint": f"{payload['departure_city']} {payload['title']} {place} {topic}",
                            "site_query": site_query(payload, place, topic, site),
                            "collection_method": rule["collection_method"],
                            "must_capture_fields": list(rule["must_capture_fields"]),
                            "evidence_level": rule["evidence_level"],
                            "time_layer": time_layer,
                            "sample_target": HEAVY_SAMPLE_TARGETS.get(site, 1),
                            "retry_policy": "retry_same_mode",
                            "fallback_policy": "page_first_then_fallback",
                        }
                    )
    return {
        "trip_slug": payload["trip_slug"],
        "research_dimensions": ["place", "topic", "platform", "site", "time_layer"],
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
