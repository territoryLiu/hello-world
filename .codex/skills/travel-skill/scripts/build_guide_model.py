from pathlib import Path
import argparse
import json


OUTPUT_KEYS = ["daily-overview", "recommended", "comprehensive"]


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _iter_facts(payload: dict):
    if isinstance(payload.get("facts"), list):
        for raw in payload["facts"]:
            if isinstance(raw, dict):
                yield {
                    "topic": _clean_text(raw.get("topic")),
                    "text": _clean_text(raw.get("text")),
                    "source_url": _clean_text(raw.get("source_url")),
                    "source_title": _clean_text(raw.get("source_title")),
                    "source_type": _clean_text(raw.get("source_type")),
                    "checked_at": _clean_text(raw.get("checked_at")) or _clean_text(payload.get("checked_at")),
                }
        return

    categories = payload.get("categories", {})
    if not isinstance(categories, dict):
        return
    for topic, items in categories.items():
        iterable = items if isinstance(items, list) else []
        for raw in iterable:
            if isinstance(raw, dict):
                yield {
                    "topic": _clean_text(topic),
                    "text": _clean_text(raw.get("text")),
                    "source_url": _clean_text(raw.get("source_url")),
                    "source_title": _clean_text(raw.get("source_title")),
                    "source_type": _clean_text(raw.get("source_type")),
                    "checked_at": _clean_text(raw.get("checked_at")) or _clean_text(payload.get("checked_at")),
                }


def _facts_by_topic(payload: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for fact in _iter_facts(payload):
        if not fact["topic"] or not fact["text"]:
            continue
        grouped.setdefault(fact["topic"], []).append(fact)
    return grouped


def _dedup_sources(payload: dict) -> list[dict]:
    seen = set()
    result = []
    for fact in _iter_facts(payload):
        if not fact["text"]:
            continue
        source = {
            "title": fact["source_title"] or "待补充来源",
            "url": fact["source_url"],
            "type": fact["source_type"] or "unknown",
            "checked_at": fact["checked_at"] or _clean_text(payload.get("checked_at")),
        }
        key = (source["title"], source["url"], source["type"], source["checked_at"])
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result


def _content_item(title: str, summary: str, points: list[str]) -> dict:
    return {
        "title": title,
        "summary": summary,
        "points": [point for point in points if point],
        "is_placeholder": False,
    }


def _items_from_facts(facts: list[dict], fallback_title: str) -> list[dict]:
    items = []
    for fact in facts:
        title = fact["source_title"] or fallback_title
        points = []
        if fact["source_type"]:
            points.append(f"来源类型: {fact['source_type']}")
        if fact["checked_at"]:
            points.append(f"核对日期: {fact['checked_at']}")
        items.append(_content_item(title, fact["text"], points))
    return items


def _pick(grouped: dict[str, list[dict]], key: str) -> list[dict]:
    return list(grouped.get(key, []))


def compose(payload: dict) -> dict:
    grouped = _facts_by_topic(payload)
    sources = _dedup_sources(payload)

    transport_facts = _pick(grouped, "transport") + _pick(grouped, "long_distance_transport")
    clothing_facts = _pick(grouped, "clothing") + _pick(grouped, "packing")
    risk_facts = _pick(grouped, "risk") + _pick(grouped, "risks")
    lodging_facts = _pick(grouped, "lodging") + _pick(grouped, "lodging_area")
    weather_facts = _pick(grouped, "weather") + _pick(grouped, "seasonality")
    food_facts = _pick(grouped, "food")
    attraction_facts = _pick(grouped, "attractions")

    summary_parts = [fact["text"] for fact in (transport_facts + weather_facts)[:2] if fact.get("text")]
    daily_overview = {
        "summary": "；".join(summary_parts) if summary_parts else "待补充行程总览。",
        "days": _items_from_facts(attraction_facts[:2], "每日安排"),
        "wearing": _items_from_facts(clothing_facts, "穿衣建议"),
        "transport": _items_from_facts(transport_facts, "交通安排"),
        "alerts": _items_from_facts(risk_facts, "注意事项"),
        "sources": list(sources),
    }
    recommended = {
        "overview": _items_from_facts((weather_facts + lodging_facts)[:2], "推荐概览"),
        "route": _items_from_facts(transport_facts[:2], "推荐路线"),
        "days": _items_from_facts(attraction_facts[:3], "每日安排"),
        "attractions": _items_from_facts(attraction_facts, "景点建议"),
        "food": _items_from_facts(food_facts, "美食推荐"),
        "packing_list": _items_from_facts(clothing_facts, "打包建议"),
        "sources": list(sources),
    }
    comprehensive = {
        "overview": _items_from_facts((weather_facts + transport_facts + lodging_facts)[:3], "全面概览"),
        "transport_options": _items_from_facts(transport_facts + lodging_facts[:1], "交通方案"),
        "attractions": _items_from_facts(attraction_facts, "景点清单"),
        "food_options": _items_from_facts(food_facts, "餐饮清单"),
        "lodging": _items_from_facts(lodging_facts, "住宿建议"),
        "seasonality": _items_from_facts(weather_facts, "季节体感"),
        "risks": _items_from_facts(risk_facts, "注意事项"),
        "sources": list(sources),
    }

    meta = {
        "trip_slug": _clean_text(payload.get("trip_slug")),
        "title": _clean_text(payload.get("title")),
        "checked_at": _clean_text(payload.get("checked_at")),
        "source_count": len(sources),
    }
    return {
        "meta": meta,
        "outputs": {
            "daily-overview": daily_overview,
            "recommended": recommended,
            "comprehensive": comprehensive,
        },
        "sources": sources,
        "image_plan": payload.get("image_plan", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    model = compose(payload if isinstance(payload, dict) else {})
    output_path.write_text(
        json.dumps(model, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
