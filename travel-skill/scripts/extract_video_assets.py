from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from score_video_keyframes import score_manifest
from video_pipeline import build_fallback_plan, execute_fallback_plan


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_transcript_segments(path: Path) -> tuple[list[dict], str]:
    if not path.exists():
        return [], ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return [], ""
    segments = payload.get("segments") if isinstance(payload.get("segments"), list) else []
    normalized = []
    for index, raw in enumerate(segments):
        if not isinstance(raw, dict):
            continue
        normalized.append(
            {
                "index": raw.get("id", index),
                "start": raw.get("start", 0),
                "end": raw.get("end", 0),
                "text": str(raw.get("text") or "").strip(),
            }
        )
    return normalized, str(payload.get("text") or "").strip()


def _build_keyframe_manifest(path: Path) -> dict:
    items = []
    for frame in sorted(path.glob("*.jpg")):
        items.append(
            {
                "path": str(frame),
                "local_path": str(frame),
                "label": frame.stem,
            }
        )
    return {"items": items}


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
    item["transcript_segments"] = item.get("transcript_segments") if isinstance(item.get("transcript_segments"), list) else []
    item["frame_scores"] = item.get("frame_scores") if isinstance(item.get("frame_scores"), list) else []
    item["selected_frames"] = item.get("selected_frames") if isinstance(item.get("selected_frames"), list) else []
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
        keyframe_manifest = _build_keyframe_manifest(Path(plan["artifacts"]["keyframe_dir"]))
        _write_json(Path(plan["artifacts"]["keyframe_manifest"]), keyframe_manifest)
        score_payload = score_manifest(keyframe_manifest)
        for frame in score_payload.get("frame_scores", []):
            if isinstance(frame, dict):
                frame["selected_for_publish"] = bool(frame.get("selected"))
        for frame in score_payload.get("selected_frames", []):
            if isinstance(frame, dict):
                frame["selected_for_publish"] = True
        _write_json(Path(plan["artifacts"]["score_manifest"]), score_payload)
        item["frame_scores"] = score_payload.get("frame_scores") if isinstance(score_payload.get("frame_scores"), list) else []
        item["selected_frames"] = score_payload.get("selected_frames") if isinstance(score_payload.get("selected_frames"), list) else []
        transcript_segments, transcript_full = _load_transcript_segments(Path(plan["artifacts"]["transcript"]))
        item["transcript_segments"] = transcript_segments
        if transcript_full:
            item["transcript_full"] = transcript_full
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
