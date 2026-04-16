from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys


KNOWN_FFMPEG_PATHS = [
    Path(r"D:\software\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"),
]


def _scripts_dir() -> Path:
    python_dir = Path(sys.executable).resolve().parent
    scripts_dir = python_dir / "Scripts"
    return scripts_dir if scripts_dir.exists() else python_dir


def _candidate_paths(tool: str) -> list[Path]:
    env_key = f"TRAVEL_SKILL_{tool.upper()}_PATH"
    candidates: list[Path] = []
    env_value = os.environ.get(env_key)
    if env_value:
        candidates.append(Path(env_value))
    scripts_dir = _scripts_dir()
    if tool == "yt_dlp":
        candidates.extend([scripts_dir / "yt-dlp.exe", scripts_dir / "yt-dlp"])
    elif tool == "whisper":
        candidates.extend([scripts_dir / "whisper.exe", scripts_dir / "whisper"])
    elif tool == "ffmpeg":
        candidates.extend(KNOWN_FFMPEG_PATHS)
    return candidates


def resolve_tool_paths() -> dict[str, str]:
    resolved = {
        "yt_dlp": shutil.which("yt-dlp") or "",
        "ffmpeg": shutil.which("ffmpeg") or "",
        "whisper": shutil.which("whisper") or "",
    }
    for tool, current in list(resolved.items()):
        if current:
            continue
        for candidate in _candidate_paths(tool):
            if candidate.exists():
                resolved[tool] = str(candidate)
                break
    return resolved


def _source_path(url: str) -> Path | None:
    candidate = Path(str(url or ""))
    return candidate if candidate.exists() else None


def _shared_model_dir() -> Path:
    env_value = os.environ.get("TRAVEL_SKILL_MODEL_DIR")
    if env_value:
        return Path(env_value)
    return Path.cwd() / "travel-skill-model-cache" / "whisper"


def build_fallback_plan(url: str, asset_root: Path, transcribe: bool = True) -> dict:
    asset_root = Path(asset_root)
    source_path = _source_path(url)
    video_path = asset_root / "video.mp4"
    audio_path = asset_root / "audio.wav"
    keyframe_dir = asset_root / "keyframes"
    transcript_path = asset_root / "audio.json"
    model_dir = _shared_model_dir()
    tools = resolve_tool_paths()
    download_command = [tools["yt_dlp"] or "yt-dlp", "-o", str(video_path), url]
    if source_path is not None:
        download_command = ["copy-local", str(source_path), str(video_path)]
    return {
        "tools": tools,
        "source_url": url,
        "source_path": str(source_path) if source_path else "",
        "steps": [
            {"stage": "download", "command": download_command, "required_tools": [] if source_path else ["yt_dlp"]},
            {
                "stage": "extract_audio",
                "command": [tools["ffmpeg"] or "ffmpeg", "-y", "-i", str(video_path), str(audio_path)],
                "required_tools": ["ffmpeg"],
            },
            {
                "stage": "keyframes",
                "command": [
                    tools["ffmpeg"] or "ffmpeg",
                    "-y",
                    "-i",
                    str(video_path),
                    "-vf",
                    "fps=1/8",
                    str(keyframe_dir / "frame-%03d.jpg"),
                ],
                "required_tools": ["ffmpeg"],
            },
            {
                "stage": "transcribe",
                "command": [
                    tools["whisper"] or "whisper",
                    str(audio_path),
                    "--model",
                    "tiny",
                    "--model_dir",
                    str(model_dir),
                    "--output_format",
                    "json",
                    "--output_dir",
                    str(asset_root),
                ],
                "required_tools": ["whisper"],
                "enabled": transcribe,
            },
        ],
        "artifacts": {
            "video": str(video_path),
            "audio": str(audio_path),
            "keyframe_dir": str(keyframe_dir),
            "keyframe_manifest": str(asset_root / "keyframes.json"),
            "score_manifest": str(asset_root / "frame-scores.json"),
            "transcript": str(transcript_path),
            "model_dir": str(model_dir),
        },
    }


def _run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    ffmpeg_path = resolve_tool_paths().get("ffmpeg") or ""
    if ffmpeg_path:
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")
    return subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False, env=env)


def _first_frame_command(plan: dict) -> list[str]:
    video_path = plan["artifacts"]["video"]
    keyframe_dir = Path(plan["artifacts"]["keyframe_dir"])
    return [
        plan["tools"]["ffmpeg"] or "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        str(keyframe_dir / "frame-001.jpg"),
    ]


def execute_fallback_plan(plan: dict) -> dict:
    asset_root = Path(plan["artifacts"]["video"]).parent
    asset_root.mkdir(parents=True, exist_ok=True)
    keyframe_dir = Path(plan["artifacts"]["keyframe_dir"])
    keyframe_dir.mkdir(parents=True, exist_ok=True)
    Path(plan["artifacts"]["model_dir"]).mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    for step in plan.get("steps", []):
        if not isinstance(step, dict):
            continue
        if step.get("enabled") is False:
            results.append({"stage": step.get("stage"), "status": "skipped", "reason": "disabled"})
            continue
        missing = [tool for tool in step.get("required_tools", []) if not plan["tools"].get(tool)]
        if missing:
            results.append({"stage": step.get("stage"), "status": "missing-tool", "missing_tools": missing})
            continue

        command = step.get("command", [])
        stage = str(step.get("stage") or "")
        if stage == "download" and command[:1] == ["copy-local"]:
            source = Path(command[1])
            target = Path(command[2])
            shutil.copy2(source, target)
            results.append({"stage": stage, "status": "done", "command": command})
            continue

        completed = _run_command(command, asset_root)
        if stage == "keyframes" and completed.returncode != 0:
            fallback_command = _first_frame_command(plan)
            fallback_completed = _run_command(fallback_command, asset_root)
            if fallback_completed.returncode == 0:
                results.append(
                    {
                        "stage": stage,
                        "status": "done",
                        "command": fallback_command,
                        "stdout": fallback_completed.stdout[-4000:],
                        "stderr": fallback_completed.stderr[-4000:],
                        "fallback_used": True,
                    }
                )
                continue
        if stage == "transcribe" and completed.returncode == 0:
            transcript_path = Path(plan["artifacts"]["transcript"])
            if not transcript_path.exists():
                completed = subprocess.CompletedProcess(
                    command,
                    1,
                    completed.stdout,
                    completed.stderr + "\nExpected transcript artifact was not created.",
                )
        result = {
            "stage": stage,
            "status": "done" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "command": command,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
        results.append(result)
        if completed.returncode != 0:
            break

    return {"results": results, "artifacts": plan.get("artifacts", {})}
