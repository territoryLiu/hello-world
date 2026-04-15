from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from video_pipeline import build_fallback_plan, execute_fallback_plan


def build_status(item: dict) -> dict:
    item = dict(item)
    asset_root = Path(item.get("asset_root") or Path.cwd() / "video-assets")
    run_pipeline = bool(item.get("run_pipeline"))
    transcribe = bool(item.get("transcribe", True))
    plan = build_fallback_plan(str(item.get("url") or ""), asset_root, transcribe=transcribe)
    tools = plan["tools"]
    source_path = Path(plan.get("source_path") or "") if plan.get("source_path") else None
    required_tools = {"ffmpeg"}
    if source_path is None:
        required_tools.add("yt_dlp")
    if transcribe:
        required_tools.add("whisper")
    missing = [name for name in sorted(required_tools) if not tools.get(name)]

    item["fallback_plan"] = plan
    item["ffmpeg_ready"] = bool(tools.get("ffmpeg"))
    item["whisper_ready"] = bool(tools.get("whisper"))
    item["yt_dlp_ready"] = bool(tools.get("yt_dlp"))
    item["transcript_status"] = "planned" if transcribe and item["whisper_ready"] else ("skipped" if not transcribe else "missing-tool")
    item["keyframe_status"] = "planned" if item["ffmpeg_ready"] else "missing-tool"
    item["media_artifacts"] = [{"kind": key, "path": value} for key, value in plan["artifacts"].items()]
    item["missing_fields"] = item.get("missing_fields") if isinstance(item.get("missing_fields"), list) else []
    if missing:
        item["coverage_status"] = str(item.get("coverage_status") or "partial")
        item["failure_reason"] = str(
            item.get("failure_reason")
            or ("video_download_failed" if "yt_dlp" in missing else "audio_transcription_failed")
        )
        item["failure_detail"] = f"Missing tools: {', '.join(missing)}"
        return item

    if run_pipeline:
        execution = execute_fallback_plan(plan)
        item["execution"] = execution
        result_by_stage = {entry.get("stage"): entry for entry in execution.get("results", []) if isinstance(entry, dict)}
        item["transcript_status"] = result_by_stage.get("transcribe", {}).get("status", item["transcript_status"])
        item["keyframe_status"] = result_by_stage.get("keyframes", {}).get("status", item["keyframe_status"])
        failed = next((entry for entry in execution.get("results", []) if entry.get("status") == "failed"), None)
        if failed:
            item["coverage_status"] = "partial"
            stage = str(failed.get("stage") or "")
            default_reason = "audio_transcription_failed" if stage == "transcribe" else "video_download_failed"
            item["failure_reason"] = str(item.get("failure_reason") or default_reason)
            item["failure_detail"] = f"{failed.get('stage')} failed with code {failed.get('returncode')}"
        else:
            item["coverage_status"] = "complete"
            item["failure_reason"] = str(item.get("failure_reason") or "")
            item["failure_detail"] = str(item.get("failure_detail") or "")
    else:
        item["coverage_status"] = "complete"
        item["failure_reason"] = str(item.get("failure_reason") or "")
        item["failure_detail"] = str(item.get("failure_detail") or "")
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
