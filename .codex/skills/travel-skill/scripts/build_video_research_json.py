from pathlib import Path
import argparse
import json


def _list(value):
    return value if isinstance(value, list) else []


def build_video_record(item: dict) -> dict:
    return {
        "source_url": str(item.get("url") or ""),
        "platform": str(item.get("platform") or ""),
        "collected_at": str(item.get("collected_at") or ""),
        "collector_mode": str(item.get("collector_mode") or "page-only"),
        "coverage_status": str(item.get("coverage_status") or "partial"),
        "failure_reason": str(item.get("failure_reason") or ""),
        "author": str(item.get("author") or ""),
        "title": str(item.get("title") or ""),
        "publish_time": str(item.get("published_at") or ""),
        "duration_sec": item.get("duration_sec") or 0,
        "page_text": str(item.get("summary") or ""),
        "comment_highlights": _list(item.get("comment_highlights")),
        "transcript_segments": _list(item.get("transcript_segments")),
        "visual_segments": _list(item.get("visual_segments")),
        "timeline": _list(item.get("timeline")),
        "claims": _list(item.get("claims")),
        "travel_facts": _list(item.get("travel_facts")),
        "travel_tips": _list(item.get("travel_tips")),
        "risk_notes": _list(item.get("risk_notes")),
        "evidence_links": _list(item.get("evidence_links")),
        "media_artifacts": _list(item.get("media_artifacts")),
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
