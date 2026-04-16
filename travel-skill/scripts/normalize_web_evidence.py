from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_video_research_json import build_video_record
from collect_media_candidates import normalize_items as normalize_media_items
from collect_page_evidence import collect as collect_page_evidence
from extract_structured_facts import extract
from merge_sources import merge


VIDEO_SITES = {"douyin", "bilibili"}


def _text(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _list(item: dict, *keys: str) -> list:
    for key in keys:
        value = item.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def _segments(item: dict, *keys: str) -> list:
    for key in keys:
        value = item.get(key)
        if isinstance(value, list) and value:
            return value
        if isinstance(value, dict):
            segments = value.get("segments")
            if isinstance(segments, list) and segments:
                return segments
    return []


def _normalize_images(images: list) -> list[dict]:
    normalized = []
    for raw in images:
        if isinstance(raw, dict):
            url = _text(raw, "url", "image_url", "src")
            if url:
                normalized.append({**raw, "url": url})
        elif isinstance(raw, str) and raw.strip():
            normalized.append({"url": raw.strip()})
    return normalized


def _normalize_comment_highlights(raw_comments: list) -> list:
    if not isinstance(raw_comments, list):
        return []
    if raw_comments and all(isinstance(item, str) for item in raw_comments):
        return [item.strip() for item in raw_comments if item.strip()]
    highlights = []
    for raw in raw_comments:
        if isinstance(raw, dict):
            text = _text(raw, "text", "content")
            if text:
                highlights.append(text)
    return highlights


def canonicalize_entry(raw: dict) -> dict:
    entry = dict(raw if isinstance(raw, dict) else {})
    site = _text(entry, "site", "platform").lower()
    comments = _list(entry, "comment_threads_full", "comments", "comment_threads")
    canonical = {
        **entry,
        "site": site or _text(entry, "site", "platform").lower(),
        "platform": _text(entry, "platform"),
        "source_url": _text(entry, "source_url", "url", "raw_url"),
        "url": _text(entry, "url", "raw_url", "source_url"),
        "source_title": _text(entry, "source_title", "title", "name", "page_title"),
        "title": _text(entry, "title", "name", "page_title", "source_title"),
        "author": _text(entry, "author", "author_name"),
        "publish_time": _text(entry, "publish_time", "published_at", "published_time", "pub_time"),
        "summary": _text(entry, "summary", "description", "desc", "page_text"),
        "page_body_full": _text(entry, "page_body_full", "body", "content_text", "content"),
        "comment_threads_full": comments if comments and any(isinstance(item, dict) for item in comments) else [],
        "comment_highlights": _list(entry, "comment_highlights") or _normalize_comment_highlights(comments),
        "image_candidates": _normalize_images(_list(entry, "image_candidates", "images", "gallery")),
        "transcript_segments": _segments(entry, "transcript_segments", "transcript", "subtitles"),
        "visual_segments": _list(entry, "visual_segments"),
        "timeline": _list(entry, "timeline"),
        "shot_candidates": _list(entry, "shot_candidates", "screenshots", "keyframes"),
        "shop_name": _text(entry, "shop_name", "name", "title"),
        "address": _text(entry, "address", "location", "shop_address"),
        "per_capita_range": _text(entry, "per_capita_range", "price", "price_range"),
        "recommended_dishes": _list(entry, "recommended_dishes", "recommended_items", "recommendations"),
        "review_themes": _list(entry, "review_themes", "review_keywords", "review_tags"),
        "pitfalls": _list(entry, "pitfalls", "review_notes", "warnings"),
    }
    if canonical["comment_threads_full"]:
        canonical["comment_sample_size"] = len(canonical["comment_threads_full"])
    elif isinstance(entry.get("comment_sample_size"), int):
        canonical["comment_sample_size"] = entry["comment_sample_size"]
    else:
        canonical["comment_sample_size"] = len(canonical["comment_highlights"])
    return canonical


def normalize_payload(payload: dict) -> dict:
    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else payload.get("entries")
    raw_items = raw_items if isinstance(raw_items, list) else []
    canonical_entries = [canonicalize_entry(item) for item in raw_items if isinstance(item, dict)]

    page_items = [item for item in canonical_entries if item.get("site") == "xiaohongshu"]
    video_items = [item for item in canonical_entries if item.get("site") in VIDEO_SITES]

    page_evidence = collect_page_evidence({"items": page_items})
    video_records = {"items": [build_video_record(item) for item in video_items]}
    media_candidates = normalize_media_items(canonical_entries)
    merged = merge(canonical_entries)
    structured = extract(
        {
            "entries": merged.get("entries", []),
            "summary": merged.get("summary", {}),
            "normalized": merged.get("normalized", {}),
        }
    )

    return {
        "trip_slug": str(payload.get("trip_slug") or ""),
        "raw_items": canonical_entries,
        "page_evidence": page_evidence,
        "video_records": video_records,
        "media_candidates": media_candidates,
        "merged": merged,
        "structured": structured,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    normalized = normalize_payload(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
