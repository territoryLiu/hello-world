import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from research_contracts import (  # noqa: E402
    FAILURE_REASONS,
    HEAVY_SAMPLE_TARGETS,
    TIME_LAYERS,
    site_required_fields,
)


class ResearchContractsTest(unittest.TestCase):
    def test_time_layers_are_dual_layer(self):
        self.assertEqual(TIME_LAYERS, ("recent", "last_year_same_period"))

    def test_heavy_sampling_defaults_match_product_decisions(self):
        self.assertEqual(HEAVY_SAMPLE_TARGETS["xiaohongshu"], 20)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["douyin"], 10)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["bilibili"], 10)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["dianping"], 15)
        self.assertEqual(HEAVY_SAMPLE_TARGETS["meituan"], 15)

    def test_failure_reasons_include_video_and_time_layer_cases(self):
        self.assertIn("video_download_failed", FAILURE_REASONS)
        self.assertIn("time_layer_not_determined", FAILURE_REASONS)

    def test_xiaohongshu_requires_comment_and_media_fields(self):
        required = site_required_fields("xiaohongshu")
        self.assertIn("comment_highlights", required)
        self.assertIn("comment_sample_size", required)
        self.assertIn("image_candidates", required)


if __name__ == "__main__":
    unittest.main()
