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

    def test_score_video_keyframes_uses_multimodal_analyzer_when_available(self):
        manifest = {
            "items": [
                {"path": "frame-001.jpg", "local_path": "frame-001.jpg", "timestamp": "00:05", "label": "frame-001"},
            ]
        }

        def analyzer(frame):
            return {
                "evidence_score": 0.97,
                "visual_score": 0.74,
                "selected": True,
                "travel_signal_tags": ["queue", "ticketing"],
                "selection_rationale": "Multimodal model detected queue and ticket context.",
            }

        result = score_manifest(manifest, analyzer=analyzer)

        self.assertEqual(result["frame_scores"][0]["score_source"], "multimodal")
        self.assertEqual(result["frame_scores"][0]["evidence_score"], 0.97)
        self.assertTrue(result["selected_frames"][0]["selected_for_publish"])

    def test_score_video_keyframes_falls_back_when_multimodal_analysis_fails(self):
        manifest = {
            "items": [
                {"path": "frame-001.jpg", "local_path": "frame-001.jpg", "timestamp": "00:05", "label": "queue"},
            ]
        }

        def analyzer(_frame):
            raise RuntimeError("network blocked")

        result = score_manifest(manifest, analyzer=analyzer)

        self.assertEqual(result["frame_scores"][0]["score_source"], "heuristic-fallback")
        self.assertIn("analysis_error", result["frame_scores"][0])
        self.assertTrue(result["selected_frames"])


if __name__ == "__main__":
    unittest.main()
