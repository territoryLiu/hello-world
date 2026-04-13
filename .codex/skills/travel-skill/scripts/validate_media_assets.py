from pathlib import Path
import argparse
import json


def classify_item(item: dict) -> dict:
    has_link = bool(str(item.get("url") or "").strip())
    keyframes = item.get("keyframes") if isinstance(item.get("keyframes"), list) else []
    if has_link and keyframes:
        state = "hero-ready" if len(keyframes) >= 2 else "illustrative-media"
        can_render = True
    elif has_link:
        state = "text-citation-only"
        can_render = False
    else:
        state = "blocked"
        can_render = False
    item = dict(item)
    item["publish_state"] = state
    item["can_render_as_visual"] = can_render
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    items = payload.get("items") if isinstance(payload, dict) and isinstance(payload.get("items"), list) else []
    result = {"items": [classify_item(item) for item in items if isinstance(item, dict)]}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
