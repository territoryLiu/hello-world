from pathlib import Path
import argparse
import html
import json
from urllib.parse import urlsplit

from build_guide_model import EXECUTION_KEYS, SECTION_KEYS


SECTION_LABELS = {
    "overview": ("行程概览", "先看路线骨架、交通切换和核对日期。"),
    "recommended": ("推荐方案", "优先给出更稳的主线安排。"),
    "options": ("备选方案", "保留天气、预算和排队波动下的替代动作。"),
    "attractions": ("景点安排", "核心景点和节奏建议。"),
    "food": ("吃喝清单", "餐厅、招牌菜和插入时段。"),
    "season": ("天气体感", "历史体感、风感和补充判断。"),
    "packing": ("穿衣打包", "分层穿衣与实用装备。"),
    "transport": ("逐段交通", "大交通、本地接驳和风险段。"),
    "sources": ("来源清单", "列出当前页面依赖的可追溯信息源。"),
}

EXECUTION_LABELS = {
    "booking_order": ("预订顺序", "高风险项目先锁，避免顺序反了。"),
    "daily_table": ("每日执行", "把每天拆成可落地的执行块。"),
    "budget_bands": ("预算分档", "价格带写成范围，而不是假装实时精确。"),
}

SECTION_ORDER = list(SECTION_KEYS) + list(EXECUTION_KEYS)


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
    return (
        '<article class="source-card">'
        '<div class="source-header">'
        f"<h3>{_escape(source.get('title') or '待补充来源')}</h3>"
        f"{checked}"
        "</div>"
        f'<p class="source-meta">来源类型：{_escape(source.get("type") or "unknown")}</p>'
        f'{f"<p class=\"source-meta\">原始链接：{_escape(raw_url)}</p>" if raw_url and not url else ""}'
        f"<p>{link}</p>"
        "</article>"
    )


def _render_section(key: str, items: list[dict], page_index: int, mobile: bool = False) -> str:
    label, lead = SECTION_LABELS.get(key, EXECUTION_LABELS.get(key, (key, "")))
    kind = "sources" if key == "sources" else "content"
    cards = (
        "".join(_render_source_card(item) for item in items)
        if kind == "sources"
        else "".join(_render_content_card(item) for item in items)
    )
    density = "compact" if key in EXECUTION_KEYS or kind == "sources" else "wide"
    page_attr = f' data-page="{page_index}"' if mobile else ""
    return (
        f'<section id="{key}" class="section-block" data-kind="{kind}" data-density="{density}"{page_attr}>'
        '<div class="section-head">'
        f"<h2>{html.escape(label)}</h2>"
        f'<p class="section-lead">{html.escape(lead)}</p>'
        "</div>"
        f'<div class="section-body">{cards}</div>'
        "</section>"
    )


def _render_nav() -> str:
    items = []
    for key in SECTION_ORDER:
        label = SECTION_LABELS.get(key, EXECUTION_LABELS.get(key, (key, "")))[0]
        items.append(f'<a href="#{key}">{html.escape(label)}</a>')
    return "".join(items)


def _render_meta_chips(payload: dict) -> str:
    meta = payload.get("meta", {})
    chips = [
        ("攻略版本", _safe_text(meta.get("checked_at")) or "待补充"),
        ("来源数量", str(meta.get("source_count", 0))),
        ("分享形态", "多文件 + 单文件 + ZIP"),
    ]
    return "".join(
        f'<span class="meta-chip"><strong>{html.escape(label)}</strong>{html.escape(value)}</span>'
        for label, value in chips
    )


def _build_summary(payload: dict) -> str:
    meta = payload.get("meta", {})
    overview = _safe_list(payload.get("sections", {}).get("overview"))
    if overview:
        first = overview[0]
        summary = _safe_text(first.get("summary"))
        if summary:
            return summary
    title = _safe_text(meta.get("title"))
    if title:
        return f"围绕 {title} 输出可分享的桌面页、移动页和离线包。"
    return "围绕当前研究结果输出可分享的桌面页、移动页和离线包。"


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
    for source in _safe_list(payload.get("sections", {}).get("sources")):
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


def render_site(payload: dict, output_root: Path) -> Path:
    meta = payload.get("meta", {})
    slug = _safe_text(meta.get("trip_slug")) or "travel-guide"
    title = _safe_text(meta.get("title")) or slug
    summary = _build_summary(payload)
    section_html = []
    sections = payload.get("sections", {})
    execution = payload.get("execution", {})

    for index, key in enumerate(SECTION_ORDER, start=1):
        if key in SECTION_KEYS:
            items = _safe_list(sections.get(key))
        else:
            items = _safe_list(execution.get(key))
        section_html.append(_render_section(key, items, page_index=index, mobile=False))

    desktop_html = _load_template("desktop-index.html")
    mobile_html = _load_template("mobile-index.html")
    section_content = "\n".join(section_html) + '\n<p class="footer-note">下单前请再到官方渠道复核实时价格、班次与规则。</p>'
    mobile_content = "\n".join(
        _render_section(
            key,
            _safe_list(sections.get(key) if key in SECTION_KEYS else execution.get(key)),
            page_index=index,
            mobile=True,
        )
        for index, key in enumerate(SECTION_ORDER, start=1)
    )
    mobile_content += '\n<p class="footer-note">移动页同样适合离线打开与即时转发。</p>'

    replacements = {
        "{{TITLE}}": html.escape(title),
        "{{SUMMARY}}": html.escape(summary),
        "{{META_CHIPS}}": _render_meta_chips(payload),
        "{{NAV_ITEMS}}": _render_nav(),
        "{{SECTION_CONTENT}}": section_content,
    }
    desktop_output = desktop_html
    for key, value in replacements.items():
        desktop_output = desktop_output.replace(key, value)

    mobile_output = mobile_html
    for key, value in replacements.items():
        mobile_output = mobile_output.replace(key, mobile_content if key == "{{SECTION_CONTENT}}" else value)

    trip_root = output_root / "trips" / slug
    desktop_dir = trip_root / "desktop"
    mobile_dir = trip_root / "mobile"
    assets_dir = trip_root / "assets"
    notes_dir = trip_root / "notes"
    for path in [desktop_dir, mobile_dir, assets_dir, notes_dir]:
        path.mkdir(parents=True, exist_ok=True)

    (desktop_dir / "index.html").write_text(desktop_output, encoding="utf-8")
    (mobile_dir / "index.html").write_text(mobile_output, encoding="utf-8")
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
