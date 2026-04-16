from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_structured_facts import extract
from generate_review_packet import build_html, build_markdown
from merge_sources import merge
from validate_site_coverage import validate


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("bundle_paths"), list):
        return payload
    embedded = payload.get("batch_manifest")
    if isinstance(embedded, dict):
        merged = dict(embedded)
        if not merged.get("trip_slug") and isinstance(payload.get("trip_slug"), str):
            merged["trip_slug"] = payload["trip_slug"]
        if not merged.get("batch_id") and isinstance(payload.get("batch_id"), str):
            merged["batch_id"] = payload["batch_id"]
        return merged
    return payload


def _bundle_paths(manifest: dict) -> list[Path]:
    paths = manifest.get("bundle_paths")
    if not isinstance(paths, list):
        return []
    return [Path(path) for path in paths if isinstance(path, str) and path.strip()]


def _synthetic_facts(item: dict) -> list[str]:
    existing = item.get("facts")
    if isinstance(existing, list) and existing:
        return [str(fact).strip() for fact in existing if str(fact).strip()]
    text_candidates = [
        item.get("page_body_full"),
        item.get("summary"),
        item.get("page_text"),
        item.get("text"),
    ]
    for value in text_candidates:
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    shop_name = item.get("shop_name")
    recommended = item.get("recommended_dishes")
    if isinstance(shop_name, str) and shop_name.strip():
        if isinstance(recommended, list) and recommended:
            return [f"{shop_name.strip()} 推荐 {', '.join(str(dish).strip() for dish in recommended if str(dish).strip())}"]
        return [shop_name.strip()]
    return []


def _with_facts(item: dict) -> dict:
    return {**item, "facts": _synthetic_facts(item)}


def aggregate_manifest(manifest: dict) -> tuple[dict, dict]:
    raw_items = []
    page_items = []
    video_items = []
    media_items = []
    trip_slug = str(manifest.get("trip_slug") or "")

    for bundle_path in _bundle_paths(manifest):
        payload = _load_json(bundle_path)
        if not trip_slug and isinstance(payload.get("trip_slug"), str):
            trip_slug = payload["trip_slug"]
        raw = payload.get("raw_items")
        if isinstance(raw, list):
            raw_items.extend(_with_facts(item) for item in raw if isinstance(item, dict))
        page_evidence = payload.get("page_evidence")
        if isinstance(page_evidence, dict) and isinstance(page_evidence.get("items"), list):
            page_items.extend(item for item in page_evidence["items"] if isinstance(item, dict))
        video_records = payload.get("video_records")
        if isinstance(video_records, dict) and isinstance(video_records.get("items"), list):
            video_items.extend(item for item in video_records["items"] if isinstance(item, dict))
        media_candidates = payload.get("media_candidates")
        if isinstance(media_candidates, dict) and isinstance(media_candidates.get("items"), list):
            media_items.extend(item for item in media_candidates["items"] if isinstance(item, dict))

    merged = merge(raw_items)
    structured = extract(
        {
            "entries": merged.get("entries", []),
            "summary": merged.get("summary", {}),
            "normalized": merged.get("normalized", {}),
        }
    )
    batch_bundle = {
        "trip_slug": trip_slug,
        "raw_items": raw_items,
        "page_evidence": {"items": page_items},
        "video_records": {"items": video_items},
        "media_candidates": {"items": media_items},
        "merged": merged,
        "structured": structured,
    }
    coverage = validate(batch_bundle)
    if trip_slug and not coverage.get("trip_slug"):
        coverage["trip_slug"] = trip_slug
    return batch_bundle, coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--bundle-output", required=True)
    parser.add_argument("--coverage-output", required=True)
    parser.add_argument("--review-output-dir", required=True)
    args = parser.parse_args()

    manifest = _manifest_payload(_load_json(Path(args.input)))
    batch_bundle, coverage = aggregate_manifest(manifest if isinstance(manifest, dict) else {})

    bundle_output = Path(args.bundle_output)
    bundle_output.parent.mkdir(parents=True, exist_ok=True)
    bundle_output.write_text(json.dumps(batch_bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    coverage_output = Path(args.coverage_output)
    coverage_output.parent.mkdir(parents=True, exist_ok=True)
    coverage_output.write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")

    review_dir = Path(args.review_output_dir)
    review_dir.mkdir(parents=True, exist_ok=True)
    structured = batch_bundle.get("structured", {})
    review_payload = structured if isinstance(structured, dict) else {}
    (review_dir / "research-packet.md").write_text(build_markdown(review_payload), encoding="utf-8")
    (review_dir / "research-packet.html").write_text(build_html(review_payload), encoding="utf-8")


if __name__ == "__main__":
    main()
