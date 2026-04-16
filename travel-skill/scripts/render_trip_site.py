from pathlib import Path
import argparse
import html
import json
import sys
from urllib.parse import urlsplit

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import TEMPLATE_IDS, TEMPLATE_LABELS, TEMPLATE_SECTIONS


RENDER_TEMPLATES = TEMPLATE_IDS
DAILY_OVERVIEW_SECTIONS = ["days", "wearing", "transport", "alerts"]


SECTION_META = {
    "days": ("每日安排", "先看按天拆分后的主线节奏。"),
    "wearing": ("穿衣与装备", "把当月体感和必备物品放在一起看。"),
    "transport": ("交通安排", "优先确认当天主交通和接驳方式。"),
    "alerts": ("温馨提示", "把预约、排队和天气提醒单独列出。"),
    "recommended_route": ("最推荐路线", "把最省心的一条执行线放在最前。"),
    "route_options": ("多方案交通决策", "默认高铁优先，长距离同步给空铁联运。"),
    "clothing_guide": ("穿衣与装备指南", "把城市体感、景区体感和装备建议放在一起。"),
    "attractions": ("深度景点解析", "聚焦玩法、费用、预约与停留时长。"),
    "transport_details": ("交通细节", "把车次、接驳、打车和换乘拆开写清楚。"),
    "food_by_city": ("地道美食图谱", "按城市整理详细店铺卡片与备选。"),
    "tips": ("温馨提示", "把节奏、排队、天气和复核提醒集中呈现。"),
    "sources": ("信息来源", "保留可追溯来源，方便二次核对。"),
}
EDITORIAL_THEME = {
    "font": '"Source Han Serif SC", "STSong", serif',
    "accent": "#8c4b2e",
    "bg": "#f3ede3",
    "surface": "#fffaf4",
    "ink": "#241d16",
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


def _render_media_image(entry: dict) -> str:
    if not isinstance(entry, dict):
        return ""
    image_url = _safe_href(entry.get("image_url"))
    if not image_url:
        return ""
    alt = _safe_text(entry.get("image_hint")) or "旅行插图"
    return (
        '<figure class="media-figure">'
        f'<img class="media-image" src="{html.escape(image_url, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy" />'
        "</figure>"
    )


def _guide_content_script(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"window.__TRAVEL_GUIDE__ = {data};\n"


def _style_override_css(device: str) -> str:
    theme = EDITORIAL_THEME
    mobile_grid = "1fr" if device == "mobile" else "repeat(2, minmax(0, 1fr))"
    return f"""
    :root {{
      --theme-bg: {theme['bg']};
      --theme-surface: {theme['surface']};
      --theme-ink: {theme['ink']};
      --theme-accent: {theme['accent']};
      --theme-accent-soft: {theme['accent']}1f;
      --theme-line: {theme['ink']}1a;
      --theme-shadow: 0 18px 42px {theme['ink']}24;
    }}
    body {{
      font-family: {theme['font']};
    }}
    .page-shell {{
      width: min(1180px, calc(100% - 28px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }}
    .hero,
    .hero-media,
    .section-block,
    .card,
    .source-card {{
      background: var(--theme-surface);
      border: 1px solid var(--theme-line);
      border-radius: 28px;
      box-shadow: var(--theme-shadow);
    }}
    .hero,
    .hero-media,
    .section-block {{
      padding: 24px;
      margin-bottom: 18px;
    }}
    .hero-summary,
    .section-lead,
    .card-summary,
    .source-meta,
    .source-url,
    .empty-text {{
      color: color-mix(in srgb, var(--theme-ink) 68%, white);
    }}
    .content-shell {{
      display: grid;
      gap: 18px;
    }}
    .section-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 12px;
      position: sticky;
      top: 12px;
      background: rgba(255, 255, 255, 0.82);
      backdrop-filter: blur(12px);
      border-radius: 18px;
      border: 1px solid var(--theme-line);
    }}
    .section-nav a,
    .meta-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      border-radius: 999px;
      text-decoration: none;
      border: 1px solid var(--theme-line);
      background: rgba(255, 255, 255, 0.74);
      color: inherit;
    }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }}
    .section-head {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 14px;
    }}
    .section-body {{
      display: grid;
      grid-template-columns: {mobile_grid};
      gap: 14px;
    }}
    .card,
    .source-card {{
      padding: 18px;
    }}
    .timeline-stack {{
      display: grid;
      gap: 18px;
      position: relative;
      padding-left: 22px;
    }}
    .timeline-stack::before {{
      content: "";
      position: absolute;
      left: 8px;
      top: 0;
      bottom: 0;
      width: 2px;
      background: var(--theme-line);
    }}
    .timeline-card {{
      position: relative;
      padding: 18px 18px 18px 22px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.78);
      border: 1px solid var(--theme-line);
      box-shadow: var(--theme-shadow);
    }}
    .timeline-card::before {{
      content: "";
      position: absolute;
      left: -20px;
      top: 24px;
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: var(--theme-accent);
      border: 3px solid var(--theme-surface);
      box-shadow: 0 0 0 1px var(--theme-line);
    }}
    .card-points {{
      list-style: none;
      padding: 0;
      margin: 14px 0 0;
      display: grid;
      gap: 10px;
    }}
    .card-points li {{
      padding: 10px 12px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.7);
    }}
    .transport-matrix {{
      margin-top: 14px;
      display: grid;
      gap: 10px;
    }}
    .transport-row {{
      display: grid;
      gap: 6px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.78);
      border: 1px solid var(--theme-line);
    }}
    .transport-row strong {{
      color: var(--theme-accent);
    }}
    .transport-meta {{
      margin: 0;
      font-size: 14px;
      color: color-mix(in srgb, var(--theme-ink) 76%, white);
    }}
    .transport-access-card,
    .food-group-card {{
      position: relative;
      overflow: hidden;
      border-width: 1px;
    }}
    .transport-access-card {{
      background: linear-gradient(180deg, rgba(154, 75, 47, 0.09), rgba(255, 255, 255, 0.9));
    }}
    .food-group-card {{
      background: linear-gradient(180deg, rgba(154, 75, 47, 0.06), rgba(255, 250, 244, 0.98));
    }}
    .transport-access-card::before,
    .food-group-card::before {{
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background: var(--theme-accent);
    }}
    .card-source-meta {{
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px dashed var(--theme-line);
      display: grid;
      gap: 6px;
    }}
    .card-source-line {{
      margin: 0;
      font-size: 13px;
      color: color-mix(in srgb, var(--theme-ink) 70%, white);
      word-break: break-all;
    }}
    .card-inline-media {{
      margin-top: 14px;
      display: grid;
      gap: 8px;
    }}
    .card-comment-strip {{
      margin-top: 14px;
      padding: 14px 16px;
      border-radius: 18px;
      background: var(--theme-accent-soft);
      border: 1px solid var(--theme-line);
      display: grid;
      gap: 10px;
    }}
    .card-comment-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 8px;
    }}
    .card-comment-list li {{
      padding: 10px 12px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.76);
    }}
    .card-inline-media .media-label {{
      margin: 0;
    }}
    .media-note {{
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.62);
      border: 1px solid var(--theme-line);
      margin-bottom: 12px;
    }}
    .media-figure {{
      margin: 0 0 12px;
    }}
    .media-image {{
      width: 100%;
      height: auto;
      display: block;
      border-radius: 18px;
      aspect-ratio: 16 / 10;
      object-fit: cover;
      border: 1px solid var(--theme-line);
      box-shadow: var(--theme-shadow);
    }}
    .media-label,
    .eyebrow {{
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 12px;
      color: var(--theme-accent);
    }}
    h1, h2, h3, h4 {{
      margin: 0;
    }}
    h1 {{
      font-size: clamp(34px, 5vw, 58px);
      line-height: 1.08;
    }}
    a {{
      color: inherit;
    }}
    .source-url {{
      word-break: break-all;
    }}
    @media (max-width: 900px) {{
      .section-body {{
        grid-template-columns: 1fr;
      }}
    }}
    """


def _meta_chips(meta: dict) -> str:
    traveler_constraints = meta.get("traveler_constraints") if isinstance(meta.get("traveler_constraints"), dict) else {}
    chips = [
        ("核对日期", _safe_text(meta.get("checked_at")) or "待补充"),
        ("来源数量", str(meta.get("source_count", 0))),
    ]
    if isinstance(meta.get("transport_rule"), dict):
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


def _render_transport_matrix(rows: list[dict]) -> str:
    valid_rows = [row for row in rows if isinstance(row, dict)]
    if not valid_rows:
        return ""
    cards = []
    for row in valid_rows:
        cards.append(
            '<div class="transport-row">'
            f"<strong>{_escape(row.get('name') or '交通方案')}</strong>"
            f'<p class="transport-meta">{_escape(row.get("schedule"))}</p>'
            f'<p class="transport-meta">{_escape(row.get("price"))}</p>'
            f'<p class="transport-meta">{_escape(row.get("duration"))}</p>'
            f'<p class="transport-meta">{_escape(row.get("notes"))}</p>'
            "</div>"
        )
    return '<div class="transport-matrix">' + "".join(cards) + "</div>"


def _render_card_source_meta(meta: dict) -> str:
    if not isinstance(meta, dict):
        return ""
    raw_url = _safe_text(meta.get("url"))
    safe_url = _safe_href(raw_url)
    lines = [
        f"site: {_safe_text(meta.get('site')) or 'unknown'}",
        f"checked_at: {_safe_text(meta.get('checked_at')) or 'unknown'}",
        f"title: {_safe_text(meta.get('title')) or 'unknown'}",
    ]
    if safe_url:
        lines.append(safe_url)
    elif raw_url:
        lines.append(raw_url)
    return '<div class="card-source-meta">' + "".join(
        f'<p class="card-source-line">{_escape(line)}</p>' for line in lines if _safe_text(line)
    ) + "</div>"


def _render_card_media(media: dict) -> str:
    if not isinstance(media, dict):
        return ""
    image_url = _safe_href(media.get("image_url"))
    if not image_url:
        return ""
    hint = _safe_text(media.get("image_hint")) or "卡片配图"
    source_ref = _safe_text(media.get("source_ref"))
    source_kind = _safe_text(media.get("image_source_kind"))
    return (
        '<div class="card-inline-media">'
        f"{_render_media_image({'image_url': image_url, 'image_hint': hint})}"
        f'<p class="media-label">{_escape(hint)}</p>'
        f'<p class="card-source-line">{_escape(source_ref or source_kind)}</p>'
        "</div>"
    )


def _render_comment_highlights(items: list[str]) -> str:
    comments = [item for item in items if isinstance(item, str) and item.strip()]
    if not comments:
        return ""
    return (
        '<div class="card-comment-strip">'
        '<p class="media-label">评论摘录</p>'
        + '<ul class="card-comment-list">'
        + "".join(f"<li>{_escape(comment)}</li>" for comment in comments)
        + "</ul>"
        + "</div>"
    )


def _render_content_card(item: dict) -> str:
    matrix_html = _render_transport_matrix(_safe_list(item.get("transport_matrix")))
    card_media_html = _render_card_media(item.get("card_media"))
    comment_html = _render_comment_highlights(_safe_list(item.get("comment_highlights")))
    source_meta_html = _render_card_source_meta(item.get("source_meta"))
    card_kind = _safe_text(item.get("card_kind"))
    extra_class = ""
    if card_kind == "transport-access":
        extra_class = " transport-access-card"
    elif card_kind == "food-group":
        extra_class = " food-group-card"
    return (
        f'<article class="card{extra_class}">'
        f"<h3>{_escape(item.get('title') or '内容条目')}</h3>"
        f'<p class="card-summary">{_escape(item.get("summary"))}</p>'
        f"{card_media_html}"
        f"{comment_html}"
        f"{_render_points(_safe_list(item.get('points')))}"
        f"{matrix_html}"
        f"{source_meta_html}"
        "</article>"
    )


def _render_timeline_cards(items: list[dict]) -> str:
    cards = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cards.append(
            '<article class="timeline-card">'
            f"<h3>{_escape(item.get('title') or '行程节点')}</h3>"
            f'<p class="card-summary">{_escape(item.get("summary"))}</p>'
            f"{_render_points(_safe_list(item.get('points')))}"
            "</article>"
        )
    return '<div class="timeline-stack">' + "".join(cards) + "</div>"


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
        if (
            isinstance(item, dict)
            and _safe_text(item.get("section")) == section_id
            and _safe_text(item.get("publish_state")) != "text-citation-only"
        ):
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
            f'{_render_media_image(entry)}'
            '<p class="media-label">参考画面</p>'
            f"<h4>{_escape(entry.get('image_hint') or '待补充画面')}</h4>"
            f'<p>{_escape(entry.get("source_ref") or "")}</p>'
            "</aside>"
        )
    return "".join(blocks)


def _render_hero_media(meta: dict, image_plan: dict, template_id: str) -> str:
    cover = image_plan.get("cover") if isinstance(image_plan, dict) and isinstance(image_plan.get("cover"), dict) else {}
    if _safe_text(cover.get("publish_state")) == "text-citation-only":
        return ""
    detail_lines = []
    if cover.get("image_hint"):
        detail_lines.append(str(cover.get("image_hint")))
    if isinstance(meta.get("transport_rule"), dict):
        detail_lines.append(f"距离规则：{meta['transport_rule'].get('long_distance')}")
    if not detail_lines and not _safe_href(cover.get("image_url")):
        return ""
    return (
        '<div class="hero-media">'
        f"{_render_media_image(cover)}"
        f"<p class=\"eyebrow\">{_escape(TEMPLATE_LABELS.get(template_id, template_id))}</p>"
        + "".join(f"<p>{_escape(line)}</p>" for line in detail_lines)
        + "</div>"
    )


def _render_section(section_id: str, title: str, lead: str, items: list[dict], image_plan: dict, source_mode: bool) -> str:
    media = _render_media_block(image_plan, section_id)
    if source_mode:
        cards = "".join(_render_source_card(item) for item in items)
    elif section_id == "days":
        cards = _render_timeline_cards(items)
    else:
        cards = "".join(_render_content_card(item) for item in items)
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


def _group_sources(payload: dict) -> list[tuple[str, list[tuple[str, list[dict]]]]]:
    grouped: dict[str, dict[str, list[dict]]] = {}
    for source in _safe_list(payload.get("sources")):
        if not isinstance(source, dict):
            continue
        site = _safe_text(source.get("site")) or "unknown"
        topic = _safe_text(source.get("topic")) or "unknown"
        grouped.setdefault(site, {}).setdefault(topic, []).append(source)
    return [
        (site, [(topic, grouped[site][topic]) for topic in sorted(grouped[site])])
        for site in sorted(grouped)
    ]


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
    for site, topics in _group_sources(payload):
        lines.append(f"## {site}")
        lines.append("")
        for topic, items in topics:
            lines.append(f"### {topic}")
            lines.append("")
            for source in items:
                lines.extend(
                    [
                        f"- title: {_safe_text(source.get('title')) or '待补充来源'}",
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
    sections = []
    for site, topics in _group_sources(payload):
        for topic, items in topics:
            cards = "".join(_render_source_card(source) for source in items)
            sections.append(
                '<section class="section-block">'
                '<div class="section-head">'
                f"<h2>{_escape(site)} · {_escape(topic)}</h2>"
                '<p class="section-lead">按站点、主题、checked_at 与 time-sensitive 组织来源。</p>'
                "</div>"
                f'<div class="section-body">{cards}</div>'
                "</section>"
            )
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_escape(_safe_text(meta.get('title')) or '旅行攻略')} · 来源说明</title>
    <link rel="stylesheet" href="../assets/base.css" />
    <style>{_style_override_css('desktop')}</style>
  </head>
  <body data-page="sources" data-template="sources">
    <div class="page-shell style-reference">
      <header class="hero">
        <p class="eyebrow">来源说明</p>
        <h1>{_escape(_safe_text(meta.get('title')) or '旅行攻略')}</h1>
        <p class="hero-summary">按 site、topic、checked_at 和 time-sensitive 组织的来源页。</p>
      </header>
      <main class="content-shell">{''.join(sections)}</main>
    </div>
  </body>
</html>
"""


def _section_items(payload: dict, section_id: str) -> list[dict]:
    outputs = payload.get("outputs") if isinstance(payload.get("outputs"), dict) else {}
    daily = outputs.get("daily-overview") if isinstance(outputs.get("daily-overview"), dict) else {}
    recommended = outputs.get("recommended") if isinstance(outputs.get("recommended"), dict) else {}
    comprehensive = outputs.get("comprehensive") if isinstance(outputs.get("comprehensive"), dict) else {}
    if section_id in {"days", "wearing", "transport", "alerts"}:
        return _safe_list(daily.get(section_id))
    if section_id == "sources":
        return _safe_list(payload.get("sources")) or _safe_list(recommended.get("sources")) or _safe_list(daily.get("sources"))
    return _safe_list(recommended.get(section_id)) or _safe_list(comprehensive.get(section_id))


def _render_section_block(payload: dict, section_id: str, image_plan: dict) -> str:
    title, lead = SECTION_META[section_id]
    return _render_section(
        section_id,
        title,
        lead,
        _section_items(payload, section_id),
        image_plan,
        section_id == "sources",
    )


def _apply_template(replacements: dict[str, str]) -> str:
    template_html = _load_asset("template-editorial.html")
    output = template_html
    for key, value in replacements.items():
        output = output.replace(f"{{{{ {key} }}}}", value)
    return output


def _render_research_report(report: dict) -> str:
    theme_blocks = [block for block in _safe_list(report.get("theme_blocks")) if isinstance(block, dict)]
    if not theme_blocks:
        theme_blocks = [
            {
                "title": "dual time layer",
                "recent": ["latest status pending"],
                "historical": ["historical experience pending"],
            }
        ]
    coverage_cards = "".join(
        f"<li><strong>{_escape(item.get('site'))}</strong> · {_escape(item.get('coverage_status'))}</li>"
        for item in _safe_list(report.get("coverage_overview"))
        if isinstance(item, dict)
    )
    quick_findings = "".join(
        f"<li>{_escape(point)}</li>"
        for point in _safe_list(report.get("quick_findings"))
    )
    theme_cards = "".join(
        (
            '<section class="section-block">'
            f"<div class='section-head'><h2>{_escape(block.get('title'))}</h2></div>"
            '<div class="section-body">'
            f"<article class='card'><h3>最新现状</h3><ul class='card-points'>{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(block.get('recent')))}</ul></article>"
            f"<article class='card'><h3>去年同期经验</h3><ul class='card-points'>{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(block.get('historical')))}</ul></article>"
            "</div></section>"
        )
        for block in theme_blocks
    )
    evidence_cards = "".join(
        (
            '<article class="card">'
            f"<p class='eyebrow'>{_escape(card.get('platform'))} · {_escape(card.get('time_layer'))}</p>"
            f"<h3>{_escape(card.get('title'))}</h3>"
            f"<p class='card-summary'>{_escape(card.get('summary'))}</p>"
            "</article>"
        )
        for card in _safe_list(report.get("evidence_cards"))
        if isinstance(card, dict)
    )
    gap_items = "".join(
        f"<li><strong>{_escape(item.get('site'))}</strong> · {_escape(item.get('reason'))}</li>"
        for item in _safe_list(report.get("gaps"))
        if isinstance(item, dict)
    )
    return (
        '<section class="section-block"><div class="section-head"><h2>覆盖总览</h2></div>'
        f'<ul class="card-points">{coverage_cards}</ul></section>'
        '<section class="section-block"><div class="section-head"><h2>快速结论</h2></div>'
        f'<ul class="card-points">{quick_findings}</ul></section>'
        f"{theme_cards}"
        '<section class="section-block"><div class="section-head"><h2>证据卡片</h2></div>'
        f'<div class="section-body">{evidence_cards}</div></section>'
        '<section class="section-block"><div class="section-head"><h2>缺口与失败</h2></div>'
        f'<ul class="card-points">{gap_items}</ul></section>'
        '<section class="section-block"><div class="section-head"><h2>来源附录</h2></div><div id="sources-root"></div></section>'
    )


def _render_research_report_media_aware(report: dict) -> str:
    theme_blocks = [block for block in _safe_list(report.get("theme_blocks")) if isinstance(block, dict)]
    if not theme_blocks:
        theme_blocks = [
            {
                "title": "dual time layer",
                "recent": ["latest status pending"],
                "historical": ["historical experience pending"],
            }
        ]

    coverage_cards = "".join(
        f"<li><strong>{_escape(item.get('site'))}</strong> 路 coverage_status: {_escape(item.get('coverage_status'))}</li>"
        for item in _safe_list(report.get("coverage_overview"))
        if isinstance(item, dict)
    )
    quick_findings = "".join(f"<li>{_escape(point)}</li>" for point in _safe_list(report.get("quick_findings")))
    theme_cards = "".join(
        (
            '<section class="section-block">'
            f"<div class='section-head'><h2>{_escape(block.get('title'))}</h2></div>"
            '<div class="section-body">'
            f"<article class='card'><h3>最新现状</h3><ul class='card-points'>{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(block.get('recent')))}</ul></article>"
            f"<article class='card'><h3>去年同期经验</h3><ul class='card-points'>{''.join(f'<li>{_escape(point)}</li>' for point in _safe_list(block.get('historical')))}</ul></article>"
            "</div></section>"
        )
        for block in theme_blocks
    )
    evidence_cards = "".join(
        (
            '<article class="card">'
            f"<p class='eyebrow'>{_escape(card.get('platform'))} 路 {_escape(card.get('time_layer'))}</p>"
            f"<h3>{_escape(card.get('title'))}</h3>"
            f"<p class='card-summary'>{_escape(card.get('summary'))}</p>"
            + (
                f"<p class='card-source-line'>coverage_status: {_escape(card.get('coverage_status'))}</p>"
                if _safe_text(card.get("coverage_status"))
                else ""
            )
            + "</article>"
        )
        for card in _safe_list(report.get("evidence_cards"))
        if isinstance(card, dict)
    )
    selected_frame_cards = "".join(
        (
            '<article class="card selected-frame">'
            f"<p class='eyebrow'>{_escape(frame.get('platform'))} 路 {_escape(frame.get('time_layer'))}</p>"
            f"<h3>{_escape(frame.get('title') or 'Selected Frame')}</h3>"
            f"{_render_media_image(frame)}"
            f"<p class='card-summary'>{_escape(frame.get('image_hint') or frame.get('summary'))}</p>"
            f"<p class='card-source-line'>coverage_status: {_escape(frame.get('coverage_status'))}</p>"
            f"<p class='card-source-line'>evidence_score: {_escape(frame.get('evidence_score'))}</p>"
            "</article>"
        )
        for frame in _safe_list(report.get("selected_frames"))
        if isinstance(frame, dict)
    )
    gap_items = "".join(
        f"<li><strong>{_escape(item.get('site'))}</strong> 路 {_escape(item.get('reason'))}</li>"
        for item in _safe_list(report.get("gaps"))
        if isinstance(item, dict)
    )
    media_section = (
        '<section class="section-block"><div class="section-head"><h2>媒体证据</h2></div>'
        f'<div class="section-body">{selected_frame_cards}</div></section>'
        if selected_frame_cards
        else ""
    )
    return (
        '<section class="section-block"><div class="section-head"><h2>覆盖总览</h2></div>'
        f'<ul class="card-points">{coverage_cards}</ul></section>'
        '<section class="section-block"><div class="section-head"><h2>快速结论</h2></div>'
        f'<ul class="card-points">{quick_findings}</ul></section>'
        f"{theme_cards}"
        '<section class="section-block"><div class="section-head"><h2>证据卡片</h2></div>'
        f'<div class="section-body">{evidence_cards}</div></section>'
        f"{media_section}"
        '<section class="section-block"><div class="section-head"><h2>缺口与失败</h2></div>'
        f'<ul class="card-points">{gap_items}</ul></section>'
        '<section class="section-block"><div class="section-head"><h2>来源附录</h2></div><div id="sources-root"></div></section>'
    )


def render_trip_site(payload: dict, guide_root: Path) -> Path:
    guide_root.mkdir(parents=True, exist_ok=True)
    notes_dir = guide_root / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    title = _safe_text(payload.get("title"))
    if not title and isinstance(payload.get("meta"), dict):
        title = _safe_text(payload["meta"].get("title"))
    if not title:
        title = _safe_text(payload.get("trip_slug")) or "旅行研究报告"

    report = payload.get("research_report") if isinstance(payload.get("research_report"), dict) else {}
    body_html = _render_research_report_media_aware(report)
    html_text = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_escape(title)} · 研究底稿</title>
    <style>{_style_override_css('desktop')}</style>
  </head>
  <body data-page="research-report">
    <div class="page-shell">
      <header class="hero">
        <p class="eyebrow">研究底稿</p>
        <h1>{_escape(title)}</h1>
        <p class="hero-summary">按覆盖、双时间层、证据卡和缺口组织的研究报告。</p>
      </header>
      <main class="content-shell">{body_html}</main>
    </div>
  </body>
</html>
"""
    guide_root.joinpath("research-report.html").write_text(html_text, encoding="utf-8")
    notes_dir.joinpath("sources.md").write_text("# 来源附录\n", encoding="utf-8")
    notes_dir.joinpath("sources.html").write_text("<!doctype html><html lang='zh-CN'><body><h1>来源附录</h1></body></html>", encoding="utf-8")
    return guide_root


def _render_template_page(payload: dict, template_id: str, device: str) -> str:
    meta = payload.get("meta", {})
    slug = _safe_text(meta.get("trip_slug")) or "travel-guide"
    title = _safe_text(meta.get("title")) or "旅行攻略"
    image_plan = payload.get("image_plan") if isinstance(payload.get("image_plan"), dict) else {}
    section_ids = TEMPLATE_SECTIONS[template_id]
    nav_items = "".join(
        f'<a href="#{section_id}">{_escape(SECTION_META[section_id][0])}</a>'
        for section_id in section_ids
    )
    summary = _safe_text(
        (payload.get("outputs", {}).get("daily-overview", {}) if isinstance(payload.get("outputs"), dict) else {}).get("summary")
    ) or f"{title} · {TEMPLATE_LABELS.get(template_id, template_id)}"
    hero_inner = (
        f'<p class="eyebrow">旅行攻略</p>'
        f"<h1>{_escape(title)}</h1>"
        f'<p class="layer-title">{_escape(TEMPLATE_LABELS.get(template_id, template_id))}</p>'
        f'<p class="hero-summary">{_escape(summary)}</p>'
        f'<div class="meta-row">{_meta_chips(meta)}</div>'
        f'{_render_hero_media(meta, image_plan, template_id)}'
    )
    replacements = {
        "hero": hero_inner,
        "daily_overview": "".join(
            _render_section_block(payload, section_id, image_plan)
            for section_id in DAILY_OVERVIEW_SECTIONS
        ),
        "recommended_route": _render_section_block(payload, "recommended_route", image_plan) if "recommended_route" in section_ids else "",
        "route_options": _render_section_block(payload, "route_options", image_plan) if "route_options" in section_ids else "",
        "clothing_guide": _render_section_block(payload, "clothing_guide", image_plan) if "clothing_guide" in section_ids else "",
        "attractions": _render_section_block(payload, "attractions", image_plan) if "attractions" in section_ids else "",
        "transport_details": _render_section_block(payload, "transport_details", image_plan) if "transport_details" in section_ids else "",
        "food_by_city": _render_section_block(payload, "food_by_city", image_plan) if "food_by_city" in section_ids else "",
        "tips": _render_section_block(payload, "tips", image_plan) if "tips" in section_ids else "",
        "sources": _render_section_block(payload, "sources", image_plan) if "sources" in section_ids else "",
    }
    body_html = _apply_template(replacements)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_escape(title)} · {_escape(TEMPLATE_LABELS.get(template_id, template_id))}</title>
    <link rel="stylesheet" href="../../assets/base.css" />
    <style>{_style_override_css(device)}</style>
  </head>
  <body data-device="{_escape(device)}" data-template="{_escape(template_id)}" data-trip="{_escape(slug)}">
    <div class="page-shell template-{_escape(template_id)} device-{_escape(device)}">
      <nav class="section-nav">{nav_items}</nav>
      {body_html}
    </div>
    <script src="../../assets/guide-content.js"></script>
    <script src="../../assets/render-guide.js"></script>
  </body>
</html>
"""


def render_site(payload: dict, output_root: Path, style: str = "all") -> Path:
    meta = payload.get("meta", {})
    slug = _safe_text(meta.get("trip_slug")) or "travel-guide"
    guide_root = output_root / "guides" / slug
    assets_dir = guide_root / "assets"
    notes_dir = guide_root / "notes"
    assets_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)

    normalized_style = _safe_text(style) or "all"
    if normalized_style not in {"all", "default", "editorial"}:
        raise ValueError(f"unsupported render style: {normalized_style}")

    selected_templates = ["editorial"]
    for device in ["desktop", "mobile"]:
        for template_id in selected_templates:
            template_dir = guide_root / device / template_id
            template_dir.mkdir(parents=True, exist_ok=True)
            template_dir.joinpath("index.html").write_text(
                _render_template_page(payload, template_id, device),
                encoding="utf-8",
            )

    assets_dir.joinpath("base.css").write_text(_load_asset("base.css"), encoding="utf-8")
    assets_dir.joinpath("render-guide.js").write_text(_load_asset("render-guide.js"), encoding="utf-8")
    assets_dir.joinpath("guide-content.js").write_text(_guide_content_script(payload), encoding="utf-8")
    render_trip_site(payload, guide_root)
    notes_dir.joinpath("sources.md").write_text(_sources_markdown(payload), encoding="utf-8")
    notes_dir.joinpath("sources.html").write_text(_sources_html(payload), encoding="utf-8")
    return guide_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--style", default="all")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    render_site(payload if isinstance(payload, dict) else {}, Path(args.output_root), args.style)


if __name__ == "__main__":
    main()
