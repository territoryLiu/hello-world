from pathlib import Path
import argparse
import json


FIELDS = [
    "platform",
    "url",
    "title",
    "author",
    "published_at",
    "summary",
    "comment_highlights",
    "transcript_segments",
    "visual_segments",
    "timeline",
    "shot_candidates",
    "image_candidates",
    "media_artifacts",
    "recommended_usage",
    "collector_mode",
    "coverage_status",
    "failure_reason",
]


def normalize_items(payload: list[dict]) -> dict:
    items = []
    for raw in payload:
        entry = raw if isinstance(raw, dict) else {}
        item = {}
        for field in FIELDS:
            value = entry.get(field)
            if field in {"comment_highlights", "transcript_segments", "visual_segments", "timeline", "shot_candidates", "image_candidates", "media_artifacts"}:
                item[field] = value if isinstance(value, list) else []
            else:
                item[field] = str(value or "")
        if not item["collector_mode"]:
            item["collector_mode"] = "page-only"
        if not item["coverage_status"]:
            item["coverage_status"] = "partial"
        if not item["failure_reason"]:
            item["failure_reason"] = ""
        items.append(item)
    return {"items": items}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    normalized = normalize_items(payload if isinstance(payload, list) else [])
    Path(args.output).write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
