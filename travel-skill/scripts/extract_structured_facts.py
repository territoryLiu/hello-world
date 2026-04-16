from pathlib import Path
import argparse
import json


def _fact_to_text(fact) -> str:
    if isinstance(fact, dict):
        if str(fact.get("text", "")).strip():
            return str(fact.get("text"))
        return json.dumps(fact, ensure_ascii=False, sort_keys=True)
    if isinstance(fact, list):
        return json.dumps(fact, ensure_ascii=False)
    return str(fact or "")


def _safe_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_list(value) -> list:
    return value if isinstance(value, list) else []


def _schema_for_site(site: str) -> str:
    if site == "xiaohongshu":
        return "xiaohongshu-note-v1"
    if site in {"douyin", "bilibili"}:
        return "video-post-v1"
    if site in {"dianping", "meituan"}:
        return "local-listing-v1"
    return "generic-source-v1"


def _normalize_entry(entry: dict) -> dict:
    platform = _safe_text(entry.get("platform"))
    site = _safe_text(entry.get("site")) or platform or "unknown"
    normalized = {
        "place": _safe_text(entry.get("place")),
        "topic": _safe_text(entry.get("topic") or entry.get("category")),
        "platform": platform,
        "site": site,
        "normalized_schema": _schema_for_site(site),
        "source_url": _safe_text(entry.get("source_url") or entry.get("url")),
        "source_title": _safe_text(entry.get("source_title") or entry.get("title")),
        "author": _safe_text(entry.get("author")),
        "publish_time": _safe_text(entry.get("publish_time") or entry.get("published_at")),
        "time_layer": _safe_text(entry.get("time_layer")) or "recent",
        "coverage_status": _safe_text(entry.get("coverage_status")) or "partial",
        "failure_reason": _safe_text(entry.get("failure_reason")),
        "missing_fields": _safe_list(entry.get("missing_fields")),
    }
    if site == "xiaohongshu":
        normalized.update(
            {
                "summary": _safe_text(entry.get("summary")),
                "page_body_full": _safe_text(entry.get("page_body_full")),
                "comment_threads_full": _safe_list(entry.get("comment_threads_full")),
                "comment_sample_size": entry.get("comment_sample_size") or len(_safe_list(entry.get("comment_threads_full"))),
                "comment_highlights": _safe_list(entry.get("comment_highlights")),
                "image_candidates": _safe_list(entry.get("image_candidates")),
            }
        )
    elif site in {"douyin", "bilibili"}:
        normalized.update(
            {
                "summary": _safe_text(entry.get("summary") or entry.get("page_text")),
                "comment_highlights": _safe_list(entry.get("comment_highlights")),
                "transcript_segments": _safe_list(entry.get("transcript_segments")),
                "visual_segments": _safe_list(entry.get("visual_segments")),
                "timeline": _safe_list(entry.get("timeline")),
                "shot_candidates": _safe_list(entry.get("shot_candidates")),
                "selected_frames": _safe_list(entry.get("selected_frames")),
                "frame_scores": _safe_list(entry.get("frame_scores")),
            }
        )
    elif site in {"dianping", "meituan"}:
        normalized.update(
            {
                "shop_name": _safe_text(entry.get("shop_name")),
                "address": _safe_text(entry.get("address")),
                "per_capita_range": _safe_text(entry.get("per_capita_range")),
                "recommended_dishes": _safe_list(entry.get("recommended_dishes")),
                "queue_pattern": _safe_text(entry.get("queue_pattern")),
                "review_themes": _safe_list(entry.get("review_themes")),
                "pitfalls": _safe_list(entry.get("pitfalls")),
            }
        )
    else:
        normalized["summary"] = _safe_text(entry.get("summary"))
    return normalized


def extract(payload: dict) -> dict:
    by_place: dict[str, dict[str, list[dict]]] = {}
    facts = []
    knowledge_points = []
    normalized_records = []
    for raw_entry in payload.get("entries", []):
        entry = raw_entry if isinstance(raw_entry, dict) else {}
        place = str(entry.get("place", ""))
        topic = str(entry.get("topic", entry.get("category", "")))
        platform = str(entry.get("platform", ""))
        site = str(entry.get("site", platform or "unknown"))
        source_url = str(entry.get("url", ""))
        checked_at = str(entry.get("checked_at", ""))
        source_type = str(entry.get("source_type", ""))
        source_title = str(entry.get("title", ""))
        time_layer = str(entry.get("time_layer", "recent"))
        normalized_records.append(_normalize_entry(entry))

        raw_facts = entry.get("facts", [])
        if raw_facts is None:
            raw_facts = []
        facts_iterable = raw_facts if isinstance(raw_facts, list) else [raw_facts]

        for fact in facts_iterable:
            text = _fact_to_text(fact).strip()
            if not text:
                continue
            fact_item = {
                "place": place,
                "topic": topic,
                "platform": platform,
                "site": site,
                "text": text,
                "source_url": source_url,
                "checked_at": checked_at,
                "source_type": source_type,
                "source_title": source_title,
                "time_layer": time_layer,
            }
            by_place.setdefault(place, {}).setdefault(topic, []).append(fact_item)
            facts.append(fact_item)
            knowledge_points.append(
                {
                    "place": place,
                    "topic": topic,
                    "time_layer": time_layer,
                    "claim": text,
                    "evidence_refs": [source_url] if source_url else [],
                }
            )
    return {
        "by_place": by_place,
        "facts": facts,
        "knowledge_points": knowledge_points,
        "normalized_records": normalized_records,
        "summary": payload.get("summary", {}),
        "normalized": payload.get("normalized", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    extracted = extract(payload if isinstance(payload, dict) else {})
    output_path.write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
