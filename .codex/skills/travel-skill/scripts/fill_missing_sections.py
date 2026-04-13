from pathlib import Path
import argparse
import json

from build_guide_model import OUTPUT_KEYS
from travel_config import FLIGHT_HYBRID_THRESHOLD_LABEL


DEFAULT_SOURCE = {
    "title": "待补充来源",
    "url": "",
    "type": "unknown",
    "checked_at": "",
    "site": "unknown",
    "topic": "unknown",
    "time_sensitive": "no",
}

LAYER_DEFAULTS = {
    "daily-overview": {
        "summary": "待补充每日节奏总览。",
        "days": {"title": "每日安排占位", "summary": "按天补齐主要活动与时间轴。", "points": ["先把每天的主线行程排稳。"]},
        "wearing": {"title": "分层穿衣占位", "summary": "结合当月体感补齐穿衣与装备建议。", "points": ["分层穿衣会更稳妥。"]},
        "transport": {"title": "逐段交通占位", "summary": "补齐当天主交通与接驳方式。", "points": ["把高铁、打车和步行段拆开写清楚。"]},
        "alerts": {"title": "注意事项占位", "summary": "把天气、排队和预约提醒单独列出。", "points": ["重要提醒建议提前核对。"]},
    },
    "recommended": {
        "recommended_route": {"title": "最推荐路线占位", "summary": "先给一条最省心的执行路线。", "points": ["先看最推荐方案，再看备选。"]},
        "route_options": {"title": "多方案路线占位", "summary": "补齐高铁优先、空铁联运和备选方案。", "points": ["默认给高铁优先方案。", f"超过 {FLIGHT_HYBRID_THRESHOLD_LABEL} 再补空铁联运。"]},
        "clothing_guide": {"title": "穿衣指南占位", "summary": "补齐城市与景区的穿衣层次。", "points": ["把城市体感和山上体感分开写。"]},
        "attractions": {"title": "景点信息占位", "summary": "补齐景点特色、票价和预约信息。", "points": ["景点信息建议带上费用和预约口径。"]},
        "transport_details": {"title": "交通详情占位", "summary": "补齐高铁、飞机、公交和打车细节。", "points": ["交通细节里把换乘说明写完整。"]},
        "food_by_city": {"title": "分城市美食占位", "summary": "补齐店名、地址、招牌菜和备选店。", "points": ["每个城市尽量给出主推店和备选店。"]},
        "tips": {"title": "注意事项占位", "summary": "补齐预约、排队、天气和节奏提醒。", "points": ["把高风险节点提前说清楚。"]},
    },
    "comprehensive": {
        "recommended_route": {"title": "最推荐路线占位", "summary": "补齐完整执行线。", "points": ["把最稳妥的主路线放在最前。"]},
        "route_options": {"title": "多方案路线占位", "summary": "补齐高铁优先与空铁联运备选。", "points": ["默认高铁优先。", f"长距离行程超过 {FLIGHT_HYBRID_THRESHOLD_LABEL} 再补空铁联运。"]},
        "clothing_guide": {"title": "穿衣指南占位", "summary": "补齐气温、体感与必备物品。", "points": ["把城市和景区的体感拆开写。"]},
        "attractions": {"title": "景点信息占位", "summary": "补齐玩法、费用和预约节奏。", "points": ["景点段落建议带上停留时长。"]},
        "transport_details": {"title": "交通详情占位", "summary": "补齐每一段交通、价格与时间。", "points": ["交通细节建议覆盖高铁、空铁联运和接驳。"]},
        "food_by_city": {"title": "分城市美食占位", "summary": "补齐城市分组下的详细店铺卡片。", "points": ["店铺卡片里放地址、招牌菜和排队提示。"]},
        "tips": {"title": "注意事项占位", "summary": "补齐天气、客流、预约和中转提示。", "points": ["提示里把核对日期写清楚。"]},
    },
}


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ensure_list(value) -> list:
    return value if isinstance(value, list) else []


def _content_item(title: str, summary: str, points: list[str], is_placeholder: bool) -> dict:
    return {
        "title": _clean_text(title) or "内容条目",
        "summary": _clean_text(summary),
        "points": [point for point in points if isinstance(point, str) and point.strip()],
        "is_placeholder": is_placeholder,
    }


def _normalize_content_item(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    title = _clean_text(raw.get("title")) or "内容条目"
    summary = _clean_text(raw.get("summary"))
    points = [point.strip() for point in _ensure_list(raw.get("points")) if isinstance(point, str) and point.strip()]
    if not summary and not points and title == "内容条目":
        return None
    return _content_item(title, summary, points, bool(raw.get("is_placeholder")))


def _normalize_source_item(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    source = {
        "title": _clean_text(raw.get("title")) or DEFAULT_SOURCE["title"],
        "url": _clean_text(raw.get("url")),
        "type": _clean_text(raw.get("type")) or DEFAULT_SOURCE["type"],
        "checked_at": _clean_text(raw.get("checked_at")),
        "site": _clean_text(raw.get("site")) or DEFAULT_SOURCE["site"],
        "topic": _clean_text(raw.get("topic")) or DEFAULT_SOURCE["topic"],
        "time_sensitive": _clean_text(raw.get("time_sensitive")) or DEFAULT_SOURCE["time_sensitive"],
    }
    if not any(value for value in source.values() if value not in {"unknown", "no", "待补充来源"}):
        return None
    return source


def _placeholder(default_item: dict) -> dict:
    return _content_item(default_item["title"], default_item["summary"], default_item["points"], True)


def _clean_content_list(items, default_item: dict) -> list[dict]:
    cleaned = [item for item in (_normalize_content_item(raw) for raw in _ensure_list(items)) if item is not None]
    return cleaned if cleaned else [_placeholder(default_item)]


def _clean_source_list(items) -> list[dict]:
    cleaned = [item for item in (_normalize_source_item(raw) for raw in _ensure_list(items)) if item is not None]
    return cleaned if cleaned else [dict(DEFAULT_SOURCE)]


def fill(payload: dict) -> dict:
    model = payload if isinstance(payload, dict) else {}
    meta = model.get("meta") if isinstance(model.get("meta"), dict) else {}
    outputs = model.get("outputs") if isinstance(model.get("outputs"), dict) else {}
    root_sources = _clean_source_list(model.get("sources"))
    image_plan = model.get("image_plan") if isinstance(model.get("image_plan"), dict) else {}

    cleaned_outputs = {}
    for layer_name in OUTPUT_KEYS:
        layer = outputs.get(layer_name) if isinstance(outputs.get(layer_name), dict) else {}
        defaults = LAYER_DEFAULTS[layer_name]
        cleaned_layer = {}
        if layer_name == "daily-overview":
            cleaned_layer["summary"] = _clean_text(layer.get("summary")) or defaults["summary"]
        for key, default_item in defaults.items():
            if key == "summary":
                continue
            cleaned_layer[key] = _clean_content_list(layer.get(key), default_item)
        cleaned_layer["sources"] = _clean_source_list(layer.get("sources") or root_sources)
        cleaned_outputs[layer_name] = cleaned_layer

    output_meta = dict(meta)
    output_meta["source_count"] = len(root_sources)

    return {
        "meta": output_meta,
        "outputs": cleaned_outputs,
        "sources": root_sources,
        "image_plan": image_plan,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    completed = fill(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(completed, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
