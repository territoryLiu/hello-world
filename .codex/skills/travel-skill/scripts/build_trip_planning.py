from pathlib import Path
import argparse
import json

from travel_paths import ensure_trip_layout


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


def build_option_plans(payload: dict) -> dict:
    main_days = build_main_plan(payload)["days"]
    return {
        "plans": [
            {
                "plan_id": "rail-first",
                "title": "高铁优先方案",
                "fit_for": "节奏稳定",
                "tradeoffs": ["耗时更长"],
                "days": main_days,
            },
            {
                "plan_id": "flight-hybrid",
                "title": "空铁联运方案",
                "fit_for": "压缩远程移动",
                "tradeoffs": ["成本更高"],
                "days": main_days,
            },
            {
                "plan_id": "extended-nearby",
                "title": "周边延伸方案",
                "fit_for": "想多留半天到一天做周边延展",
                "tradeoffs": ["总天数更长"],
                "days": main_days,
            },
        ]
    }


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
