from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import (
    FLIGHT_HYBRID_THRESHOLD_KM,
    FLIGHT_HYBRID_THRESHOLD_LABEL,
    GUIDE_OUTPUT_KEYS as OUTPUT_KEYS,
    LONG_DISTANCE_RULE_OVER,
    LONG_DISTANCE_RULE_WITHIN,
)
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
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_copy(text: str) -> str:
    normalized = _clean_text(text)
    for source, target in POSITIVE_REPLACEMENTS:
        normalized = normalized.replace(source, target)
    normalized = normalized.replace("不要", "建议")
    normalized = normalized.replace("避免", "尽量用更省力的方式处理")
    return " ".join(normalized.split())


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


def _content_item(
    title: str,
    summary: str,
    points: list[str],
    is_placeholder: bool = False,
    extra_fields: dict | None = None,
) -> dict:
    item = {
        "title": _clean_text(title) or "内容条目",
        "summary": _normalize_copy(summary),
        "points": [_normalize_copy(point) for point in points if _clean_text(point)],
        "is_placeholder": is_placeholder,
    }
    if isinstance(extra_fields, dict):
        item.update(extra_fields)
    return item


def _with_common_fields(raw: dict, topic: str, payload: dict) -> dict:
    fact = dict(raw)
    fact["topic"] = _clean_text(raw.get("topic") or topic)
    fact["text"] = _normalize_copy(raw.get("text_zh") or raw.get("text", ""))
    fact["source_url"] = _clean_text(raw.get("source_url"))
    fact["source_title"] = _clean_text(raw.get("source_title"))
    fact["source_type"] = _clean_text(raw.get("source_type") or raw.get("platform"))
    fact["checked_at"] = _clean_text(raw.get("checked_at")) or _clean_text(payload.get("checked_at"))
    fact["site"] = _clean_text(raw.get("site") or raw.get("platform") or raw.get("source_type")) or "unknown"
    fact["place"] = _clean_text(raw.get("place") or raw.get("city"))
    fact["shop_name"] = _clean_text(raw.get("shop_name"))
    fact["address"] = _clean_text(raw.get("address"))
    fact["flavor_style"] = _clean_text(raw.get("flavor_style"))
    fact["queue_tip"] = _clean_text(raw.get("queue_tip"))
    fact["ticket_price"] = _clean_text(raw.get("ticket_price"))
    fact["reservation"] = _clean_text(raw.get("reservation"))
    fact["reservation_window"] = _clean_text(raw.get("reservation_window"))
    fact["suggested_duration"] = _clean_text(raw.get("suggested_duration"))
    fact["arrival_window"] = _clean_text(raw.get("arrival_window"))
    fact["queue_peak"] = _clean_text(raw.get("queue_peak"))
    fact["dropoff_point"] = _clean_text(raw.get("dropoff_point"))
    fact["recommended_dishes"] = _clean_list(raw.get("recommended_dishes"))
    fact["backup_options"] = _clean_list(raw.get("backup_options"))
    fact["comment_highlights"] = _clean_list(raw.get("comment_highlights"))
    fact["timeline"] = _clean_list(raw.get("timeline"))
    fact["shot_candidates"] = raw.get("shot_candidates") if isinstance(raw.get("shot_candidates"), list) else []
    fact["fallback_strategy"] = _clean_text(raw.get("fallback_strategy"))
    fact["checked_date_context"] = _clean_text(raw.get("checked_date_context"))
    fact["latest_searchable_schedule"] = raw.get("latest_searchable_schedule") if isinstance(raw.get("latest_searchable_schedule"), dict) else {}
    fact["schedule"] = _clean_text(raw.get("schedule"))
    fact["price_range"] = _clean_text(raw.get("price_range"))
    fact["commute_duration"] = _clean_text(raw.get("commute_duration"))
    fact["transfer_city"] = _clean_text(raw.get("transfer_city"))
    fact["stopover_suggestion"] = _clean_text(raw.get("stopover_suggestion"))
    fact["transport_modes"] = _clean_list(raw.get("transport_modes"))
    fact["best_months"] = _clean_list(raw.get("best_months"))
    fact["current_window"] = _clean_text(raw.get("current_window"))
    fact["not_best_now"] = _clean_text(raw.get("not_best_now"))
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


def _source_meta(fact: dict) -> dict:
    return _source_item(fact)


def _comment_highlights(fact: dict, limit: int = 3) -> list[str]:
    comments = [_normalize_copy(item) for item in _clean_list(fact.get("comment_highlights")) if _clean_text(item)]
    return comments[:limit]


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
    extra_fields = {"source_meta": _source_meta(fact)}
    comments = _comment_highlights(fact)
    if comments:
        extra_fields["comment_highlights"] = comments
    return _content_item(title, fact.get("text", ""), points, extra_fields=extra_fields)


def _traveler_notes(constraints: dict) -> list[str]:
    if not isinstance(constraints, dict):
        return []
    notes = []
    if constraints.get("requires_accessible_pace"):
        notes.append("节奏放松一些会更舒服，午后留出休息缓冲会更稳妥。")
    if constraints.get("avoid_long_unbroken_walks"):
        notes.append("把步行段拆短，并把接驳点安排得更近，会更省力。")
    if constraints.get("has_children"):
        notes.append("有小孩同行时把高强度项目放在上午，体感会更从容。")
    if constraints.get("has_seniors"):
        notes.append("有长辈同行时优先安排少换乘、少爬升的路线。")
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
        return {
            "long_distance": (
                LONG_DISTANCE_RULE_OVER
                if distance_km > FLIGHT_HYBRID_THRESHOLD_KM
                else LONG_DISTANCE_RULE_WITHIN
            )
        }
    return {"long_distance": "unknown"}


def _transport_fallback_lines(fact: dict) -> list[str]:
    if fact.get("fallback_strategy") != "latest-searchable-date":
        return []
    latest_schedule = fact.get("latest_searchable_schedule")
    if not isinstance(latest_schedule, dict):
        return []
    lines = []
    latest_date = _clean_text(latest_schedule.get("date"))
    if latest_date:
        lines.append(f"最近可售日：{latest_date}")
    trains = _clean_list(latest_schedule.get("trains"))
    if trains:
        lines.append(f"参考车次：{'；'.join(trains[:3])}")
    checked_date = _clean_text(fact.get("checked_date_context")) or _clean_text(fact.get("checked_at"))
    if checked_date:
        lines.append(f"检索基准日：{checked_date}")
    lines.append("正式售票后再复核当日车次与票价。")
    return lines


def _transport_metric_lines(fact: dict) -> list[str]:
    lines = []
    if fact.get("schedule"):
        lines.append(f"班次参考：{fact['schedule']}")
    if fact.get("price_range"):
        lines.append(f"票价参考：{fact['price_range']}")
    if fact.get("commute_duration"):
        lines.append(f"通勤时长：{fact['commute_duration']}")
    if fact.get("arrival_window"):
        lines.append(f"建议到达：{fact['arrival_window']}")
    if fact.get("queue_peak"):
        lines.append(f"高峰提示：{fact['queue_peak']}")
    if fact.get("dropoff_point"):
        lines.append(f"落点提示：{fact['dropoff_point']}")
    if fact.get("transport_modes"):
        lines.append(f"可行交通：{'、'.join(fact['transport_modes'])}")
    if fact.get("transfer_city"):
        lines.append(f"中转城市：{fact['transfer_city']}")
    if fact.get("stopover_suggestion"):
        lines.append(f"中转建议：{fact['stopover_suggestion']}")
    return lines


def _seasonality_lines(fact: dict) -> list[str]:
    lines = []
    if fact.get("best_months"):
        lines.append(f"最美月份：{'、'.join(fact['best_months'])}")
    if fact.get("current_window"):
        lines.append(f"当前时段：{fact['current_window']}")
    if fact.get("not_best_now"):
        lines.append(f"观景节奏：{fact['not_best_now']}")
    return lines


def _transport_matrix(fact: dict, transport_rule: dict) -> list[dict]:
    schedule = _clean_text(fact.get("schedule")) or "以最新可查询班次为参考"
    price = _clean_text(fact.get("price_range")) or "票价待临近售票日复核"
    duration = _clean_text(fact.get("commute_duration")) or "总耗时待复核"
    transfer_city = _clean_text(fact.get("transfer_city")) or "中转城市待复核"
    stopover = _clean_text(fact.get("stopover_suggestion")) or "可按到达时间安排半日打卡"
    transport_modes = "、".join(_clean_list(fact.get("transport_modes"))) or "高铁、飞机、公交、打车"
    matrix = [
        {
            "name": "高铁优先",
            "schedule": schedule,
            "price": price,
            "duration": duration,
            "notes": "默认首选，时刻稳定，便于锁定整段行程节奏。",
        },
        {
            "name": "空铁联运",
            "schedule": f"飞机 + 高铁，经{transfer_city}",
            "price": "通常高于纯高铁，适合压缩总耗时",
            "duration": f"适合超 {FLIGHT_HYBRID_THRESHOLD_LABEL} 跨省移动",
            "notes": stopover,
        },
        {
            "name": "全景接驳",
            "schedule": "覆盖大交通 + 城市公交/地铁/打车/自驾",
            "price": "按分段交通叠加估算",
            "duration": "把到站后通勤一并算入",
            "notes": f"可行方式：{transport_modes}",
        },
    ]
    if transport_rule.get("long_distance") != LONG_DISTANCE_RULE_OVER:
        matrix[1]["notes"] = "距离较短时以高铁或直达交通为主，空铁联运作为补充参考。"
    return matrix


def _transport_access_cards(transport_facts: list[dict]) -> list[dict]:
    if not transport_facts:
        return []
    primary_fact = transport_facts[0]
    modes = set(_clean_list(primary_fact.get("transport_modes")))
    cards = []
    if {"公交", "地铁"} & modes:
        points = []
        if "公交" in modes:
            points.append("公交可作为景点之间的补位方案，适合留足换乘时间。")
        if "地铁" in modes:
            points.append("地铁适合城市核心区移动，早晚高峰更适合预留缓冲。")
        if primary_fact.get("commute_duration"):
            points.append(f"整体通勤参考：{primary_fact['commute_duration']}")
        cards.append(
            _content_item(
                "市内公共交通",
                "把公交和地铁单独拎出来看，更方便安排落地后的时间。",
                points,
                extra_fields={"card_kind": "transport-access"},
            )
        )
    if "打车" in modes:
        cards.append(
            _content_item(
                "打车与短接驳",
                "打车更适合早出晚归或景点分散的时段，节奏会更稳。",
                [
                    "打车适合补齐高铁站、机场、酒店与景点之间的短接驳。",
                    "多人同行时分摊后通常更省心。",
                    "热门时段建议预留叫车缓冲。",
                ],
                extra_fields={"card_kind": "transport-access"},
            )
        )
    if "自驾" in modes:
        cards.append(
            _content_item(
                "自驾与机动方案",
                "自驾更适合景点分散或想保留机动停留点的行程。",
                [
                    "自驾适合把拍照停留、临时加点和返程节奏掌握在自己手里。",
                    "景区停车、山路天气和返程疲劳更适合单独复核。",
                ],
                extra_fields={"card_kind": "transport-access"},
            )
        )
    return cards


def _route_option_cards(payload: dict, transport_facts: list[dict]) -> list[dict]:
    distance_km = _distance_km(payload)
    rule = _transport_rule(distance_km)
    traveler_points = _traveler_notes(payload.get("traveler_constraints", {}))
    primary_fact = transport_facts[0] if transport_facts else {}
    base_summary = primary_fact.get("text") or "先把大交通定下来，再安排市内接驳。"
    fallback_points = _transport_fallback_lines(primary_fact) if primary_fact else []
    stopover_lines = [
        line
        for line in _transport_metric_lines(primary_fact)
        if line.startswith("中转城市：") or line.startswith("中转建议：")
    ]
    primary_card = _content_item(
        "高铁优先方案",
        f"高铁优先，时间更稳定。{base_summary}",
        ["默认首选：高铁优先。", *fallback_points, *traveler_points[:2]],
    )
    if primary_fact:
        primary_card["transport_matrix"] = _transport_matrix(primary_fact, rule)
        primary_card["source_meta"] = _source_meta(primary_fact)
    cards = [primary_card]
    if rule["long_distance"] == LONG_DISTANCE_RULE_OVER:
        cards.append(
            _content_item(
                "空铁联运方案",
                f"行程超过 {FLIGHT_HYBRID_THRESHOLD_LABEL} 时同步给出空铁联运，兼顾效率和到站后的接驳稳定性。",
                [
                    "适合长距离跨省移动时压缩总耗时。",
                    "可结合中转城市安排半日或一日停留。",
                    *stopover_lines,
                    *traveler_points[:2],
                ],
            )
        )
        cards.append(
            _content_item(
                "纯高铁备选",
                "保留纯高铁备选，便于在天气或航班波动时快速切换。",
                ["适合作为稳妥备选。", *traveler_points[:1]],
            )
        )
    return cards


def _route_option_cards_from_planning(planning: dict) -> list[dict]:
    route_options = planning.get("route_options") if isinstance(planning, dict) else {}
    plans = route_options.get("plans") if isinstance(route_options, dict) else []
    cards = []
    for plan in plans if isinstance(plans, list) else []:
        day_lines = []
        for day in plan.get("days", []) if isinstance(plan.get("days"), list) else []:
            if not isinstance(day, dict):
                continue
            day_no = day.get("day")
            theme = _clean_text(day.get("theme"))
            if day_no is not None and theme:
                day_lines.append(f"D{day_no}：{theme}")
        cards.append(
            _content_item(
                plan.get("title", "备选方案"),
                plan.get("fit_for", ""),
                [*(_clean_list(plan.get("tradeoffs"))), *day_lines],
            )
        )
    return cards


def _food_cards(food_facts: list[dict]) -> list[dict]:
    cards = []
    multi_shop_mode = len(food_facts) > 1
    if multi_shop_mode:
        grouped: dict[tuple[str, str], list[dict]] = {}
        for fact in food_facts:
            place = _clean_text(fact.get("place")) or "当地"
            flavor = _clean_text(fact.get("flavor_style")) or "地方风味"
            grouped.setdefault((place, flavor), []).append(fact)
        for (place, flavor), items in grouped.items():
            dish_pool: list[str] = []
            for item in items:
                for dish in _clean_list(item.get("recommended_dishes")):
                    if dish not in dish_pool:
                        dish_pool.append(dish)
            cards.append(
                _content_item(
                    f"{place} · {flavor}概览",
                    "先看这一组更稳妥的代表店，再决定具体用餐顺序。",
                    [
                        f"{len(items)} 家可选",
                        f"代表菜：{'、'.join(dish_pool[:4])}" if dish_pool else "代表菜待补充",
                    ],
                    extra_fields={"card_kind": "food-group"},
                )
            )
    for fact in food_facts:
        place = _clean_text(fact.get("place")) or "当地"
        shop_name = _clean_text(fact.get("shop_name")) or _clean_text(fact.get("source_title")) or "推荐餐厅"
        flavor = _clean_text(fact.get("flavor_style")) or "地方风味"
        title = f"{place} · {flavor}" if multi_shop_mode else f"{place} · {shop_name}"
        summary = fact.get("text") or flavor or "适合安排在行程中的一顿正餐。"
        points = []
        if multi_shop_mode:
            points.append(f"店名：{shop_name}")
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
        if fact.get("reservation_window"):
            points.append(f"预约时窗：{fact['reservation_window']}")
        if fact.get("arrival_window"):
            points.append(f"建议到达：{fact['arrival_window']}")
        if fact.get("queue_peak"):
            points.append(f"排队高峰：{fact['queue_peak']}")
        if fact.get("dropoff_point"):
            points.append(f"落点提示：{fact['dropoff_point']}")
        if fact.get("site"):
            points.append(f"来源站点：{fact['site']}")
        if fact.get("source_title"):
            points.append(f"参考来源：{fact['source_title']}")
        extra_fields = {"source_meta": _source_meta(fact)}
        comments = _comment_highlights(fact)
        if comments:
            extra_fields["comment_highlights"] = comments
        cards.append(_content_item(title, summary, points, extra_fields=extra_fields))
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
        extra_fields = {"source_meta": _source_meta(fact)}
        comments = _comment_highlights(fact)
        if comments:
            extra_fields["comment_highlights"] = comments
        cards.append(_content_item(title, fact.get("text", ""), points, extra_fields=extra_fields))
    return cards


def _enrich_attraction_cards(cards: list[dict], attraction_facts: list[dict]) -> list[dict]:
    enriched = []
    for index, card in enumerate(cards):
        fact = attraction_facts[index] if index < len(attraction_facts) else {}
        points = list(card.get("points", []))
        extras = []
        if fact.get("reservation_window"):
            extras.append(f"预约时窗：{fact['reservation_window']}")
        if fact.get("arrival_window"):
            extras.append(f"建议到达：{fact['arrival_window']}")
        if fact.get("queue_peak"):
            extras.append(f"排队高峰：{fact['queue_peak']}")
        if fact.get("dropoff_point"):
            extras.append(f"落点提示：{fact['dropoff_point']}")
        card_copy = dict(card)
        card_copy["points"] = points + [_normalize_copy(item) for item in extras if _clean_text(item)]
        enriched.append(card_copy)
    return enriched


def _tips_cards(risk_facts: list[dict], constraints: dict, weather_facts: list[dict]) -> list[dict]:
    cards = [_simple_fact_card(fact, "行前提示") for fact in risk_facts]
    seasonality_fact = next((fact for fact in weather_facts if fact.get("topic") == "seasonality"), None)
    if seasonality_fact:
        cards.append(_content_item("出行时机", seasonality_fact.get("text", ""), _seasonality_lines(seasonality_fact)))
    traveler_notes = _traveler_notes(constraints)
    if traveler_notes:
        cards.append(_content_item("节奏与体力安排", traveler_notes[0], traveler_notes[1:]))
    weather_fact = next((fact for fact in weather_facts if fact.get("topic") == "weather"), None)
    if weather_fact:
        cards.append(_simple_fact_card(weather_fact, "天气提醒"))
    return cards


def _clothing_cards(clothing_facts: list[dict], weather_facts: list[dict], constraints: dict) -> list[dict]:
    cards = [_simple_fact_card(fact, "穿衣建议") for fact in clothing_facts[:2]]
    weather_fact = next((fact for fact in weather_facts if fact.get("topic") == "weather"), None)
    if weather_fact:
        cards.append(_simple_fact_card(weather_fact, "天气体感"))
    seasonality_fact = next((fact for fact in weather_facts if fact.get("topic") == "seasonality"), None)
    if seasonality_fact:
        cards.append(_content_item("出行时机", seasonality_fact.get("text", ""), _seasonality_lines(seasonality_fact)))
    traveler_notes = _traveler_notes(constraints)
    if traveler_notes:
        cards.append(_content_item("随行成员节奏", traveler_notes[0], traveler_notes[1:]))
    return cards


def _pick_fact(items: list[dict], index: int) -> dict:
    if not items:
        return {}
    return items[index] if index < len(items) else items[-1]


def _daily_plan_cards(
    attraction_facts: list[dict],
    food_facts: list[dict],
    transport_facts: list[dict],
    lodging_facts: list[dict],
    traveler_notes: list[str],
) -> list[dict]:
    seed_count = max(len(attraction_facts), len(food_facts), 1)
    day_count = max(1, min(3, seed_count))
    cards = []
    for index in range(day_count):
        morning_fact = _pick_fact(attraction_facts, index)
        afternoon_fact = _pick_fact(attraction_facts, index + 1 if len(attraction_facts) > 1 else index)
        lunch_fact = _pick_fact(food_facts, index * 2)
        dinner_fact = _pick_fact(food_facts, index * 2 + 1 if len(food_facts) > 1 else index * 2)
        transport_fact = _pick_fact(transport_facts, 0)
        lodging_fact = _pick_fact(lodging_facts, index)

        morning_text = morning_fact.get("place") or morning_fact.get("text") or "先安排一段轻量开场。"
        afternoon_text = afternoon_fact.get("place") or afternoon_fact.get("text") or "下午留给主景点或城市漫游。"
        dinner_text = dinner_fact.get("shop_name") or dinner_fact.get("flavor_style") or dinner_fact.get("text") or "晚餐安排当地代表菜。"
        lunch_text = lunch_fact.get("shop_name") or lunch_fact.get("flavor_style") or lunch_fact.get("text") or "中午安排一顿当地口味。"
        transport_text = transport_fact.get("schedule") or transport_fact.get("text") or "把当天的接驳与返程缓冲单独预留。"
        lodging_text = lodging_fact.get("text") or traveler_notes[0] if traveler_notes else "晚间适合回酒店整理第二天装备。"
        points = [
            f"上午：{morning_text}",
            f"下午：{afternoon_text}",
            f"晚间：{lodging_text}",
            f"交通：{transport_text}",
            f"用餐：午餐看 {lunch_text}；晚餐看 {dinner_text}",
        ]
        if traveler_notes:
            points.append(f"节奏：{traveler_notes[min(index, len(traveler_notes) - 1)]}")
        cards.append(
            _content_item(
                f"D{index + 1} 行程主线",
                "先看当天主线，再按交通、用餐和晚间收口执行。",
                points,
            )
        )
    return cards


def _daily_plan_cards_from_planning(planning: dict) -> list[dict]:
    route_main = planning.get("route_main") if isinstance(planning, dict) else {}
    days = route_main.get("days") if isinstance(route_main, dict) else []
    cards = []
    for day in days if isinstance(days, list) else []:
        cards.append(
            _content_item(
                f"D{day['day']} {day['theme']}",
                f"落脚 {day['base_city']}，按白天与晚间节奏执行。",
                [
                    f"上午：{'；'.join(day.get('morning', []))}",
                    f"下午：{'；'.join(day.get('afternoon', []))}",
                    f"晚间：{'；'.join(day.get('evening', []))}",
                    f"交通：{'；'.join(day.get('transport', []))}",
                    f"用餐：{'；'.join(day.get('meals', []))}",
                    f"备选：{'；'.join(day.get('backup_spots', []))}",
                ],
            )
        )
    return cards


def _match_card_media(card: dict, section: str, image_plan: dict) -> dict | None:
    if not isinstance(image_plan, dict):
        return None
    section_images = image_plan.get("section_images")
    if not isinstance(section_images, list):
        return None
    source_meta = card.get("source_meta") if isinstance(card.get("source_meta"), dict) else {}
    source_title = _clean_text(source_meta.get("title"))
    card_title = _clean_text(card.get("title"))
    for entry in section_images:
        if not isinstance(entry, dict):
            continue
        if _clean_text(entry.get("section")) != section:
            continue
        source_ref = _clean_text(entry.get("source_ref"))
        if source_ref and source_ref not in {source_title, card_title}:
            continue
        image_url = _clean_text(entry.get("image_url"))
        if not image_url:
            continue
        return {
            "image_hint": _clean_text(entry.get("image_hint")),
            "source_ref": source_ref,
            "image_url": image_url,
            "image_source_kind": _clean_text(entry.get("image_source_kind")),
        }
    return None


def _attach_card_media(cards: list[dict], section: str, image_plan: dict) -> list[dict]:
    attached = []
    for card in cards:
        card_copy = dict(card)
        media = _match_card_media(card_copy, section, image_plan)
        if media:
            card_copy["card_media"] = media
        attached.append(card_copy)
    return attached


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
    image_plan = payload.get("image_plan") if isinstance(payload.get("image_plan"), dict) else {}

    planning_payload = payload.get("planning") if isinstance(payload.get("planning"), dict) else {}
    route_options = _route_option_cards_from_planning(planning_payload) or _route_option_cards(payload, transport_facts)
    traveler_notes = _traveler_notes(constraints)
    recommended_route = [
        _content_item(
            "最推荐路线",
            "先把大交通和核心景点串起来，再把休息、换乘和用餐节点压进同一条线里。",
            [
                "默认先看高铁优先方案。",
                f"超过 {FLIGHT_HYBRID_THRESHOLD_LABEL} 时同步查看空铁联运。",
                *traveler_notes[:2],
            ],
        )
    ]
    transport_details = route_options + [
        _simple_fact_card(fact, "交通细节", _transport_fallback_lines(fact) + _transport_metric_lines(fact))
        for fact in transport_facts[:3]
    ] + _transport_access_cards(transport_facts)
    clothing_cards = _clothing_cards(clothing_facts, weather_facts, constraints)
    attraction_cards = _enrich_attraction_cards(_attraction_cards(attraction_facts), attraction_facts)
    food_cards = _food_cards(food_facts)
    tips_cards = _tips_cards(risk_facts, constraints, weather_facts)
    clothing_cards = _attach_card_media(clothing_cards, "clothing_guide", image_plan)
    attraction_cards = _attach_card_media(attraction_cards, "attractions", image_plan)
    transport_details = _attach_card_media(transport_details, "transport_details", image_plan)
    food_cards = _attach_card_media(food_cards, "food_by_city", image_plan)

    summary_candidates = [fact["text"] for fact in (transport_facts + weather_facts)[:2] if fact.get("text")]
    summary = " ".join(summary_candidates) if summary_candidates else "先看每日节奏，再按路线和来源逐层展开。"

    daily_day_cards = _daily_plan_cards_from_planning(planning_payload) or _daily_plan_cards(
        attraction_facts, food_facts, transport_facts, lodging_facts, traveler_notes
    )

    daily_overview = {
        "summary": summary,
        "days": daily_day_cards or attraction_cards[:3] or recommended_route[:1],
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
        "image_plan": image_plan,
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
