from pathlib import Path
import argparse
import json

from build_guide_model import OUTPUT_KEYS


DEFAULT_SOURCE = {"title": "待补充来源", "url": "", "type": "unknown", "checked_at": ""}

LAYER_DEFAULTS = {
    "daily-overview": {
        "summary": "待补充每日行程总览。",
        "days": {"title": "每日安排占位", "summary": "待补齐每天安排。", "points": ["按天拆分主要活动。"]},
        "wearing": {"title": "分层穿衣占位", "summary": "待补齐当前月份穿衣建议。", "points": ["分层穿衣更稳妥。"]},
        "transport": {"title": "逐段交通占位", "summary": "待补齐当天主要交通与接驳。", "points": ["逐段交通建议补齐主备方案。"]},
        "alerts": {"title": "注意事项占位", "summary": "待补齐天气、排队和时间提醒。", "points": ["重要风险建议提前核对。"]},
    },
    "recommended": {
        "recommended_route": {
            "title": "最推荐路线占位",
            "summary": "待补齐最合适的一条路线。",
            "points": ["先给最推荐路线，再补备用方案。"],
        },
        "route_options": {
            "title": "多方案路线占位",
            "summary": "待补齐高铁优先、飞机+高铁组合和纯高铁三类方案。",
            "points": ["默认先给高铁方案。", "超过 600km 再补飞机+高铁组合。"],
        },
        "clothing_guide": {
            "title": "穿衣指南占位",
            "summary": "待补齐城市与景区的穿衣层次。",
            "points": ["城市一套，上山一套。"],
        },
        "attractions": {
            "title": "景点信息占位",
            "summary": "待补齐景点玩法、票价和预约信息。",
            "points": ["景点信息建议补齐费用与预约时间。"],
        },
        "transport_details": {
            "title": "交通详情占位",
            "summary": "待补齐高铁、飞机、公交、打车和接驳细节。",
            "points": ["把高铁车次和飞机班次写清楚。"],
        },
        "food_by_city": {
            "title": "分城市美食占位",
            "summary": "待补齐按城市划分的餐厅推荐。",
            "points": ["每座城市至少给出几家可选店。"],
        },
        "tips": {
            "title": "注意事项与避坑占位",
            "summary": "待补齐预约、排队、天气和预算提醒。",
            "points": ["把容易踩坑的环节提前讲清楚。"],
        },
    },
    "comprehensive": {
        "recommended_route": {
            "title": "最推荐路线占位",
            "summary": "待补齐最推荐的一条执行线。",
            "points": ["把最省心的方案放在最前面。"],
        },
        "route_options": {
            "title": "多方案路线占位",
            "summary": "待补齐高铁优先、飞机+高铁组合和纯高铁方案。",
            "points": ["默认高铁优先。", "跨省长距离再补飞机+高铁。"],
        },
        "clothing_guide": {
            "title": "穿衣指南占位",
            "summary": "待补齐当前月份的气温、体感和必备物品。",
            "points": ["穿衣建议要区分城市和高海拔景区。"],
        },
        "attractions": {
            "title": "景点信息占位",
            "summary": "待补齐景点简介、费用和预约说明。",
            "points": ["景点建议写停留时长和预约口径。"],
        },
        "transport_details": {
            "title": "交通详情占位",
            "summary": "待补齐每一段交通方式、时间和价格区间。",
            "points": ["交通详情建议覆盖高铁、飞机、公交、地铁、打车。"],
        },
        "food_by_city": {
            "title": "分城市美食占位",
            "summary": "待补齐按城市归类的店铺、地址和推荐菜。",
            "points": ["店铺推荐尽量多给一些，方便读者选择。"],
        },
        "tips": {
            "title": "注意事项与避坑占位",
            "summary": "待补齐天气、客流、预约和中转提示。",
            "points": ["把核对日期和风险条件写清楚。"],
        },
    },
}


def _clean_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ensure_list(value) -> list:
    return value if isinstance(value, list) else []


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
    title = _clean_text(raw.get("title")) or "内容条目"
    summary = _clean_text(raw.get("summary"))
    points = [point.strip() for point in _ensure_list(raw.get("points")) if isinstance(point, str) and point.strip()]
    if not summary and not points and title == "内容条目":
        return None
    return _content_item(title, summary, points, isinstance(raw.get("is_placeholder"), bool) and raw.get("is_placeholder", False))


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
    meta = model.get("meta", {})
    outputs = model.get("outputs", {})
    root_sources = _clean_source_list(model.get("sources"))
    image_plan = model.get("image_plan") if isinstance(model.get("image_plan"), dict) else {}

    if not isinstance(meta, dict):
        meta = {}
    if not isinstance(outputs, dict):
        outputs = {}

    cleaned_outputs = {}
    for layer_name in OUTPUT_KEYS:
        layer = outputs.get(layer_name, {})
        layer = layer if isinstance(layer, dict) else {}
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

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    completed = fill(payload if isinstance(payload, dict) else {})
    output_path.write_text(json.dumps(completed, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
