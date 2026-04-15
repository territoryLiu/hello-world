import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_video_research_json import build_video_record  # noqa: E402
from video_pipeline import build_fallback_plan, resolve_tool_paths  # noqa: E402
from extract_video_assets import build_status  # noqa: E402


class VideoPipelineTest(unittest.TestCase):
    def test_resolve_tool_paths_finds_known_ffmpeg_installation(self):
        tools = resolve_tool_paths()
        self.assertTrue(tools["ffmpeg"])
        self.assertTrue(Path(tools["ffmpeg"]).exists())

    def test_fallback_plan_contains_download_audio_keyframe_and_transcript_steps(self):
        plan = build_fallback_plan("https://example.com/video", Path("C:/tmp/assets"))
        stages = [step["stage"] for step in plan["steps"]]
        self.assertEqual(stages, ["download", "extract_audio", "keyframes", "transcribe"])

    def test_fallback_plan_uses_shared_model_cache(self):
        plan_a = build_fallback_plan("https://example.com/video", Path("d:/vscode/video/assets-a"))
        plan_b = build_fallback_plan("https://example.com/video", Path("d:/vscode/video/assets-b"))
        self.assertEqual(plan_a["artifacts"]["model_dir"], plan_b["artifacts"]["model_dir"])

    def test_video_record_tracks_time_layer_and_missing_fields(self):
        item = build_video_record(
            {
                "url": "https://example.com/video",
                "platform": "douyin",
                "collector_mode": "video-fallback",
                "coverage_status": "partial",
                "time_layer": "recent",
                "missing_fields": ["transcript_segments"],
            }
        )
        self.assertEqual(item["time_layer"], "recent")
        self.assertEqual(item["missing_fields"], ["transcript_segments"])
        self.assertEqual(item["collector_mode"], "video-fallback")

    def test_build_status_executes_local_video_pipeline(self):
        local_video = Path(r"d:\vscode\video\travel-skill-smoke-input.mp4")
        self.assertTrue(local_video.exists())
        asset_root = Path(r"d:\vscode\video\travel-skill-video-test")
        item = build_status(
            {
                "url": str(local_video),
                "asset_root": str(asset_root),
                "collector_mode": "video-fallback",
                "missing_fields": [],
                "time_layer": "recent",
                "run_pipeline": True,
                "transcribe": False,
            }
        )
        self.assertEqual(item["coverage_status"], "complete")
        artifacts = {entry["kind"]: entry["path"] for entry in item["media_artifacts"]}
        self.assertTrue(Path(artifacts["video"]).exists())
        self.assertTrue(Path(artifacts["audio"]).exists())
        self.assertTrue(Path(artifacts["keyframe_dir"]).exists())

    def test_build_status_transcribes_local_video_when_enabled(self):
        local_video = Path(r"d:\vscode\video\travel-skill-smoke-input.mp4")
        self.assertTrue(local_video.exists())
        asset_root = Path(r"d:\vscode\video\travel-skill-video-test-transcribe")
        item = build_status(
            {
                "url": str(local_video),
                "asset_root": str(asset_root),
                "collector_mode": "video-fallback",
                "missing_fields": [],
                "time_layer": "recent",
                "run_pipeline": True,
                "transcribe": True,
            }
        )
        self.assertEqual(item["coverage_status"], "complete")
        artifacts = {entry["kind"]: entry["path"] for entry in item["media_artifacts"]}
        self.assertTrue(Path(artifacts["transcript"]).exists())
        self.assertEqual(item["transcript_status"], "done")


if __name__ == "__main__":
    unittest.main()
