from pathlib import Path
import json
import tempfile
import unittest

from tests.helpers import SKILL_DIR, run_script


class MediaPipelineTest(unittest.TestCase):
    def test_collect_media_candidates_outputs_video_research_shape(self):
        payload = [
            {
                "platform": "douyin",
                "title": "长白山穿衣",
                "author": "A",
                "summary": "4月很冷",
                "url": "https://www.douyin.com/video/123",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "media.json"
            output_path = Path(tmp) / "normalized.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "collect_media_candidates.py", "--input", input_path, "--output", output_path)
            normalized = json.loads(output_path.read_text(encoding="utf-8"))

        item = normalized["items"][0]
        self.assertEqual(item["collector_mode"], "page-only")
        self.assertEqual(item["coverage_status"], "partial")
        self.assertEqual(item["transcript_segments"], [])
        self.assertEqual(item["visual_segments"], [])
        self.assertEqual(item["media_artifacts"], [])
        self.assertEqual(item["failure_reason"], "")

    def test_extract_video_assets_marks_missing_tools_without_faking_done(self):
        payload = {
            "items": [
                {
                    "platform": "bilibili",
                    "url": "https://www.bilibili.com/video/BV1xx",
                    "title": "延吉攻略",
                    "collector_mode": "video-fallback",
                    "coverage_status": "partial",
                    "failure_reason": "",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "media.json"
            output_path = Path(tmp) / "assets.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "extract_video_assets.py", "--input", input_path, "--output", output_path)
            result = json.loads(output_path.read_text(encoding="utf-8"))

        item = result["items"][0]
        if not item["ffmpeg_ready"]:
            self.assertEqual(item["keyframe_status"], "missing-tool")
        if not item["whisper_ready"]:
            self.assertEqual(item["transcript_status"], "missing-tool")
        self.assertIn(item["coverage_status"], {"partial", "complete"})

    def test_validate_media_assets_blocks_text_only_video_from_visual_slots(self):
        payload = {
            "items": [
                {
                    "platform": "bilibili",
                    "url": "https://www.bilibili.com/video/BV1xx",
                    "title": "长白山北坡攻略",
                    "has_clickable_link": True,
                    "keyframes": [],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "media.json"
            output_path = Path(tmp) / "validated.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "validate_media_assets.py", "--input", input_path, "--output", output_path)
            validated = json.loads(output_path.read_text(encoding="utf-8"))
            item = validated["items"][0]
            self.assertEqual(item["publish_state"], "text-citation-only")
            self.assertFalse(item["can_render_as_visual"])
            self.assertIn(item["coverage_status"], {"partial", "complete"})
            self.assertIn("failure_reason", item)


if __name__ == "__main__":
    unittest.main()
