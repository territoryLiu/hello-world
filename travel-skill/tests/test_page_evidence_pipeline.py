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

    def test_collect_page_evidence_adds_normalized_schema_and_source_fields(self):
        payload = {
            "items": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "platform": "social",
                    "url": "https://www.xiaohongshu.com/explore/1",
                    "title": "西湖日出",
                    "author": "A",
                    "publish_time": "2026-04-16",
                    "page_body_full": "六点半之前到断桥。",
                    "comment_threads_full": [{"author": "B", "text": "五点多更空"}],
                    "image_candidates": [{"url": "https://cdn.example.com/1.jpg"}],
                }
            ]
        }

        result = collect(payload)
        item = result["items"][0]

        self.assertEqual(item["normalized_schema"], "xiaohongshu-note-v1")
        self.assertEqual(item["source_url"], "https://www.xiaohongshu.com/explore/1")
        self.assertEqual(item["source_title"], "西湖日出")

    def test_collect_page_evidence_accepts_common_web_access_alias_fields(self):
        payload = {
            "items": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "platform": "social",
                    "raw_url": "https://www.xiaohongshu.com/explore/2",
                    "title": "西湖避坑",
                    "author_name": "A",
                    "body": "七点前上苏堤更舒服。",
                    "comments": [{"author": "B", "text": "六点半人还不多"}],
                    "images": [{"src": "https://cdn.example.com/2.jpg"}],
                }
            ]
        }

        result = collect(payload)
        item = result["items"][0]

        self.assertEqual(item["source_url"], "https://www.xiaohongshu.com/explore/2")
        self.assertEqual(item["page_body_full"], "七点前上苏堤更舒服。")
        self.assertEqual(len(item["comment_threads_full"]), 1)
        self.assertEqual(item["image_candidates"][0]["url"], "https://cdn.example.com/2.jpg")


if __name__ == "__main__":
    unittest.main()
