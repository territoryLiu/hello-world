from pathlib import Path
import argparse
import json


SECTION_KEYS = [
    "overview",
    "recommended",
    "options",
    "attractions",
    "food",
    "season",
    "packing",
    "transport",
    "sources",
]

EXECUTION_KEYS = ["booking_order", "daily_table", "budget_bands"]


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _iter_facts(payload: dict):
    categories = payload.get("categories", {})
    if not isinstance(categories, dict):
        return
    for category, items in categories.items():
        iterable = items if isinstance(items, list) else []
        for raw in iterable:
            if isinstance(raw, dict):
                text = _clean_text(raw.get("text"))
                yield {
                    "category": _clean_text(category),
                    "text": text,
                    "source_url": _clean_text(raw.get("source_url")),
                    "source_title": _clean_text(raw.get("source_title")),
                    "source_type": _clean_text(raw.get("source_type")),
                    "checked_at": _clean_text(raw.get("checked_at")),
                }
                continue


def _facts_by_category(payload: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for fact in _iter_facts(payload):
        if not fact["category"] or not fact["text"]:
            continue
        grouped.setdefault(fact["category"], []).append(fact)
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
            "checked_at": fact["checked_at"] or payload.get("checked_at", ""),
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


def _section_from_facts(facts: list[dict], fallback_title: str) -> list[dict]:
    items = []
    for fact in facts:
        title = fact["source_title"] or fallback_title
        points = []
        if fact["source_type"] or fact["checked_at"]:
            points.append(f"来源属性: {fact['source_type'] or 'unknown'} / {fact['checked_at'] or 'unknown'}")
        items.append(_content_item(title=title, summary=fact["text"], points=points))
    return items


def _pick(grouped: dict[str, list[dict]], key: str) -> list[dict]:
    return list(grouped.get(key, []))


def compose(payload: dict) -> dict:
    grouped = _facts_by_category(payload)
    sources = _dedup_sources(payload)

    sections = {key: [] for key in SECTION_KEYS}
    sections["overview"] = _section_from_facts(_pick(grouped, "overview"), "行程概览")
    if not sections["overview"]:
        sections["overview"] = _section_from_facts((_pick(grouped, "transport") + _pick(grouped, "weather"))[:2], "行程概览")
    sections["recommended"] = _section_from_facts((_pick(grouped, "attractions") + _pick(grouped, "food"))[:4], "推荐路线")
    sections["options"] = _section_from_facts((_pick(grouped, "lodging") + _pick(grouped, "risk"))[:4], "备选方案")
    sections["attractions"] = _section_from_facts(_pick(grouped, "attractions"), "景点建议")
    sections["food"] = _section_from_facts(_pick(grouped, "food"), "餐饮建议")
    sections["season"] = _section_from_facts(_pick(grouped, "weather"), "季节体感")
    sections["packing"] = _section_from_facts(_pick(grouped, "clothing"), "穿衣准备")
    sections["transport"] = _section_from_facts(_pick(grouped, "transport"), "交通安排")
    sections["sources"] = sources

    execution = {key: [] for key in EXECUTION_KEYS}
    for item in sections["transport"]:
        text = f"{item['title']}\n{item['summary']}\n" + "\n".join(item["points"])
        if any(token in text for token in ["建议", "优先", "尽早", "先", "再"]):
            execution["booking_order"].append(
                _content_item(
                    title="订票顺序建议",
                    summary=item["summary"],
                    points=["先大交通后本地接驳，及时确认退改规则。"],
                )
            )
    for item in sections["attractions"][:3]:
        execution["daily_table"].append(
            _content_item(
                title="每日执行表",
                summary=item["summary"],
                points=["按上午/下午/晚间拆分并预留机动时间。"],
            )
        )

    for item in sections["options"] + sections["transport"]:
        text = f"{item['title']}\n{item['summary']}\n" + "\n".join(item["points"])
        if any(token in text for token in ["元", "¥", "￥", "预算", "分档"]):
            execution["budget_bands"].append(
                _content_item(
                    title="预算分档",
                    summary=item["summary"],
                    points=["给出经济/舒适/宽松三档价格区间。"],
                )
            )

    ordered_sections = {key: sections[key] for key in SECTION_KEYS}
    ordered_execution = {key: execution[key] for key in EXECUTION_KEYS}

    meta = {
        "trip_slug": _clean_text(payload.get("trip_slug")),
        "title": _clean_text(payload.get("title")),
        "checked_at": _clean_text(payload.get("checked_at")),
        "source_count": len(ordered_sections["sources"]),
    }
    return {"meta": meta, "sections": ordered_sections, "execution": ordered_execution}


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
