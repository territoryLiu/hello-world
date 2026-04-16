import sys
import unittest
from pathlib import Path
from unittest import mock


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

    def test_resolve_tool_paths_can_fall_back_to_imageio_ffmpeg(self):
        fake_module = type(
            "FakeImageioFFmpeg",
            (),
            {"get_ffmpeg_exe": staticmethod(lambda: str(TEST_TMP_ROOT / "fake-ffmpeg.exe"))},
        )
        with mock.patch("video_pipeline.shutil.which", return_value=""), mock.patch(
            "video_pipeline.KNOWN_FFMPEG_PATHS",
            [],
        ), mock.patch.dict("sys.modules", {"imageio_ffmpeg": fake_module}):
            tools = resolve_tool_paths()

        self.assertEqual(tools["ffmpeg"], str(TEST_TMP_ROOT / "fake-ffmpeg.exe"))

    def test_fallback_plan_contains_download_audio_keyframe_and_transcript_steps(self):
        plan = build_fallback_plan("https://example.com/video", Path("assets"))
        stages = [step["stage"] for step in plan["steps"]]
        self.assertEqual(stages, ["download", "extract_audio", "keyframes", "transcribe"])

    def test_fallback_plan_uses_shared_model_cache(self):
        plan_a = build_fallback_plan("https://example.com/video", TESTDATA_ROOT / "assets-a")
        plan_b = build_fallback_plan("https://example.com/video", TESTDATA_ROOT / "assets-b")
        self.assertEqual(plan_a["artifacts"]["model_dir"], plan_b["artifacts"]["model_dir"])

    def test_fallback_plan_defaults_model_cache_to_codex_data_dir(self):
        expected = str(Path.home() / ".codex" / "data" / "travel-skill-model-cache" / "whisper")
        with mock.patch.dict("os.environ", {}, clear=False):
            plan = build_fallback_plan("https://example.com/video", TESTDATA_ROOT / "assets-default-cache")
        self.assertEqual(plan["artifacts"]["model_dir"], expected)

    def test_fallback_plan_exposes_keyframe_and_score_manifests(self):
        plan = build_fallback_plan("https://example.com/video", TESTDATA_ROOT / "assets-c")
        self.assertIn("keyframe_manifest", plan["artifacts"])
        self.assertIn("score_manifest", plan["artifacts"])

    def test_video_record_tracks_time_layer_and_missing_fields(self):
        item = build_video_record(
            {
                "place": "hangzhou",
                "topic": "risks",
                "url": "https://example.com/video",
                "platform": "douyin",
                "site": "douyin",
                "title": "灵隐寺避坑",
                "author": "A",
                "summary": "八点后排队会变长",
                "collector_mode": "video-fallback",
                "coverage_status": "partial",
                "time_layer": "recent",
                "missing_fields": ["transcript_segments"],
            }
        )
        self.assertEqual(item["place"], "hangzhou")
        self.assertEqual(item["topic"], "risks")
        self.assertEqual(item["site"], "douyin")
        self.assertEqual(item["normalized_schema"], "video-post-v1")
        self.assertEqual(item["source_title"], "灵隐寺避坑")
        self.assertEqual(item["time_layer"], "recent")
        self.assertEqual(item["missing_fields"], ["transcript_segments"])
        self.assertEqual(item["collector_mode"], "video-fallback")

    def test_video_record_accepts_common_web_access_alias_fields(self):
        item = build_video_record(
            {
                "place": "hangzhou",
                "topic": "attractions",
                "platform": "douyin",
                "site": "douyin",
                "url": "https://www.douyin.com/video/2",
                "title": "西湖人流观察",
                "description": "八点后游客明显变多",
                "comments": ["七点半还可以", "最好早到"],
                "transcript": {"segments": [{"start": 0, "end": 3, "text": "八点后游客明显变多"}]},
                "screenshots": [{"image_url": "frame-001.jpg"}],
            }
        )

        self.assertEqual(item["page_text"], "八点后游客明显变多")
        self.assertEqual(len(item["comment_highlights"]), 2)
        self.assertEqual(len(item["transcript_segments"]), 1)
        self.assertEqual(item["shot_candidates"][0]["image_url"], "frame-001.jpg")

    def test_build_status_executes_local_video_pipeline(self):
        local_video = TESTDATA_ROOT / "travel-skill-smoke-input.mp4"
        self.assertTrue(local_video.exists())
        asset_root = TEST_TMP_ROOT / "video-test"
        model_dir = TEST_TMP_ROOT / "model-cache" / "whisper"
        if asset_root.exists():
            import shutil
            shutil.rmtree(asset_root)
        asset_root.mkdir(parents=True, exist_ok=True)

        with mock.patch.dict("os.environ", {"TRAVEL_SKILL_MODEL_DIR": str(model_dir)}, clear=False):
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
        model_dir = REPO_ROOT / "travel-skill-model-cache" / "whisper"
        model_file = model_dir / "tiny.pt"
        if asset_root.exists():
            import shutil
            shutil.rmtree(asset_root)
        asset_root.mkdir(parents=True, exist_ok=True)

        with mock.patch.dict("os.environ", {"TRAVEL_SKILL_MODEL_DIR": str(model_dir)}, clear=False):
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
        if tools["ffmpeg"] and tools["whisper"] and model_file.exists():
            self.assertEqual(item["coverage_status"], "complete")
            self.assertTrue(Path(artifacts["transcript"]).exists())
            self.assertTrue(Path(artifacts["keyframe_manifest"]).exists())
            self.assertTrue(Path(artifacts["score_manifest"]).exists())
            self.assertEqual(item["transcript_status"], "done")
            self.assertIsInstance(item.get("transcript_segments"), list)
            self.assertTrue(item.get("frame_scores"))
        else:
            self.assertEqual(item["coverage_status"], "partial")
            self.assertTrue(item["failure_reason"])
            self.assertTrue(item["failure_detail"])


if __name__ == "__main__":
    unittest.main()
