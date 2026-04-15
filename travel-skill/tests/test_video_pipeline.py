import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
TESTDATA_ROOT = REPO_ROOT / "travel-skill" / "testdata"
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_video_research_json import build_video_record  # noqa: E402
from extract_video_assets import build_status  # noqa: E402
from video_pipeline import build_fallback_plan, resolve_tool_paths  # noqa: E402


class VideoPipelineTest(unittest.TestCase):
    def test_resolve_tool_paths_reports_known_tool_slots(self):
        tools = resolve_tool_paths()
        self.assertEqual(set(tools), {"yt_dlp", "ffmpeg", "whisper"})
        if tools["ffmpeg"]:
            self.assertTrue(Path(tools["ffmpeg"]).exists())

    def test_fallback_plan_contains_download_audio_keyframe_and_transcript_steps(self):
        plan = build_fallback_plan("https://example.com/video", Path("assets"))
        stages = [step["stage"] for step in plan["steps"]]
        self.assertEqual(stages, ["download", "extract_audio", "keyframes", "transcribe"])

    def test_fallback_plan_uses_shared_model_cache(self):
        plan_a = build_fallback_plan("https://example.com/video", TESTDATA_ROOT / "assets-a")
        plan_b = build_fallback_plan("https://example.com/video", TESTDATA_ROOT / "assets-b")
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
        local_video = TESTDATA_ROOT / "travel-skill-smoke-input.mp4"
        self.assertTrue(local_video.exists())
        asset_root = TEST_TMP_ROOT / "video-test"
        if asset_root.exists():
            import shutil
            shutil.rmtree(asset_root)
        asset_root.mkdir(parents=True, exist_ok=True)

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
        artifacts = {entry["kind"]: entry["path"] for entry in item["media_artifacts"]}
        if resolve_tool_paths()["ffmpeg"]:
            self.assertEqual(item["coverage_status"], "complete")
            self.assertTrue(Path(artifacts["video"]).exists())
            self.assertTrue(Path(artifacts["audio"]).exists())
            self.assertTrue(Path(artifacts["keyframe_dir"]).exists())
        else:
            self.assertEqual(item["coverage_status"], "partial")
            self.assertEqual(item["failure_reason"], "audio_transcription_failed")
            self.assertIn("ffmpeg", item["failure_detail"])

    def test_build_status_transcribes_local_video_when_enabled(self):
        local_video = TESTDATA_ROOT / "travel-skill-smoke-input.mp4"
        self.assertTrue(local_video.exists())
        asset_root = TEST_TMP_ROOT / "video-test-transcribe"
        if asset_root.exists():
            import shutil
            shutil.rmtree(asset_root)
        asset_root.mkdir(parents=True, exist_ok=True)

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
        artifacts = {entry["kind"]: entry["path"] for entry in item["media_artifacts"]}
        tools = resolve_tool_paths()
        if tools["ffmpeg"] and tools["whisper"]:
            self.assertEqual(item["coverage_status"], "complete")
            self.assertTrue(Path(artifacts["transcript"]).exists())
            self.assertEqual(item["transcript_status"], "done")
        else:
            self.assertEqual(item["coverage_status"], "partial")
            self.assertTrue(item["failure_reason"])
            self.assertTrue(item["failure_detail"])


if __name__ == "__main__":
    unittest.main()
