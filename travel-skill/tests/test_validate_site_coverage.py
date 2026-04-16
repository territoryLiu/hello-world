import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_site_coverage import validate  # noqa: E402


class ValidateSiteCoverageTest(unittest.TestCase):
    def test_marks_partial_when_sample_target_is_not_met(self):
        payload = {
            "records": [
                {"topic": "attractions", "site": "xiaohongshu", "coverage_status": "complete", "missing_fields": [], "time_layer": "recent"}
            ]
        }
        report = validate(payload)
        self.assertEqual(report["by_site"]["xiaohongshu"]["coverage_status"], "partial")
        self.assertIn("insufficient_sample_size", report["by_site"]["xiaohongshu"]["failure_reasons"])

    def test_topic_report_keeps_missing_sites(self):
        payload = {"records": [{"topic": "food", "site": "xiaohongshu", "coverage_status": "complete", "missing_fields": []}]}
        report = validate(payload)
        self.assertIn("dianping", report["by_topic"]["food"]["missing_required_sites"])
        self.assertIn("meituan", report["by_topic"]["food"]["missing_required_sites"])

    def test_flags_video_incomplete_when_page_is_complete(self):
        payload = {
            "records": [
                {
                    "topic": "risks",
                    "site": "douyin",
                    "coverage_status": "partial",
                    "page_body_full": "page body ok",
                    "comment_threads_full": [{"text": "ok"}],
                    "transcript_segments": [],
                    "frame_scores": [],
                    "missing_fields": ["transcript_segments", "frame_scores"],
                }
            ]
        }
        report = validate(payload)
        self.assertIn("video_incomplete", report["by_site"]["douyin"]["failure_reasons"])

    def test_validate_accepts_normalized_web_evidence_bundle(self):
        payload = {
            "structured": {
                "normalized_records": [
                    {
                        "topic": "attractions",
                        "site": "xiaohongshu",
                        "coverage_status": "complete",
                        "missing_fields": [],
                        "time_layer": "recent",
                    },
                    {
                        "topic": "risks",
                        "site": "douyin",
                        "coverage_status": "partial",
                        "missing_fields": ["transcript_segments"],
                        "page_body_full": "page body ok",
                        "transcript_segments": [],
                        "frame_scores": [],
                        "time_layer": "recent",
                    },
                ]
            }
        }

        report = validate(payload)
        self.assertIn("xiaohongshu", report["by_site"])
        self.assertIn("douyin", report["by_site"])
        self.assertIn("video_incomplete", report["by_site"]["douyin"]["failure_reasons"])


if __name__ == "__main__":
    unittest.main()
