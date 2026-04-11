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
        "transport": {"title": "逐段交通占位", "summary": "待补齐当天主交通与接驳。", "points": ["逐段交通建议补齐主备方案。"]},
        "alerts": {"title": "注意事项占位", "summary": "待补齐天气、排队和时间提醒。", "points": ["重要风险建议提前核对。"]},
    },
    "recommended": {
        "overview": {"title": "推荐概览占位", "summary": "待补齐最合适方案概览。", "points": ["先明确路线骨架。"]},
        "route": {"title": "推荐路线占位", "summary": "待补齐主线路与换乘说明。", "points": ["按城市与景点顺序整理。"]},
        "days": {"title": "每日安排占位", "summary": "待补齐每日执行安排。", "points": ["按上午、下午、晚间拆分。"]},
        "attractions": {"title": "景点安排占位", "summary": "待补齐主景点说明。", "points": ["景点建议标记停留时长。"]},
        "food": {"title": "店铺级推荐占位", "summary": "待补齐店名、地址、菜系与推荐菜。", "points": ["店铺级推荐方便后续选择。"]},
        "packing_list": {"title": "打包建议占位", "summary": "待补齐衣物、药品和证件。", "points": ["分层穿衣和必备物品建议一起整理。"]},
    },
    "comprehensive": {
        "overview": {"title": "全面概览占位", "summary": "待补齐完整路线说明。", "points": ["覆盖多交通与多景点选择。"]},
        "transport_options": {"title": "价格区间占位", "summary": "待补齐全部交通方案与价格区间。", "points": ["价格区间建议写成范围。"]},
        "attractions": {"title": "景点清单占位", "summary": "待补齐全部景点与预约信息。", "points": ["景点清单建议补齐收费与预约。"]},
        "food_options": {"title": "店铺级推荐占位", "summary": "待补齐更多餐饮备选。", "points": ["店铺级推荐更便于读者选择。"]},
        "lodging": {"title": "住宿建议占位", "summary": "待补齐商圈与落脚建议。", "points": ["住宿区域建议按动线整理。"]},
        "seasonality": {"title": "季节体感占位", "summary": "待补齐最佳月份与当前可看内容。", "points": ["历史体感与当前月份建议一起写。"]},
        "risks": {"title": "注意事项占位", "summary": "待补齐风险提醒与复核项。", "points": ["重要风险建议写清核对日期。"]},
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
    output_path.write_text(
        json.dumps(completed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
