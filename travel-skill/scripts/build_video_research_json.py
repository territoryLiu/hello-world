from pathlib import Path
import argparse
import json


def _list(value):
    return value if isinstance(value, list) else []


def _text(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


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


def build_video_record(item: dict) -> dict:
    site = str(item.get("site") or item.get("platform") or "").strip().lower()
    normalized_schema = "video-post-v1" if site in {"douyin", "bilibili"} else "generic-video-v1"
    return {
        "place": str(item.get("place") or ""),
        "topic": str(item.get("topic") or ""),
        "site": site,
        "normalized_schema": normalized_schema,
        "source_url": _text(item, "url", "raw_url"),
        "source_title": _text(item, "title", "page_title"),
        "platform": str(item.get("platform") or ""),
        "collected_at": str(item.get("collected_at") or ""),
        "collector_mode": str(item.get("collector_mode") or "page-only"),
        "coverage_status": str(item.get("coverage_status") or "partial"),
        "failure_reason": str(item.get("failure_reason") or ""),
        "failure_detail": str(item.get("failure_detail") or ""),
        "missing_fields": _list(item.get("missing_fields")),
        "time_layer": str(item.get("time_layer") or "recent"),
        "author": _text(item, "author", "author_name"),
        "title": _text(item, "title", "page_title"),
        "publish_time": str(item.get("published_at") or ""),
        "duration_sec": item.get("duration_sec") or 0,
        "page_text": _text(item, "summary", "description", "desc", "page_text"),
        "comment_highlights": _list(item.get("comment_highlights")) or _list(item.get("comments")),
        "transcript_segments": _segments(item, "transcript_segments", "transcript", "subtitles"),
        "visual_segments": _list(item.get("visual_segments")),
        "timeline": _list(item.get("timeline")),
        "shot_candidates": _list(item.get("shot_candidates")) or _list(item.get("screenshots")) or _list(item.get("keyframes")),
        "claims": _list(item.get("claims")),
        "travel_facts": _list(item.get("travel_facts")),
        "travel_tips": _list(item.get("travel_tips")),
        "risk_notes": _list(item.get("risk_notes")),
        "evidence_links": _list(item.get("evidence_links")),
        "media_artifacts": _list(item.get("media_artifacts")),
        "frame_scores": _list(item.get("frame_scores")),
        "selected_frames": _list(item.get("selected_frames")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    items = payload.get("items") if isinstance(payload, dict) and isinstance(payload.get("items"), list) else []
    result = {"items": [build_video_record(item) for item in items if isinstance(item, dict)]}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
