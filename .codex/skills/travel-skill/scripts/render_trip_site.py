from pathlib import Path
import argparse
import html
import json
from urllib.parse import urlsplit


LAYER_TITLES = {
    "daily-overview": "每日行程速览",
    "recommended": "最推荐攻略",
    "comprehensive": "最全面攻略",
}
SECTION_LABELS = {
    "daily-overview": [
        ("days", "每日安排", "先看按天拆分后的主线节奏。"),
        ("wearing", "穿衣与装备", "把当前月份体感和必备物品放在一起看。"),
        ("transport", "交通安排", "优先确认当天主交通和接驳方式。"),
        ("alerts", "温馨提示", "把预约、排队和天气提醒单独列出。"),
        ("sources", "信息来源", "保留可追溯来源，方便二次核对。"),
    ],
    "recommended": [
        ("recommended_route", "最推荐路线", "把最省心的一条执行线放在最前。"),
        ("route_options", "多方案交通决策", "默认高铁优先，长距离同步给空铁联运。"),
        ("clothing_guide", "穿衣与装备指南", "把城市体感、景区体感和装备建议放在一起。"),
        ("attractions", "深度景点解析", "聚焦玩法、费用、预约与停留时长。"),
        ("transport_details", "交通细节", "把车次、接驳、打车和换乘拆开写清楚。"),
        ("food_by_city", "地道美食图谱", "按城市整理详细店铺卡片与备选。"),
        ("tips", "温馨提示", "把节奏、排队、天气和复核提醒集中呈现。"),
        ("sources", "信息来源", "正文依赖的来源列表与核对时间。"),
    ],
    "comprehensive": [
        ("recommended_route", "最推荐路线", "先看主路线，再按章节展开。"),
        ("route_options", "多方案交通决策", "集中对比高铁优先、空铁联运和备选。"),
        ("clothing_guide", "穿衣与装备指南", "补齐当月气温、体感与装备清单。"),
        ("attractions", "深度景点解析", "完整列出玩法、价格与预约规则。"),
        ("transport_details", "交通细节", "逐段拆开看大交通、接驳和落脚点。"),
        ("food_by_city", "地道美食图谱", "按城市整理店名、地址、招牌菜和排队提示。"),
        ("tips", "温馨提示", "把节奏控制、核对时间和风险提醒写完整。"),
        ("sources", "信息来源", "保留全量来源便于复核。"),
    ],
}
STYLE_LABELS = {
    "default": "Layered Guide",
    "classic": "Classic Print",
    "minimalist": "Minimalist",
    "vintage": "Vintage",
    "zen": "Zen",
    "original": "Original",
}


def _load_asset(name: str) -> str:
    path = Path(__file__).resolve().parents[1] / "assets" / "templates" / name
    return path.read_text(encoding="utf-8")


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
    return raw if parsed.scheme.lower() in {"http", "https"} else ""


def _guide_content_script(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"window.__TRAVEL_GUIDE__ = {data};\n"


def _meta_chips(meta: dict) -> str:
    sample_reference = meta.get("sample_reference") if isinstance(meta.get("sample_reference"), dict) else {}
    traveler_constraints = meta.get("traveler_constraints") if isinstance(meta.get("traveler_constraints"), dict) else {}
    chips = [
        ("核对日期", _safe_text(meta.get("checked_at")) or "待补充"),
        ("来源数量", str(meta.get("source_count", 0))),
    ]
    if sample_reference.get("path"):
        chips.append(("对标样本", _safe_text(sample_reference.get("path"))))
    if meta.get("transport_rule"):
        chips.append(("距离规则", _safe_text(meta["transport_rule"].get("long_distance"))))
    if traveler_constraints.get("requires_accessible_pace"):
        chips.append(("行程节奏", "亲子/长辈友好"))
    return "".join(
        f'<span class="meta-chip"><strong>{_escape(label)}</strong>{_escape(value)}</span>'
        for label, value in chips
    )


def _render_points(points: list[str]) -> str:
    entries = [point for point in points if isinstance(point, str) and point.strip()]
    if not entries:
        return ""
    return '<ul class="card-points">' + "".join(f"<li>{_escape(point)}</li>" for point in entries) + "</ul>"


def _render_content_card(item: dict) -> str:
    return (
        '<article class="card">'
        f"<h3>{_escape(item.get('title') or '内容条目')}</h3>"
        f'<p class="card-summary">{_escape(item.get("summary"))}</p>'
        f"{_render_points(_safe_list(item.get('points')))}"
        "</article>"
    )


def _render_source_card(source: dict) -> str:
    raw_url = _safe_text(source.get("url"))
    safe_url = _safe_href(raw_url)
    link_html = (
        f'<a class="source-url" href="{html.escape(safe_url, quote=True)}" target="_blank" rel="noreferrer noopener">{html.escape(safe_url)}</a>'
        if safe_url
        else '<span class="empty-text">暂无链接</span>'
    )
    meta_lines = [
        f"site: {_safe_text(source.get('site')) or 'unknown'}",
        f"topic: {_safe_text(source.get('topic')) or 'unknown'}",
        f"type: {_safe_text(source.get('type')) or 'unknown'}",
        f"checked_at: {_safe_text(source.get('checked_at')) or 'unknown'}",
        f"time-sensitive: {_safe_text(source.get('time_sensitive')) or 'no'}",
    ]
    if raw_url and not safe_url:
        meta_lines.append(f"raw_url: {raw_url}")
    return (
        '<article class="source-card">'
        f"<h3>{_escape(source.get('title') or '待补充来源')}</h3>"
        + "".join(f'<p class="source-meta">{_escape(line)}</p>' for line in meta_lines)
        + f"<p>{link_html}</p>"
        + "</article>"
    )


def _find_section_media(image_plan: dict, section_id: str) -> list[dict]:
    if not isinstance(image_plan, dict):
        return []
    result = []
    for item in _safe_list(image_plan.get("section_images")):
        if isinstance(item, dict) and _safe_text(item.get("section")) == section_id:
            result.append(item)
    return result


def _render_media_block(image_plan: dict, section_id: str) -> str:
    entries = _find_section_media(image_plan, section_id)
    if not entries:
        return ""
    blocks = []
    for entry in entries:
        blocks.append(
            '<aside class="media-note">'
            '<p class="media-label">参考画面</p>'
            f"<h4>{_escape(entry.get('image_hint') or '待补充画面')}</h4>"
            f'<p>{_escape(entry.get("source_ref") or "")}</p>'
            "</aside>"
        )
    return "".join(blocks)


def _render_hero_media(meta: dict, image_plan: dict, style: str) -> str:
    cover = image_plan.get("cover") if isinstance(image_plan, dict) and isinstance(image_plan.get("cover"), dict) else {}
    sample_reference = meta.get("sample_reference") if isinstance(meta.get("sample_reference"), dict) else {}
    detail_lines = []
    if cover.get("image_hint"):
        detail_lines.append(f"参考画面：{cover.get('image_hint')}")
    if cover.get("source_ref"):
        detail_lines.append(f"来源参考：{cover.get('source_ref')}")
    if sample_reference.get("path"):
        detail_lines.append(f"样本对标：{sample_reference.get('path')}")
    if meta.get("transport_rule"):
        detail_lines.append(f"距离规则：{meta['transport_rule'].get('long_distance')}")
    if not detail_lines:
        return ""
    return (
        '<section class="hero-media">'
        f"<p class=\"eyebrow\">{_escape(STYLE_LABELS.get(style, style.title()))}</p>"
        + "".join(f"<p>{_escape(line)}</p>" for line in detail_lines)
        + "</section>"
    )


def _render_section(section_id: str, title: str, lead: str, items: list[dict], image_plan: dict, source_mode: bool) -> str:
    media = _render_media_block(image_plan, section_id)
    cards = "".join(_render_source_card(item) for item in items) if source_mode else "".join(
        _render_content_card(item) for item in items
    )
    return (
        f'<section id="{section_id}" class="section-block">'
        '<div class="section-head">'
        f"<h2>{_escape(title)}</h2>"
        f'<p class="section-lead">{_escape(lead)}</p>'
        "</div>"
        f"{media}"
        f'<div class="section-body">{cards}</div>'
        "</section>"
    )


def _render_layer_html(payload: dict, layer_name: str, device: str, style: str) -> str:
    meta = payload.get("meta", {})
    layer_payload = payload.get("outputs", {}).get(layer_name, {})
    title = _safe_text(meta.get("title")) or "旅行攻略"
    summary = _safe_text(layer_payload.get("summary")) or f"{title} · {LAYER_TITLES[layer_name]}"
    sources = _safe_list(layer_payload.get("sources")) or _safe_list(payload.get("sources"))
    nav_items = "".join(
        f'<a href="#{section_id}">{_escape(section_title)}</a>'
        for section_id, section_title, _ in SECTION_LABELS[layer_name]
    )
    sections = []
    image_plan = payload.get("image_plan") if isinstance(payload.get("image_plan"), dict) else {}
    for section_id, section_title, lead in SECTION_LABELS[layer_name]:
        items = sources if section_id == "sources" else _safe_list(layer_payload.get(section_id))
        sections.append(_render_section(section_id, section_title, lead, items, image_plan, section_id == "sources"))

    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_escape(title)} · {_escape(LAYER_TITLES[layer_name])}</title>
    <link rel="stylesheet" href="../../assets/base.css" />
  </head>
  <body data-device="{_escape(device)}" data-layer="{_escape(layer_name)}" data-style="{_escape(style)}">
    <div class="page-shell style-{_escape(style)} device-{_escape(device)}">
      <header class="hero">
        <p class="eyebrow">Travel Skill</p>
        <h1>{_escape(title)}</h1>
        <p class="layer-title">{_escape(LAYER_TITLES[layer_name])}</p>
        <p class="hero-summary">{_escape(summary)}</p>
        <div class="meta-row">{_meta_chips(meta)}</div>
      </header>
      {_render_hero_media(meta, image_plan, style)}
      <main class="content-shell">
        <nav class="section-nav">{nav_items}</nav>
        {''.join(sections)}
      </main>
    </div>
    <script src="../../assets/guide-content.js"></script>
    <script src="../../assets/render-guide.js"></script>
  </body>
</html>
"""


def _sources_markdown(payload: dict) -> str:
    meta = payload.get("meta", {})
    lines = [
        f"# {_safe_text(meta.get('title')) or '旅行攻略'} 来源清单",
        "",
        f"- trip_slug: {_safe_text(meta.get('trip_slug'))}",
        f"- checked_at: {_safe_text(meta.get('checked_at'))}",
        f"- source_count: {meta.get('source_count', 0)}",
        "",
    ]
    for source in _safe_list(payload.get("sources")):
        lines.extend(
            [
                f"## {_safe_text(source.get('site')) or 'unknown'} | {_safe_text(source.get('topic')) or 'unknown'} | {_safe_text(source.get('title')) or '待补充来源'}",
                f"- url: {_safe_text(source.get('url')) or '(no url)'}",
                f"- type: {_safe_text(source.get('type')) or 'unknown'}",
                f"- checked_at: {_safe_text(source.get('checked_at')) or 'unknown'}",
                f"- site: {_safe_text(source.get('site')) or 'unknown'}",
                f"- topic: {_safe_text(source.get('topic')) or 'unknown'}",
                f"- time_sensitive: {_safe_text(source.get('time_sensitive')) or 'no'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _sources_html(payload: dict) -> str:
    meta = payload.get("meta", {})
    cards = "".join(_render_source_card(source) for source in _safe_list(payload.get("sources")))
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_escape(_safe_text(meta.get('title')) or '旅行攻略')} · 来源说明</title>
    <link rel="stylesheet" href="../assets/base.css" />
  </head>
  <body data-page="sources" data-style="reference">
    <div class="page-shell style-reference">
      <header class="hero">
        <p class="eyebrow">Travel Skill Sources</p>
        <h1>{_escape(_safe_text(meta.get('title')) or '旅行攻略')}</h1>
        <p class="hero-summary">按 site、topic、checked_at 和 time-sensitive 组织的来源页。</p>
      </header>
      <main class="content-shell">
        <section class="section-block">
          <div class="section-head">
            <h2>来源说明</h2>
            <p class="section-lead">方便二次核实和后续补采。</p>
          </div>
          <div class="section-body">{cards}</div>
        </section>
      </main>
    </div>
  </body>
</html>
"""


def render_site(payload: dict, output_root: Path, style: str = "default") -> Path:
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
            output_dir.joinpath("index.html").write_text(
                _render_layer_html(payload, layer_name, device, style),
                encoding="utf-8",
            )

    assets_dir.joinpath("base.css").write_text(_load_asset("base.css"), encoding="utf-8")
    assets_dir.joinpath("render-guide.js").write_text(_load_asset("render-guide.js"), encoding="utf-8")
    assets_dir.joinpath("guide-content.js").write_text(_guide_content_script(payload), encoding="utf-8")
    notes_dir.joinpath("sources.md").write_text(_sources_markdown(payload), encoding="utf-8")
    notes_dir.joinpath("sources.html").write_text(_sources_html(payload), encoding="utf-8")
    return trip_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--style", default="default")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    render_site(payload if isinstance(payload, dict) else {}, Path(args.output_root), args.style)


if __name__ == "__main__":
    main()
