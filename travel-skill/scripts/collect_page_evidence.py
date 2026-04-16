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


def _pick_text(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _pick_list(item: dict, *keys: str) -> list:
    for key in keys:
        value = item.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def _normalize_images(images: list) -> list[dict]:
    normalized = []
    for raw in images:
        if isinstance(raw, dict):
            url = _pick_text(raw, "url", "image_url", "src")
            if url:
                normalized.append({**raw, "url": url})
        elif isinstance(raw, str) and raw.strip():
            normalized.append({"url": raw.strip()})
    return normalized


def collect(payload: dict) -> dict:
    items = []
    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        page_body_full = _pick_text(raw, "page_body_full", "body", "content_text", "content")
        comments = _pick_list(raw, "comment_threads_full", "comments", "comment_threads")
        image_candidates = _normalize_images(_pick_list(raw, "image_candidates", "images", "gallery"))
        missing_fields = []
        if not page_body_full:
            missing_fields.append("page_body_full")
        if not comments:
            missing_fields.append("comment_threads_full")
        item = dict(raw)
        item["normalized_schema"] = _schema_for_site(item.get("site"))
        item["source_url"] = _pick_text(item, "source_url", "url", "raw_url")
        item["source_title"] = str(item.get("source_title") or item.get("title") or "").strip()
        item["author"] = _pick_text(item, "author", "author_name")
        item["page_body_full"] = page_body_full
        item["comment_threads_full"] = comments
        item["image_candidates"] = image_candidates
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
