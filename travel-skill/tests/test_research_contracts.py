import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from research_contracts import (  # noqa: E402
    FAILURE_REASONS,
    HEAVY_SAMPLE_TARGETS,
    IMAGE_CANDIDATE_FIELDS,
    RESEARCH_RECORD_FIELDS,
    TIME_LAYERS,
    VIDEO_MEDIA_BUNDLE_FIELDS,
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

    def test_contract_exposes_page_and_video_record_fields(self):
        self.assertIn("page_body_full", RESEARCH_RECORD_FIELDS)
        self.assertIn("comment_threads_full", RESEARCH_RECORD_FIELDS)
        self.assertIn("frame_scores", VIDEO_MEDIA_BUNDLE_FIELDS)
        self.assertIn("selected_frames", VIDEO_MEDIA_BUNDLE_FIELDS)

    def test_contract_exposes_image_candidate_manifest_fields(self):
        self.assertIn("selected_for_publish", IMAGE_CANDIDATE_FIELDS)
        self.assertIn("evidence_score", IMAGE_CANDIDATE_FIELDS)
        self.assertIn("travel_signal_tags", IMAGE_CANDIDATE_FIELDS)


if __name__ == "__main__":
    unittest.main()
