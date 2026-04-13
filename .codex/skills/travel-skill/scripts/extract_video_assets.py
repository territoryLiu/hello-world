from pathlib import Path
import argparse
import json
import shutil


def ffmpeg_ready() -> bool:
    return shutil.which("ffmpeg") is not None


def whisper_ready() -> bool:
    return shutil.which("whisper") is not None


def build_status(item: dict) -> dict:
    item = dict(item)
    item["ffmpeg_ready"] = ffmpeg_ready()
    item["whisper_ready"] = whisper_ready()
    item["transcript_status"] = "done" if item["whisper_ready"] else "missing-tool"
    item["keyframe_status"] = "done" if item["ffmpeg_ready"] else "missing-tool"
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    items = payload.get("items") if isinstance(payload, dict) and isinstance(payload.get("items"), list) else []
    result = {"items": [build_status(item) for item in items if isinstance(item, dict)]}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
