from pathlib import Path
import argparse
import html
import json
from urllib.parse import urlsplit


LAYER_SECTION_LABELS = {
    "daily-overview": {
        "days": ("每日安排", "把每天安排放在前面，便于先确定节奏。"),
        "wearing": ("穿衣与装备", "结合当前月份体感与活动强度整理。"),
        "transport": ("交通安排", "优先看当天主交通和接驳。"),
        "alerts": ("注意事项", "把要提前核对的风险单独列出。"),
        "sources": ("信息来源", "保留可追溯来源与核对日期。"),
    },
    "recommended": {
        "overview": ("方案概览", "先看这条路线适合谁、节奏如何。"),
        "route": ("推荐路线", "优先给出更顺手的主线安排。"),
        "days": ("每日安排", "按天展开节奏、景点和餐饮安排。"),
        "attractions": ("景点说明", "整理核心景点与停留理由。"),
        "food": ("美食推荐", "保留店铺级选择空间。"),
        "packing_list": ("必备物品", "结合天气、温差和行程强度整理。"),
        "sources": ("信息来源", "列出正文依赖的来源。"),
    },
    "comprehensive": {
        "overview": ("全面概览", "先看整体路线和多方案逻辑。"),
        "transport_options": ("交通方案", "集中查看高铁、飞机、地铁、公交、打车等方案。"),
        "attractions": ("景点清单", "完整列出景点、预约与停留建议。"),
        "food_options": ("餐饮清单", "尽量保留更多店铺供读者选择。"),
        "lodging": ("住宿建议", "整理落脚区域与动线关系。"),
        "seasonality": ("季节与月份", "说明当前月份可看内容与最佳季节。"),
        "risks": ("注意事项", "把复核项和高风险节点单独列出。"),
        "sources": ("信息来源", "保留全量可追溯来源。"),
    },
}

LAYER_TITLES = {
    "daily-overview": "每日行程速览",
    "recommended": "最推荐攻略",
    "comprehensive": "最全面攻略",
}


def _load_template(name: str) -> str:
    template_path = Path(__file__).resolve().parents[1] / "assets" / "templates" / name
    return template_path.read_text(encoding="utf-8")


def _safe_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_list(value) -> list:
    return value if isinstance(value, list) else []


def _escape(value) -> str:
    return html.escape(_safe_text(value), quote=True)


def _safe_href(value) -> str:
    raw = _safe_text(value)
    if not raw:
        return ""
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    return raw


def _content_badge(item: dict) -> str:
    if item.get("is_placeholder") is True:
        return '<span class="is-placeholder">待补充</span>'
    return ""


def _render_points(points: list[str]) -> str:
    items = [point for point in points if isinstance(point, str) and point.strip()]
    if not items:
        return ""
    joined = "".join(f"<li>{_escape(point)}</li>" for point in items)
    return f'<ul class="card-points">{joined}</ul>'


def _render_content_card(item: dict) -> str:
    placeholder = item.get("is_placeholder") is True
    class_name = "card card-placeholder" if placeholder else "card"
    return (
        f'<article class="{class_name}">'
        '<div class="card-header">'
        f"<h3>{_escape(item.get('title') or '内容条目')}</h3>"
        f"{_content_badge(item)}"
        "</div>"
        f'<p class="card-summary">{_escape(item.get("summary"))}</p>'
        f"{_render_points(_safe_list(item.get('points')))}"
        "</article>"
    )


def _render_source_card(source: dict) -> str:
    raw_url = _safe_text(source.get("url"))
    url = _safe_href(raw_url)
    checked_at = _safe_text(source.get("checked_at"))
    checked = f'<span class="source-badge">核对 {html.escape(checked_at)}</span>' if checked_at else ""
    link = (
        f'<a class="source-url" href="{html.escape(url, quote=True)}" target="_blank" rel="noreferrer noopener">'
        f"{html.escape(url)}</a>"
        if url
        else '<span class="empty-text">暂无链接</span>'
    )
    raw_url_line = f"<p class=\"source-meta\">原始链接：{_escape(raw_url)}</p>" if raw_url and not url else ""
    return (
        '<article class="source-card">'
        '<div class="source-header">'
        f"<h3>{_escape(source.get('title') or '待补充来源')}</h3>"
        f"{checked}"
        "</div>"
        f'<p class="source-meta">来源类型：{_escape(source.get("type") or "unknown")}</p>'
        f"{raw_url_line}"
        f"<p>{link}</p>"
        "</article>"
    )


def _meta_chips(payload: dict, layer_name: str) -> str:
    meta = payload.get("meta", {})
    chips = [
        ("攻略层级", LAYER_TITLES[layer_name]),
        ("核对日期", _safe_text(meta.get("checked_at")) or "待补充"),
        ("来源数量", str(meta.get("source_count", 0))),
    ]
    return "".join(
        f'<span class="meta-chip"><strong>{_escape(label)}</strong>{_escape(value)}</span>'
        for label, value in chips
    )


def _guide_content_script(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"window.__TRAVEL_GUIDE__ = {data};\n"


def _sources_markdown(payload: dict) -> str:
    meta = payload.get("meta", {})
    lines = [
        f"# {_safe_text(meta.get('title')) or '旅游攻略'} 来源清单",
        "",
        f"- trip_slug: {_safe_text(meta.get('trip_slug'))}",
        f"- checked_at: {_safe_text(meta.get('checked_at'))}",
        f"- source_count: {meta.get('source_count', 0)}",
        "",
    ]
    for source in _safe_list(payload.get("sources")):
        title = _safe_text(source.get("title")) or "待补充来源"
        url = _safe_text(source.get("url")) or "(no url)"
        source_type = _safe_text(source.get("type")) or "unknown"
        checked_at = _safe_text(source.get("checked_at")) or "unknown"
        lines.extend(
            [
                f"## {title}",
                f"- url: {url}",
                f"- type: {source_type}",
                f"- checked_at: {checked_at}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _render_section(section_id: str, section_title: str, lead: str, items: list[dict], mobile: bool, page_index: int) -> str:
    cards = "".join(_render_source_card(item) for item in items) if section_id == "sources" else "".join(
        _render_content_card(item) for item in items
    )
    page_attr = f' data-page="{page_index}"' if mobile else ""
    extra_class = " mobile-page" if mobile else ""
    return (
        f'<section id="{section_id}" class="section-block{extra_class}"{page_attr}>'
        '<div class="section-head">'
        f"<h2>{_escape(section_title)}</h2>"
        f'<p class="section-lead">{_escape(lead)}</p>'
        "</div>"
        f'<div class="section-body">{cards}</div>'
        "</section>"
    )


def _layer_nav(layer_name: str) -> str:
    labels = LAYER_SECTION_LABELS[layer_name]
    return "".join(f'<a href="#{section_id}">{_escape(title)}</a>' for section_id, (title, _) in labels.items())


def _render_layer_html(payload: dict, layer_name: str, device: str) -> str:
    meta = payload.get("meta", {})
    layer_payload = payload.get("outputs", {}).get(layer_name, {})
    labels = LAYER_SECTION_LABELS[layer_name]
    title = _safe_text(meta.get("title")) or "旅游攻略"
    summary = _safe_text(layer_payload.get("summary")) or f"{title} · {LAYER_TITLES[layer_name]}"
    sources = _safe_list(layer_payload.get("sources")) or _safe_list(payload.get("sources"))
    sections = []
    page_index = 1
    for section_id, (section_title, lead) in labels.items():
        items = sources if section_id == "sources" else _safe_list(layer_payload.get(section_id))
        sections.append(_render_section(section_id, section_title, lead, items, device == "mobile", page_index))
        page_index += 1

    template_name = "mobile-index.html" if device == "mobile" else "desktop-index.html"
    template = _load_template(template_name)
    replacements = {
        "{{TITLE}}": _escape(title),
        "{{LAYER_TITLE}}": _escape(LAYER_TITLES[layer_name]),
        "{{SUMMARY}}": _escape(summary),
        "{{META_CHIPS}}": _meta_chips(payload, layer_name),
        "{{NAV_ITEMS}}": _layer_nav(layer_name),
        "{{SECTION_CONTENT}}": "\n".join(sections),
        "{{DEVICE}}": _escape(device),
        "{{LAYER}}": _escape(layer_name),
    }
    output = template
    for key, value in replacements.items():
        output = output.replace(key, value)
    return output


def render_site(payload: dict, output_root: Path) -> Path:
    meta = payload.get("meta", {})
    slug = _safe_text(meta.get("trip_slug")) or "travel-guide"

    trip_root = output_root / "trips" / slug
    assets_dir = trip_root / "assets"
    notes_dir = trip_root / "notes"
    assets_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)

    for device in ["desktop", "mobile"]:
        for layer_name in LAYER_TITLES:
            output_dir = trip_root / device / layer_name
            output_dir.mkdir(parents=True, exist_ok=True)
            html_text = _render_layer_html(payload, layer_name, device)
            (output_dir / "index.html").write_text(html_text, encoding="utf-8")

    (assets_dir / "base.css").write_text(_load_template("base.css"), encoding="utf-8")
    (assets_dir / "render-guide.js").write_text(_load_template("render-guide.js"), encoding="utf-8")
    (assets_dir / "guide-content.js").write_text(_guide_content_script(payload), encoding="utf-8")
    (notes_dir / "sources.md").write_text(_sources_markdown(payload), encoding="utf-8")
    return trip_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    render_site(payload if isinstance(payload, dict) else {}, Path(args.output_root))


if __name__ == "__main__":
    main()
