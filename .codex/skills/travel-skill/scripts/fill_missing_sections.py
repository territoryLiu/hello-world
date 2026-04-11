from pathlib import Path
import argparse
import json

from build_guide_model import SECTION_KEYS, EXECUTION_KEYS


SECTION_DEFAULTS: dict[str, dict] = {
    "overview": {
        "title": "行程概览占位",
        "summary": "待补齐天数、交通节奏与城市切换。",
        "points": ["明确 D1-Dn 的主线目标。"],
    },
    "recommended": {
        "title": "推荐清单占位",
        "summary": "待补齐必须做与可替代方案。",
        "points": ["明确主推路线与替代路线。"],
    },
    "options": {
        "title": "备选方案占位",
        "summary": "待补齐高峰期避坑和替代路线。",
        "points": ["至少提供 2 条可替代安排。"],
    },
    "attractions": {
        "title": "景点优先级占位",
        "summary": "待补齐主线与雨天备选。",
        "points": ["标记必去、可去、可跳过。"],
    },
    "food": {
        "title": "店铺级推荐占位",
        "summary": "待补齐店名、招牌菜、人均与排队时段。",
        "points": ["店铺级推荐：至少 3 家。"],
    },
    "season": {
        "title": "历史体感占位",
        "summary": "待补齐早晚温差、风感和降水概率。",
        "points": ["补充历史体感与体感温度。"],
    },
    "packing": {
        "title": "分层穿衣占位",
        "summary": "待补齐内层/中层/外层与鞋袜建议。",
        "points": ["分层穿衣：按静止与徒步场景给建议。"],
    },
    "transport": {
        "title": "逐段交通占位",
        "summary": "待补齐城际/市内/景区接驳的主备方案。",
        "points": ["逐段交通：每段给主方案和备选。"],
    },
}

EXECUTION_DEFAULTS: dict[str, dict] = {
    "booking_order": {
        "title": "订票顺序占位",
        "summary": "先锁定去程大交通，再锁定返程，最后补齐本地接驳与门票。",
        "points": ["订票顺序：先大交通，后本地接驳与门票。"],
    },
    "daily_table": {
        "title": "每日执行表占位",
        "summary": "待补齐 D1-Dn 上午/下午/晚间节奏与机动时间。",
        "points": ["每日执行表：至少覆盖 3 个时间段。"],
    },
    "budget_bands": {
        "title": "价格区间占位",
        "summary": "待补齐经济/舒适/宽松三档预算。",
        "points": ["价格区间：交通+住宿+餐饮都需给范围。"],
    },
}


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ensure_list(value) -> list:
    return value if isinstance(value, list) else []


def _as_bool_or_false(value) -> bool:
    return value if isinstance(value, bool) else False


def _content_item(title: str, summary: str, points: list[str], is_placeholder: bool) -> dict:
    return {
        "title": title,
        "summary": summary,
        "points": [point for point in points if isinstance(point, str) and point.strip()],
        "is_placeholder": is_placeholder,
    }


def _normalize_content_item(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    title = _clean_text(raw.get("title"))
    summary = _clean_text(raw.get("summary"))
    points = [point.strip() for point in _ensure_list(raw.get("points")) if isinstance(point, str) and point.strip()]
    if not title and not summary and not points:
        return None
    if not title:
        title = "内容条目"
    return _content_item(
        title=title,
        summary=summary,
        points=points,
        is_placeholder=_as_bool_or_false(raw.get("is_placeholder", False)),
    )


def _placeholder_item(default_item: dict) -> dict:
    return _content_item(
        title=default_item["title"],
        summary=default_item["summary"],
        points=default_item["points"],
        is_placeholder=True,
    )


def _normalize_source_item(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    title = _clean_text(raw.get("title"))
    url = _clean_text(raw.get("url"))
    source_type = _clean_text(raw.get("type"))
    checked_at = _clean_text(raw.get("checked_at"))
    if not any([title, url, source_type, checked_at]):
        return None
    return {
        "title": title or "待补充来源",
        "url": url,
        "type": source_type or "unknown",
        "checked_at": checked_at,
    }


def _has_keyword(items: list[dict], keyword: str) -> bool:
    for item in items:
        text = "\n".join([item.get("title", ""), item.get("summary", ""), *item.get("points", [])])
        if keyword in text:
            return True
    return False


def _append_placeholder_if_missing(items: list[dict], keyword: str, default_item: dict) -> list[dict]:
    if _has_keyword(items, keyword):
        return items
    return [*items, _placeholder_item(default_item)]


def fill(payload: dict) -> dict:
    model = payload if isinstance(payload, dict) else {}
    meta = model.get("meta", {})
    sections = model.get("sections", {})
    execution = model.get("execution", {})

    if not isinstance(meta, dict):
        meta = {}
    if not isinstance(sections, dict):
        sections = {}
    if not isinstance(execution, dict):
        execution = {}

    cleaned_sections = {}
    for key in SECTION_KEYS:
        if key == "sources":
            continue
        raw_items = _ensure_list(sections.get(key))
        cleaned_items = [item for item in (_normalize_content_item(raw) for raw in raw_items) if item is not None]
        if not cleaned_items:
            cleaned_items = [_placeholder_item(SECTION_DEFAULTS[key])]
        cleaned_sections[key] = cleaned_items

    raw_sources = _ensure_list(sections.get("sources"))
    cleaned_sources = [item for item in (_normalize_source_item(raw) for raw in raw_sources) if item is not None]
    if not cleaned_sources:
        cleaned_sources = [{"title": "待补充来源", "url": "", "type": "unknown", "checked_at": ""}]
    cleaned_sections["sources"] = cleaned_sources

    cleaned_execution = {}
    for key in EXECUTION_KEYS:
        raw_items = _ensure_list(execution.get(key))
        cleaned_items = [item for item in (_normalize_content_item(raw) for raw in raw_items) if item is not None]
        if not cleaned_items:
            cleaned_items = [_placeholder_item(EXECUTION_DEFAULTS[key])]
        cleaned_execution[key] = cleaned_items

    cleaned_sections["food"] = _append_placeholder_if_missing(cleaned_sections["food"], "店铺级推荐", SECTION_DEFAULTS["food"])
    cleaned_sections["season"] = _append_placeholder_if_missing(cleaned_sections["season"], "历史体感", SECTION_DEFAULTS["season"])
    cleaned_sections["packing"] = _append_placeholder_if_missing(cleaned_sections["packing"], "分层穿衣", SECTION_DEFAULTS["packing"])
    cleaned_sections["transport"] = _append_placeholder_if_missing(cleaned_sections["transport"], "逐段交通", SECTION_DEFAULTS["transport"])
    cleaned_execution["booking_order"] = _append_placeholder_if_missing(
        cleaned_execution["booking_order"], "订票顺序", EXECUTION_DEFAULTS["booking_order"]
    )
    cleaned_execution["budget_bands"] = _append_placeholder_if_missing(
        cleaned_execution["budget_bands"], "价格区间", EXECUTION_DEFAULTS["budget_bands"]
    )

    output_meta = dict(meta) if isinstance(meta, dict) else {}
    output_meta["source_count"] = len(cleaned_sections["sources"])

    ordered_sections = {key: cleaned_sections[key] for key in SECTION_KEYS}
    ordered_execution = {key: cleaned_execution[key] for key in EXECUTION_KEYS}
    return {"meta": output_meta, "sections": ordered_sections, "execution": ordered_execution}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    completed = fill(payload if isinstance(payload, dict) else {})
    output_path.write_text(
        json.dumps(completed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
