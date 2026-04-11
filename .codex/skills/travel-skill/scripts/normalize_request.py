from pathlib import Path
import argparse
import hashlib
import json
import re

DEFAULT_SHARE_MODE = "single-html"
DEFAULT_REVIEW_MODE = "manual-gate"
REQUIRED_OPTIONAL_FIELDS = ["must_go", "transport_preference"]


def slugify(text: str) -> str:
    source_text = text or ""
    ascii_map = {
        "五一": "wuyi",
        "端午": "duanwu",
        "延吉": "yanji",
        "长白山": "changbaishan",
        "吉林": "jilin",
    }
    result = source_text
    for source, target in ascii_map.items():
        result = result.replace(source, f" {target} ")
    result = re.sub(r"[^a-zA-Z0-9]+", "-", result.lower())
    result = re.sub(r"-{2,}", "-", result).strip("-")
    if result:
        return result
    digest = hashlib.sha1(source_text.encode("utf-8")).hexdigest()[:12]
    return f"trip-{digest}"


def normalize(payload: dict) -> dict:
    return {
        "title": payload["title"],
        "trip_slug": slugify(payload["title"]),
        "departure_city": payload["departure_city"],
        "date_range": payload["date_range"],
        "travelers": payload["travelers"],
        "budget": payload["budget"],
        "stay_preference": payload.get("stay_preference", ""),
        "pace_preference": payload.get("pace_preference", ""),
        "must_go": payload.get("must_go", []),
        "transport_preference": payload.get("transport_preference", ""),
        "share_mode": payload.get("share_mode", DEFAULT_SHARE_MODE),
        "review_mode": payload.get("review_mode", DEFAULT_REVIEW_MODE),
        "unknown_fields": [key for key in REQUIRED_OPTIONAL_FIELDS if key not in payload],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    normalized = normalize(payload)
    output_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
