from pathlib import Path
from html import escape
from urllib.parse import urlparse
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import SITE_COVERAGE_TARGETS as REQUIRED_SITE_MATRIX


def _safe_text(value) -> str:
    return str(value or "").strip()


def _escape_markdown(text: str) -> str:
    escaped = str(text or "")
    replacements = [
        ("\\", "\\\\"),
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ("`", "\\`"),
        ("[", "\\["),
        ("]", "\\]"),
    ]
    for old, new in replacements:
        escaped = escaped.replace(old, new)
    return escaped


def _is_clickable_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalized_facts(category: str, items) -> list[dict]:
    result = []
    iterable = items if isinstance(items, list) else []
    for raw in iterable:
        if isinstance(raw, dict) and "text" in raw:
            result.append(
                {
                    "category": category,
                    "text": _safe_text(raw.get("text")),
                    "source_url": _safe_text(raw.get("source_url")),
                    "checked_at": _safe_text(raw.get("checked_at")),
                    "source_type": _safe_text(raw.get("source_type")),
                    "source_title": _safe_text(raw.get("source_title")),
                    "site": _safe_text(raw.get("site")),
                }
            )
            continue
        if isinstance(raw, dict):
            source_url = _safe_text(raw.get("url"))
            checked_at = _safe_text(raw.get("checked_at"))
            source_type = _safe_text(raw.get("source_type"))
            source_title = _safe_text(raw.get("title"))
            raw_facts = raw.get("facts", [])
            if raw_facts is None:
                raw_facts = []
            fact_list = raw_facts if isinstance(raw_facts, list) else [raw_facts]
            for fact in fact_list:
                result.append(
                    {
                        "category": category,
                        "text": _safe_text(fact),
                        "source_url": source_url,
                        "checked_at": checked_at,
                        "source_type": source_type,
                        "source_title": source_title,
                        "site": _safe_text(raw.get("site")),
                    }
                )
            continue
        result.append(
            {
                "category": category,
                "text": _safe_text(raw),
                "source_url": "",
                "checked_at": "",
                "source_type": "",
                "source_title": "",
                "site": "",
            }
        )
    return [fact for fact in result if fact["text"]]


def _coverage(payload: dict) -> dict:
    by_place = payload.get("by_place", {})
    seen_by_topic = {}
    if not isinstance(by_place, dict):
        return {}
    for topics in by_place.values():
        topic_map = topics if isinstance(topics, dict) else {}
        for topic, items in topic_map.items():
            for fact in _normalized_facts(str(topic), items):
                site = _safe_text(fact.get("site"))
                if not site:
                    continue
                seen_by_topic.setdefault(str(topic), set()).add(site)

    coverage = {}
    for topic, required_sites in REQUIRED_SITE_MATRIX.items():
        seen = sorted(seen_by_topic.get(topic, set()))
        coverage[topic] = {
            "seen": seen,
            "missing": [site for site in required_sites if site not in seen],
        }
    return coverage


def _delivery_gate(payload: dict) -> dict:
    delivery_gate = payload.get("delivery_gate")
    return delivery_gate if isinstance(delivery_gate, dict) else {}


def build_markdown(payload: dict) -> str:
    lines = ["# Research Review Packet", "", "## Verified", ""]
    by_place = payload.get("by_place", {})
    if not isinstance(by_place, dict):
        by_place = {}
    for place, topics in by_place.items():
        lines.append(f"### {_escape_markdown(str(place))}")
        topic_map = topics if isinstance(topics, dict) else {}
        for topic, items in topic_map.items():
            lines.append(f"- topic: {_escape_markdown(str(topic))}")
            facts = _normalized_facts(str(topic), items)
            for fact in facts:
                source_title = _escape_markdown(fact["source_title"] or "Untitled Source")
                source_type = _escape_markdown(fact["source_type"] or "unknown")
                checked_at = _escape_markdown(fact["checked_at"] or "unknown-date")
                text = _escape_markdown(fact["text"])
                lines.append(f"  - {text}")
                lines.append(f"    - source: {source_title} ({source_type})")
                lines.append(f"    - 核对日期: {checked_at}")
                if fact["source_url"]:
                    lines.append(f"    - url: {_escape_markdown(fact['source_url'])}")
        lines.append("")
    lines.extend(["## Site Coverage", ""])
    for topic, data in _coverage(payload).items():
        lines.append(f"- topic: {_escape_markdown(topic)}")
        lines.append(f"  - seen: {', '.join(data['seen']) or '(none)'}")
        lines.append(f"  - missing: {', '.join(data['missing']) or '(none)'}")
    lines.append("")
    delivery_gate = _delivery_gate(payload)
    if delivery_gate:
        lines.extend(["## Delivery Gate", ""])
        lines.append(f"- status: {_escape_markdown(_safe_text(delivery_gate.get('status')) or 'unknown')}")
        failed_checks = delivery_gate.get("failed_checks")
        failed_values = [str(item) for item in failed_checks] if isinstance(failed_checks, list) else []
        lines.append(f"  - failed_checks: {', '.join(failed_values) or '(none)'}")
        checks = delivery_gate.get("checks")
        if isinstance(checks, dict):
            for name, item in checks.items():
                if not isinstance(item, dict):
                    continue
                lines.append(f"- check: {_escape_markdown(str(name))}")
                lines.append(f"  - passed: {_escape_markdown(str(bool(item.get('passed'))).lower())}")
                lines.append(f"  - reason: {_escape_markdown(_safe_text(item.get('reason')) or '(none)')}")
                source = _safe_text(item.get("source"))
                if source:
                    lines.append(f"  - source: {_escape_markdown(source)}")
        lines.append("")
    lines.extend(["## Pending Confirmation", "", "- Recheck volatile transport and weather data before departure.", ""])
    return "\n".join(lines)


def build_html(payload: dict) -> str:
    blocks = []
    by_place = payload.get("by_place", {})
    if not isinstance(by_place, dict):
        by_place = {}
    for place, topics in by_place.items():
        topic_map = topics if isinstance(topics, dict) else {}
        card_lines = [f"<section><h3>{escape(str(place))}</h3>"]
        for topic, items in topic_map.items():
            facts = _normalized_facts(str(topic), items)
            card_lines.append(f"<h4>{escape(str(topic))}</h4><ul>")
            if not facts:
                card_lines.append("<li>(no facts)</li>")
            for fact in facts:
                text = escape(fact["text"])
                source_title = escape(fact["source_title"] or "Untitled Source")
                source_type = escape(fact["source_type"] or "unknown")
                checked_at = escape(fact["checked_at"] or "unknown-date")
                url = fact["source_url"]
                card_lines.append(f"<li><div>{text}</div>")
                card_lines.append(f"<div>{source_title} ({source_type})</div>")
                card_lines.append(f"<div>核对日期: {checked_at}</div>")
                if url:
                    url_text = escape(url)
                    if _is_clickable_url(url):
                        card_lines.append(f"<div><a href=\"{url_text}\">{url_text}</a></div>")
                    else:
                        card_lines.append(f"<div>{url_text}</div>")
                card_lines.append("</li>")
            card_lines.append("</ul>")
        card_lines.append("</section>")
        blocks.append("".join(card_lines))
    delivery_gate_html = ""
    delivery_gate = _delivery_gate(payload)
    if delivery_gate:
        failed_checks = delivery_gate.get("failed_checks")
        failed_values = [escape(str(item)) for item in failed_checks] if isinstance(failed_checks, list) else []
        gate_lines = [
            "<section>",
            "<h2>Delivery Gate</h2>",
            f"<p>status: {escape(_safe_text(delivery_gate.get('status')) or 'unknown')}</p>",
            f"<p>failed_checks: {', '.join(failed_values) or '(none)'}</p>",
        ]
        checks = delivery_gate.get("checks")
        if isinstance(checks, dict):
            gate_lines.append("<ul>")
            for name, item in checks.items():
                if not isinstance(item, dict):
                    continue
                gate_lines.append("<li>")
                gate_lines.append(f"<strong>{escape(str(name))}</strong>")
                gate_lines.append(f"<div>passed: {escape(str(bool(item.get('passed'))).lower())}</div>")
                gate_lines.append(f"<div>reason: {escape(_safe_text(item.get('reason')) or '(none)')}</div>")
                source = _safe_text(item.get("source"))
                if source:
                    gate_lines.append(f"<div>source: {escape(source)}</div>")
                gate_lines.append("</li>")
            gate_lines.append("</ul>")
        gate_lines.append("</section>")
        delivery_gate_html = "".join(gate_lines)
    return """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Research Review Packet</title>
  </head>
  <body>
    <h1>Research Review Packet</h1>
    <h2>Verified</h2>
    {verified}
    {delivery_gate}
    <h2>Pending Confirmation</h2>
    <ul><li>Recheck volatile transport and weather data before departure.</li></ul>
  </body>
</html>
""".replace("{verified}", "".join(blocks)).replace("{delivery_gate}", delivery_gate_html)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        payload = {}
    (output_dir / "research-packet.md").write_text(build_markdown(payload), encoding="utf-8")
    (output_dir / "research-packet.html").write_text(build_html(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
