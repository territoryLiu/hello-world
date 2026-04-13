from pathlib import Path
import argparse
import json

from travel_paths import ensure_trip_layout
from travel_config import FLIGHT_HYBRID_THRESHOLD_KM


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _iter_facts(payload: dict) -> list[dict]:
    facts = payload.get("facts")
    if isinstance(facts, list):
        return [item for item in facts if isinstance(item, dict)]
    categories = payload.get("categories")
    if not isinstance(categories, dict):
        return []
    flattened = []
    for topic, items in categories.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                flattened.append({"topic": topic, **item})
    return flattened


def _facts_for_topic(payload: dict, *topics: str) -> list[dict]:
    return [fact for fact in _iter_facts(payload) if _clean_text(fact.get("topic")) in topics]


def _destinations(payload: dict) -> list[str]:
    places = _clean_list(payload.get("destinations"))
    if places:
        return places
    fallback_places = []
    for fact in _iter_facts(payload):
        place = _clean_text(fact.get("place"))
        if place and place not in fallback_places:
            fallback_places.append(place)
    if fallback_places:
        return fallback_places
    departure_city = _clean_text(payload.get("departure_city"))
    return [departure_city] if departure_city else ["目的地待补充"]


def _match_fact(items: list[dict], base_city: str, used_indexes: set[int]) -> dict:
    for index, item in enumerate(items):
        place = _clean_text(item.get("place"))
        if index in used_indexes:
            continue
        if base_city and place and (base_city in place or place in base_city):
            used_indexes.add(index)
            return item
    for index, item in enumerate(items):
        if index not in used_indexes:
            used_indexes.add(index)
            return item
    return {}


def _transport_lines(payload: dict, departure_city: str, base_city: str, transport_fact: dict) -> list[str]:
    lines = []
    from_place = _clean_text(transport_fact.get("from"))
    to_place = _clean_text(transport_fact.get("to"))
    schedule = _clean_text(transport_fact.get("schedule"))
    if from_place and to_place:
        lines.append(f"{from_place} -> {to_place}")
    elif departure_city and base_city and departure_city != base_city:
        lines.append(f"{departure_city} -> {base_city}")
    if schedule:
        lines.append(schedule)
    if not lines:
        lines.append(f"{base_city} 当天以主线交通加短接驳为主。")
    return lines


def _copy_day(day: dict) -> dict:
    copied = {}
    for key, value in day.items():
        if isinstance(value, list):
            copied[key] = list(value)
        else:
            copied[key] = value
    return copied


def _distance_km(payload: dict) -> int | None:
    value = payload.get("distance_km")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None
    return None


def build_main_plan(payload: dict) -> dict:
    departure_city = _clean_text(payload.get("departure_city")) or "出发地待补充"
    destinations = _destinations(payload)
    attraction_facts = _facts_for_topic(payload, "attractions")
    food_facts = _facts_for_topic(payload, "food")
    transport_facts = _facts_for_topic(payload, "long_distance_transport", "transport")
    used_attractions: set[int] = set()
    used_foods: set[int] = set()
    day_count = max(1, min(3, len(destinations)))
    days = []

    for index in range(day_count):
        base_city = destinations[min(index, len(destinations) - 1)]
        attraction_fact = _match_fact(attraction_facts, base_city, used_attractions)
        meal_fact = _match_fact(food_facts, base_city, used_foods)
        transport_fact = transport_facts[min(index, len(transport_facts) - 1)] if transport_facts else {}

        attraction_place = _clean_text(attraction_fact.get("place")) or base_city
        attraction_text = _clean_text(attraction_fact.get("text")) or f"{base_city} 适合安排一段主景点或街区漫游。"
        meal_name = _clean_text(meal_fact.get("shop_name")) or _clean_text(meal_fact.get("text")) or f"{base_city} 当地代表风味"
        backup_spots = []
        for candidate in destinations[index + 1:index + 3]:
            if candidate and candidate != base_city:
                backup_spots.append(candidate)
        if attraction_place and attraction_place != base_city:
            backup_spots.append(attraction_place)

        if index == 0:
            morning = [f"{departure_city} 出发，前往 {base_city}。"]
            theme = f"{base_city} 进场与初逛"
        else:
            morning = [f"上午先衔接 {base_city} 的主要行程。"]
            theme = f"{base_city} 深度安排"

        days.append(
            {
                "day": index + 1,
                "base_city": base_city,
                "theme": theme,
                "morning": morning,
                "afternoon": [f"下午围绕 {attraction_place} 展开。", attraction_text],
                "evening": [f"晚间安排 {meal_name}，并留出收口时间。"],
                "transport": _transport_lines(payload, departure_city, base_city, transport_fact),
                "meals": [meal_name],
                "backup_spots": backup_spots or [f"{base_city} 周边灵活加点"],
            }
        )

    return {
        "plan_id": "main",
        "title": "最推荐路线",
        "strategy": "先按出发地与目的地顺序锁定大交通，再把主要景点、用餐和休息节点整理成逐日主线。",
        "days": days,
    }


def build_rail_days(payload: dict) -> list[dict]:
    days = []
    for day in build_main_plan(payload)["days"]:
        day_copy = _copy_day(day)
        day_copy["theme"] = f"{day_copy['base_city']} 稳妥主线"
        day_copy["morning"] = ["先锁定高铁或城际主交通。"] + day_copy.get("morning", [])
        day_copy["transport"] = ["优先一次锁定大交通，再补短接驳。"] + day_copy.get("transport", [])
        day_copy["backup_spots"] = day_copy.get("backup_spots", []) + [f"{day_copy['base_city']} 市区轻量备选"]
        days.append(day_copy)
    return days


def build_flight_hybrid_days(payload: dict) -> list[dict]:
    departure_city = _clean_text(payload.get("departure_city")) or "出发地"
    days = []
    for index, day in enumerate(build_main_plan(payload)["days"]):
        day_copy = _copy_day(day)
        day_copy["theme"] = f"{day_copy['base_city']} 空铁联运线"
        if index == 0:
            day_copy["morning"] = [f"{departure_city} 先走飞机或高铁快线，再衔接到 {day_copy['base_city']}。"]
        else:
            day_copy["morning"] = [f"把更多完整白天留给 {day_copy['base_city']}，减少折返。"] + day_copy.get("morning", [])
        day_copy["transport"] = ["优先压缩远距离移动，把重交通集中在同一天。"] + day_copy.get("transport", [])
        day_copy["evening"] = day_copy.get("evening", []) + ["晚间尽量住在次日出发更顺手的落脚点。"]
        days.append(day_copy)
    return days


def build_extended_days(payload: dict) -> list[dict]:
    main_days = build_main_plan(payload)["days"]
    days = []
    for index, day in enumerate(main_days):
        day_copy = _copy_day(day)
        day_copy["theme"] = f"{day_copy['base_city']} 慢游线"
        if index == 0:
            day_copy["morning"] = ["出发时间放宽一点，把首日改成轻量进城。"] + day_copy.get("morning", [])
        day_copy["afternoon"] = ["下午优先留给沿线散步或周边补点。"] + day_copy.get("afternoon", [])
        day_copy["transport"] = ["允许多住一晚，减少频繁换酒店。"] + day_copy.get("transport", [])
        day_copy["backup_spots"] = day_copy.get("backup_spots", []) + [f"{day_copy['base_city']} 江边/老城慢游"]
        days.append(day_copy)
    if days:
        last_day = days[-1]
        last_day["evening"] = last_day.get("evening", []) + ["如果体力允许，可把周边点放到最后半天。"]
    return days


def build_option_plans(payload: dict) -> dict:
    distance_km = _distance_km(payload)
    plans = [
        {
            "plan_id": "rail-first",
            "title": "高铁优先方案",
            "fit_for": "节奏稳定，适合先把大交通锁死",
            "tradeoffs": ["需要更早出发，但整体更稳妥"],
            "days": build_rail_days(payload),
        }
    ]
    if isinstance(distance_km, int) and distance_km > FLIGHT_HYBRID_THRESHOLD_KM:
        plans.append(
            {
                "plan_id": "flight-hybrid",
                "title": "空铁联运方案",
                "fit_for": "想压缩超长距离移动时间",
                "tradeoffs": ["成本更高，换乘节点更多"],
                "days": build_flight_hybrid_days(payload),
            }
        )
    plans.append(
        {
            "plan_id": "extended-nearby",
            "title": "周边延伸方案",
            "fit_for": "想放慢节奏并补一个周边点",
            "tradeoffs": ["总时长更长，住宿切换更慢"],
            "days": build_extended_days(payload),
        }
    )
    return {"plans": plans}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    roots = ensure_trip_layout(Path(args.output_root), payload["trip_slug"])
    planning_root = roots["trip_root"] / "planning"
    (planning_root / "route-main.json").write_text(
        json.dumps(build_main_plan(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (planning_root / "route-options.json").write_text(
        json.dumps(build_option_plans(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
