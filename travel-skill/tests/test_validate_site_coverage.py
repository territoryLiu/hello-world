import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
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


if __name__ == "__main__":
    unittest.main()
