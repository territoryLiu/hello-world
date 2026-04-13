from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import SKILL_DIR, run_script


class MediaPipelineTest(unittest.TestCase):
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
            self.assertEqual(validated["items"][0]["publish_state"], "text-citation-only")
            self.assertFalse(validated["items"][0]["can_render_as_visual"])


if __name__ == "__main__":
    unittest.main()
