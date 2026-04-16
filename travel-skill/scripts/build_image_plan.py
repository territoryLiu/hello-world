from pathlib import Path
import argparse
import json


def section_name(value: str) -> str:
    raw = str(value or "")
    return raw.split(".", 1)[0] if "." in raw else (raw or "recommended")


def _pick_visual(item: dict) -> dict:
    if item.get("publish_state") == "text-citation-only":
        return {
            "image_hint": "",
            "source_ref": item.get("title", ""),
            "image_url": "",
            "image_source_kind": "",
            "publish_state": "text-citation-only",
        }
    selected_frames = item.get("selected_frames")
    if isinstance(selected_frames, list):
        preferred = next(
            (
                frame
                for frame in selected_frames
                if isinstance(frame, dict) and frame.get("selected_for_publish")
            ),
            None,
        )
        if preferred:
            image_url = str(preferred.get("local_path") or preferred.get("image_url") or "").strip()
            return {
                "image_hint": str(preferred.get("label") or item.get("title") or "").strip(),
                "source_ref": str(item.get("title") or "").strip(),
                "image_url": image_url,
                "image_source_kind": "selected-media",
                "publish_state": "selected-media",
                "evidence_score": preferred.get("evidence_score", 0),
            }
    image_candidates = item.get("image_candidates")
    if isinstance(image_candidates, list):
        for candidate in image_candidates:
            if not isinstance(candidate, dict):
                continue
            image_url = str(candidate.get("url") or candidate.get("image_url") or "").strip()
            if image_url:
                return {
                    "image_hint": str(candidate.get("label") or item.get("title") or "").strip(),
                    "source_ref": str(item.get("title") or "").strip(),
                    "image_url": image_url,
                    "image_source_kind": str(candidate.get("source_kind") or "gallery").strip() or "gallery",
                    "publish_state": str(item.get("publish_state") or "").strip(),
                }

    shot_candidates = item.get("shot_candidates")
    if isinstance(shot_candidates, list):
        for shot in shot_candidates:
            if not isinstance(shot, dict):
                continue
            image_url = str(shot.get("image_url") or shot.get("thumbnail_url") or shot.get("url") or "").strip()
            if image_url:
                return {
                    "image_hint": str(shot.get("label") or item.get("title") or "").strip(),
                    "source_ref": str(item.get("title") or "").strip(),
                    "image_url": image_url,
                    "image_source_kind": "timeline-shot",
                    "publish_state": str(item.get("publish_state") or "").strip(),
                }
        first_shot = next((shot for shot in shot_candidates if isinstance(shot, dict)), {})
        return {
            "image_hint": str(first_shot.get("label") or item.get("title") or "").strip(),
            "source_ref": str(item.get("title") or "").strip(),
            "image_url": "",
            "image_source_kind": "timeline-shot",
            "publish_state": str(item.get("publish_state") or "").strip(),
        }

    return {
        "image_hint": str(item.get("title") or "").strip(),
        "source_ref": str(item.get("title") or "").strip(),
        "image_url": "",
        "image_source_kind": "",
        "publish_state": str(item.get("publish_state") or "").strip(),
    }


def build_plan(payload: dict) -> dict:
    items = payload.get("items", [])
    iterable = items if isinstance(items, list) else []
    section_images = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        visual = _pick_visual(item)
        section_images.append(
            {
                "section": section_name(item.get("recommended_usage", "")),
                "image_hint": visual["image_hint"],
                "source_ref": visual["source_ref"],
                "image_url": visual["image_url"],
                "image_source_kind": visual["image_source_kind"],
                "publish_state": visual.get("publish_state", ""),
                "evidence_score": visual.get("evidence_score", 0),
            }
        )
    first = next((item for item in iterable if isinstance(item, dict)), {})
    cover_visual = _pick_visual(first) if first else {
        "image_hint": "",
        "source_ref": "",
        "image_url": "",
        "image_source_kind": "",
    }
    cover = {
        "image_hint": cover_visual["image_hint"],
        "source_ref": cover_visual["source_ref"],
        "image_url": cover_visual["image_url"],
        "image_source_kind": cover_visual["image_source_kind"],
        "publish_state": cover_visual.get("publish_state", ""),
        "evidence_score": cover_visual.get("evidence_score", 0),
    }
    return {"cover": cover, "section_images": section_images}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    image_plan = build_plan(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(image_plan, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
