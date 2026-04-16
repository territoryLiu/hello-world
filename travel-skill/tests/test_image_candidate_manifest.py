import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_image_plan import build_plan  # noqa: E402


class ImageCandidateManifestTest(unittest.TestCase):
    def test_build_image_plan_prefers_selected_media_manifest(self):
        payload = {
            "items": [
                {
                    "section": "attractions",
                    "recommended_usage": "attractions.hero",
                    "selected_frames": [
                        {
                            "local_path": "frame-001.jpg",
                            "selected_for_publish": True,
                            "evidence_score": 0.92,
                        }
                    ],
                }
            ]
        }

        result = build_plan(payload)
        item = result["section_images"][0]

        self.assertEqual(item["image_url"], "frame-001.jpg")
        self.assertEqual(item["publish_state"], "selected-media")


if __name__ == "__main__":
    unittest.main()
