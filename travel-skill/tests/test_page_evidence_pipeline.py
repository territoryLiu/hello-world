import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from collect_page_evidence import collect  # noqa: E402


class PageEvidencePipelineTest(unittest.TestCase):
    def test_collect_page_evidence_preserves_full_body_and_comments(self):
        payload = {
            "items": [
                {
                    "site": "xiaohongshu",
                    "page_body_full": "full body text",
                    "comment_threads_full": [{"author": "a", "text": "comment"}],
                    "image_candidates": [{"url": "https://cdn.example.com/1.jpg"}],
                }
            ]
        }

        result = collect(payload)
        item = result["items"][0]

        self.assertEqual(item["coverage_status"], "complete")
        self.assertEqual(item["comment_sample_size"], 1)
        self.assertEqual(item["page_body_full"], "full body text")

    def test_collect_page_evidence_marks_partial_when_comments_missing(self):
        payload = {
            "items": [
                {
                    "site": "xiaohongshu",
                    "page_body_full": "full body text",
                }
            ]
        }

        result = collect(payload)
        item = result["items"][0]

        self.assertEqual(item["coverage_status"], "partial")
        self.assertIn("comment_threads_full", item["missing_fields"])


if __name__ == "__main__":
    unittest.main()
