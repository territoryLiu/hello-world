from pathlib import Path
import argparse
import json


def _schema_for_site(site: str) -> str:
    site_name = str(site or "").strip().lower()
    if site_name == "xiaohongshu":
        return "xiaohongshu-note-v1"
    if site_name in {"dianping", "meituan"}:
        return "local-listing-v1"
    return "generic-page-v1"


def collect(payload: dict) -> dict:
    items = []
    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        comments = raw.get("comment_threads_full") if isinstance(raw.get("comment_threads_full"), list) else []
        missing_fields = []
        if not str(raw.get("page_body_full") or "").strip():
            missing_fields.append("page_body_full")
        if not comments:
            missing_fields.append("comment_threads_full")
        item = dict(raw)
        item["normalized_schema"] = _schema_for_site(item.get("site"))
        item["source_url"] = str(item.get("source_url") or item.get("url") or "").strip()
        item["source_title"] = str(item.get("source_title") or item.get("title") or "").strip()
        item["comment_sample_size"] = len(comments)
        item["missing_fields"] = missing_fields
        item["coverage_status"] = "complete" if not missing_fields else "partial"
        items.append(item)
    return {"items": items}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = collect(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
