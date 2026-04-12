from pathlib import Path
import argparse
import json


OUTPUT_KEYS = ["daily-overview", "recommended", "comprehensive"]
TIME_SENSITIVE_TOPICS = {
    "weather",
    "seasonality",
    "transport",
    "long_distance_transport",
    "city_transport",
    "tickets_and_booking",
    "sources",
}
POSITIVE_REPLACEMENTS = [
    ("不要赶太满", "节奏放松一些会更舒服"),
    ("避免连续走太久", "把步行段拆短会更省力"),
    ("避免排长队", "错峰到达会更从容"),
    ("避免排队", "错峰到达会更从容"),
]


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clean_list(value) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _normalize_copy(text: str) -> str:
    normalized = _clean_text(text)
    for source, target in POSITIVE_REPLACEMENTS:
        normalized = normalized.replace(source, target)
    normalized = normalized.replace("不要", "建议")
    normalized = normalized.replace("避免", "尽量用更省力的方式处理")
    normalized = " ".join(normalized.split())
    return normalized


def _to_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None
    return None


def _content_item(title: str, summary: str, points: list[str]) -> dict:
    return {
        "title": _clean_text(title) or "内容条目",
        "summary": _normalize_copy(summary),
        "points": [_normalize_copy(point) for point in points if _clean_text(point)],
        "is_placeholder": False,
    }


def _with_common_fields(raw: dict, topic: str, payload: dict) -> dict:
    fact = dict(raw)
    fact["topic"] = _clean_text(raw.get("topic") or topic)
    fact["text"] = _normalize_copy(raw.get("text", ""))
    fact["source_url"] = _clean_text(raw.get("source_url"))
    fact["source_title"] = _clean_text(raw.get("source_title"))
    fact["source_type"] = _clean_text(raw.get("source_type") or raw.get("platform"))
    fact["checked_at"] = _clean_text(raw.get("checked_at")) or _clean_text(payload.get("checked_at"))
    fact["site"] = _clean_text(raw.get("site") or raw.get("platform") or raw.get("source_type")) or "unknown"
    fact["place"] = _clean_text(raw.get("place") or raw.get("city"))
    fact["recommended_dishes"] = _clean_list(raw.get("recommended_dishes"))
    fact["backup_options"] = _clean_list(raw.get("backup_options"))
    fact["comment_highlights"] = _clean_list(raw.get("comment_highlights"))
    fact["timeline"] = _clean_list(raw.get("timeline"))
    fact["shot_candidates"] = raw.get("shot_candidates") if isinstance(raw.get("shot_candidates"), list) else []
    fact["time_sensitive"] = "yes" if fact["topic"] in TIME_SENSITIVE_TOPICS else "no"
    return fact


def _iter_facts(payload: dict):
    facts = payload.get("facts")
    if isinstance(facts, list):
        for raw in facts:
            if isinstance(raw, dict):
                yield _with_common_fields(raw, raw.get("topic", ""), payload)
        return

    categories = payload.get("categories")
    if not isinstance(categories, dict):
        return
    for topic, items in categories.items():
        if not isinstance(items, list):
            continue
        for raw in items:
            if isinstance(raw, dict):
                yield _with_common_fields(raw, topic, payload)


def _group_facts(payload: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for fact in _iter_facts(payload):
        if fact["topic"] and fact["text"]:
            grouped.setdefault(fact["topic"], []).append(fact)
    return grouped


def _facts(grouped: dict[str, list[dict]], *topics: str) -> list[dict]:
    merged: list[dict] = []
    for topic in topics:
        merged.extend(grouped.get(topic, []))
    return merged


def _source_item(fact: dict) -> dict:
    return {
        "title": _clean_text(fact.get("source_title")) or _clean_text(fact.get("shop_name")) or "待补充来源",
        "url": _clean_text(fact.get("source_url")),
        "type": _clean_text(fact.get("source_type")) or "unknown",
        "checked_at": _clean_text(fact.get("checked_at")),
        "site": _clean_text(fact.get("site")) or "unknown",
        "topic": _clean_text(fact.get("topic")) or "unknown",
        "time_sensitive": _clean_text(fact.get("time_sensitive")) or "no",
    }


def _dedup_sources(payload: dict) -> list[dict]:
    seen = set()
    result = []
    for fact in _iter_facts(payload):
        source = _source_item(fact)
        key = tuple(source.values())
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return result


def _simple_fact_card(fact: dict, fallback_title: str, extra_points: list[str] | None = None) -> dict:
    points = list(extra_points or [])
    if fact.get("site"):
        points.append(f"来源站点：{fact['site']}")
    if fact.get("source_type"):
        points.append(f"来源类型：{fact['source_type']}")
    if fact.get("checked_at"):
        points.append(f"核对时间：{fact['checked_at']}")
    title = _clean_text(fact.get("source_title")) or fallback_title
    return _content_item(title, fact.get("text", ""), points)


def _traveler_notes(constraints: dict) -> list[str]:
    if not isinstance(constraints, dict):
        return []
    notes = []
    if constraints.get("requires_accessible_pace"):
        notes.append("节奏放松一些会更舒服，午后留出休息缓冲会更稳妥。")
    if constraints.get("avoid_long_unbroken_walks"):
        notes.append("把步行段拆短，并把接驳点安排得更近，会更省力。")
    if constraints.get("has_children"):
        notes.append("亲子同行时把高强度项目放在上午，体感会更从容。")
    if constraints.get("has_seniors"):
        notes.append("长辈同行时优先安排少换乘、少爬升的路线。")
    return notes


def _distance_km(payload: dict):
    for key in ["distance_km", "route_distance_km", "estimated_distance_km"]:
        value = _to_int(payload.get(key))
        if value is not None:
            return value
    meta = payload.get("meta")
    if isinstance(meta, dict):
        for key in ["distance_km", "route_distance_km", "estimated_distance_km"]:
            value = _to_int(meta.get(key))
            if value is not None:
                return value
    return None


def _transport_rule(distance_km) -> dict:
    if isinstance(distance_km, int):
        return {"long_distance": "over-600km" if distance_km > 600 else "within-600km"}
    return {"long_distance": "unknown"}


def _route_option_cards(payload: dict, transport_facts: list[dict]) -> list[dict]:
    distance_km = _distance_km(payload)
    rule = _transport_rule(distance_km)
    traveler_points = _traveler_notes(payload.get("traveler_constraints", {}))
    base_summary = transport_facts[0]["text"] if transport_facts else "先把大交通定下来，再安排市内接驳。"
    cards = [
        _content_item(
            "高铁优先方案",
            f"高铁优先，时刻更稳定。{base_summary}",
            ["默认首选：高铁优先。", *traveler_points[:2]],
        )
    ]
    if rule["long_distance"] == "over-600km":
        cards.append(
            _content_item(
                "空铁联运方案",
                "行程超过 600km 时同步给出空铁联运，兼顾效率和到站后的接驳稳定性。",
                [
                    "适合长距离跨省移动时压缩总耗时。",
                    "可结合中转城市安排半日或一日停留。",
                    *traveler_points[:2],
                ],
            )
        )
        cards.append(
            _content_item(
                "纯高铁备选",
                "保留纯高铁备选，便于在天气或航班波动时快速切换。",
                ["适合作为稳妥备选。"] + traveler_points[:1],
            )
        )
    return cards


def _food_cards(food_facts: list[dict]) -> list[dict]:
    cards = []
    for fact in food_facts:
        place = _clean_text(fact.get("place")) or "当地"
        shop_name = _clean_text(fact.get("shop_name")) or _clean_text(fact.get("source_title")) or "推荐餐厅"
        title = f"{place} · {shop_name}" if place else shop_name
        summary = fact.get("text") or _clean_text(fact.get("flavor_style")) or "适合安排行程中的一顿正餐。"
        points = []
        if fact.get("address"):
            points.append(f"地址：{fact['address']}")
        if fact.get("recommended_dishes"):
            points.append(f"招牌菜：{'、'.join(fact['recommended_dishes'])}")
        if fact.get("flavor_style"):
            points.append(f"风味：{fact['flavor_style']}")
        if fact.get("queue_tip"):
            points.append(f"排队提示：{fact['queue_tip']}")
        if fact.get("backup_options"):
            points.append(f"备选店：{'、'.join(fact['backup_options'])}")
        if fact.get("site"):
            points.append(f"来源站点：{fact['site']}")
        if fact.get("source_title"):
            points.append(f"参考来源：{fact['source_title']}")
        cards.append(_content_item(title, summary, points))
    return cards


def _attraction_cards(attraction_facts: list[dict]) -> list[dict]:
    cards = []
    for fact in attraction_facts:
        title = _clean_text(fact.get("place")) or _clean_text(fact.get("source_title")) or "景点信息"
        points = []
        if fact.get("ticket_price"):
            points.append(f"费用参考：{fact['ticket_price']}")
        if fact.get("reservation"):
            points.append(f"预约提示：{fact['reservation']}")
        if fact.get("suggested_duration"):
            points.append(f"建议时长：{fact['suggested_duration']}")
        if fact.get("site"):
            points.append(f"来源站点：{fact['site']}")
        cards.append(_content_item(title, fact.get("text", ""), points))
    return cards


def _tips_cards(risk_facts: list[dict], constraints: dict, weather_facts: list[dict]) -> list[dict]:
    cards = [_simple_fact_card(fact, "行前提示") for fact in risk_facts]
    traveler_notes = _traveler_notes(constraints)
    if traveler_notes:
        cards.append(_content_item("节奏与体力安排", traveler_notes[0], traveler_notes[1:]))
    if weather_facts:
        cards.append(_simple_fact_card(weather_facts[0], "天气提醒"))
    return cards


def _clothing_cards(clothing_facts: list[dict], weather_facts: list[dict], constraints: dict) -> list[dict]:
    cards = [_simple_fact_card(fact, "穿衣建议") for fact in clothing_facts[:2]]
    if weather_facts:
        cards.append(_simple_fact_card(weather_facts[0], "天气体感"))
    traveler_notes = _traveler_notes(constraints)
    if traveler_notes:
        cards.append(_content_item("随行成员节奏", traveler_notes[0], traveler_notes[1:]))
    return cards


def compose(payload: dict) -> dict:
    grouped = _group_facts(payload)
    sources = _dedup_sources(payload)
    distance_km = _distance_km(payload)
    transport_rule = _transport_rule(distance_km)
    constraints = payload.get("traveler_constraints") if isinstance(payload.get("traveler_constraints"), dict) else {}
    sample_reference = payload.get("sample_reference") if isinstance(payload.get("sample_reference"), dict) else {}

    transport_facts = _facts(grouped, "transport", "long_distance_transport", "city_transport")
    weather_facts = _facts(grouped, "weather", "seasonality")
    clothing_facts = _facts(grouped, "clothing", "packing")
    attraction_facts = _facts(grouped, "attractions")
    food_facts = _facts(grouped, "food")
    risk_facts = _facts(grouped, "risk", "risks")
    lodging_facts = _facts(grouped, "lodging", "lodging_area")

    route_options = _route_option_cards(payload, transport_facts)
    traveler_notes = _traveler_notes(constraints)
    recommended_route = [
        _content_item(
            "最推荐路线",
            "先把大交通和核心景点串起来，再把休息、换乘和用餐节点压进同一条线里。",
            [
                "默认先看高铁优先方案。",
                "超过 600km 时同步查看空铁联运。",
                *traveler_notes[:2],
            ],
        )
    ]
    transport_details = route_options + [_simple_fact_card(fact, "交通细节") for fact in transport_facts[:3]]
    clothing_cards = _clothing_cards(clothing_facts, weather_facts, constraints)
    attraction_cards = _attraction_cards(attraction_facts)
    food_cards = _food_cards(food_facts)
    tips_cards = _tips_cards(risk_facts, constraints, weather_facts)

    summary_candidates = [fact["text"] for fact in (transport_facts + weather_facts)[:2] if fact.get("text")]
    summary = " ".join(summary_candidates) if summary_candidates else "先看每日节奏，再按路线和来源逐层展开。"

    daily_overview = {
        "summary": summary,
        "days": attraction_cards[:3] or recommended_route[:1],
        "wearing": clothing_cards[:3],
        "transport": transport_details[:3],
        "alerts": tips_cards[:3],
        "sources": list(sources),
    }
    recommended = {
        "recommended_route": recommended_route,
        "route_options": route_options,
        "clothing_guide": clothing_cards,
        "attractions": attraction_cards,
        "transport_details": transport_details,
        "food_by_city": food_cards,
        "tips": tips_cards,
        "sources": list(sources),
    }
    comprehensive = {
        "recommended_route": recommended_route,
        "route_options": route_options,
        "clothing_guide": clothing_cards,
        "attractions": attraction_cards,
        "transport_details": transport_details + [_simple_fact_card(fact, "住宿与落脚") for fact in lodging_facts[:2]],
        "food_by_city": food_cards,
        "tips": tips_cards,
        "sources": list(sources),
    }

    meta = {
        "trip_slug": _clean_text(payload.get("trip_slug")) or "travel-guide",
        "title": _clean_text(payload.get("title")),
        "checked_at": _clean_text(payload.get("checked_at")),
        "source_count": len(sources),
        "sample_reference": {
            "path": _clean_text(sample_reference.get("path")),
            "density_mode": _clean_text(sample_reference.get("density_mode")),
        },
        "traveler_constraints": constraints,
        "distance_km": distance_km,
        "transport_rule": transport_rule,
    }

    return {
        "meta": meta,
        "outputs": {
            "daily-overview": daily_overview,
            "recommended": recommended,
            "comprehensive": comprehensive,
        },
        "sources": sources,
        "image_plan": payload.get("image_plan", {}) if isinstance(payload.get("image_plan"), dict) else {},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    model = compose(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
