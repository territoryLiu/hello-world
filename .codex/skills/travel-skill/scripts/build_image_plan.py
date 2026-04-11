from pathlib import Path
import argparse
import json


def section_name(value: str) -> str:
    raw = str(value or "")
    return raw.split(".", 1)[0] if "." in raw else (raw or "recommended")


def build_plan(payload: dict) -> dict:
    items = payload.get("items", [])
    iterable = items if isinstance(items, list) else []
    section_images = []
    for item in iterable:
        shots = item.get("shot_candidates", [])
        first_shot = shots[0] if isinstance(shots, list) and shots else {}
        section_images.append(
            {
                "section": section_name(item.get("recommended_usage", "")),
                "image_hint": str(first_shot.get("label", "")) or str(item.get("title", "")),
                "source_ref": str(item.get("title", "")),
            }
        )
    first = iterable[0] if iterable else {}
    first_shots = first.get("shot_candidates", []) if isinstance(first, dict) else []
    cover = {
        "image_hint": str(first_shots[0].get("label", "")) if isinstance(first_shots, list) and first_shots else str(first.get("title", "")),
        "source_ref": str(first.get("title", "")),
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
