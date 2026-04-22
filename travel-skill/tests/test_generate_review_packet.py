import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_review_packet import build_html, build_markdown  # noqa: E402


class GenerateReviewPacketTest(unittest.TestCase):
    def test_build_packet_renders_delivery_gate_details_when_present(self):
        payload = {
            "by_place": {
                "平潭": {
                    "attractions": [
                        {
                            "text": "68海里五一建议提前进场",
                            "source_title": "平潭网",
                            "source_type": "official",
                            "checked_at": "2026-04-18",
                            "site": "official",
                        }
                    ]
                }
            },
            "delivery_gate": {
                "status": "fail",
                "failed_checks": ["platform_coverage"],
                "checks": {
                    "platform_coverage": {
                        "passed": False,
                        "reason": "coverage_status_missing",
                        "source": "travel-data/trips/demo/research/batch-coverage.json",
                    }
                },
            },
        }

        markdown = build_markdown(payload)
        html = build_html(payload)

        self.assertIn("## Delivery Gate", markdown)
        self.assertIn("coverage_status_missing", markdown)
        self.assertIn("Delivery Gate", html)
        self.assertIn("platform_coverage", html)
        self.assertIn("coverage_status_missing", html)


if __name__ == "__main__":
    unittest.main()
