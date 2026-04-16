import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from score_video_keyframes import score_manifest  # noqa: E402


class VideoMediaScoringTest(unittest.TestCase):
    def test_score_video_keyframes_preserves_all_candidates_and_marks_selected(self):
        manifest = {
            "items": [
                {"path": "frame-001.jpg", "timestamp": "00:05", "label": "queue"},
                {"path": "frame-002.jpg", "timestamp": "00:13", "label": "generic-view"},
            ]
        }

        result = score_manifest(manifest)

        self.assertEqual(len(result["all_keyframes"]), 2)
        self.assertTrue(any(item["selected"] for item in result["frame_scores"]))
        self.assertTrue(result["selected_frames"])


if __name__ == "__main__":
    unittest.main()
