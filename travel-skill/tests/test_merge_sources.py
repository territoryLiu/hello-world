import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from merge_sources import merge  # noqa: E402


class MergeSourcesTest(unittest.TestCase):
    def test_merge_preserves_platform_evidence_fields_for_page_and_video_sources(self):
        entries = [
            {
                "place": "hangzhou",
                "topic": "attractions",
                "url": "https://www.xiaohongshu.com/explore/1",
                "platform": "social",
                "site": "xiaohongshu",
                "title": "西湖日出",
                "checked_at": "2026-04-15T09:00:00",
                "page_body_full": "六点半之前到断桥。",
                "comment_threads_full": [{"author": "A", "text": "五点多光线最好"}],
                "image_candidates": [{"url": "https://cdn.example.com/1.jpg"}],
            },
            {
                "place": "hangzhou",
                "topic": "risks",
                "url": "https://www.douyin.com/video/1",
                "platform": "social",
                "site": "douyin",
                "title": "灵隐寺避坑",
                "checked_at": "2026-04-15T10:00:00",
                "transcript_segments": [{"start": 0, "end": 3, "text": "八点后排队变长"}],
                "visual_segments": [{"start": 0, "end": 3, "summary": "门口排队"}],
                "selected_frames": [{"local_path": "frame-001.jpg", "selected_for_publish": True}],
            },
        ]

        result = merge(entries)
        merged_entries = result["entries"]

        xhs = next(item for item in merged_entries if item["site"] == "xiaohongshu")
        self.assertEqual(xhs["page_body_full"], "六点半之前到断桥。")
        self.assertEqual(len(xhs["comment_threads_full"]), 1)
        self.assertEqual(len(xhs["image_candidates"]), 1)

        douyin = next(item for item in merged_entries if item["site"] == "douyin")
        self.assertEqual(len(douyin["transcript_segments"]), 1)
        self.assertEqual(len(douyin["visual_segments"]), 1)
        self.assertEqual(len(douyin["selected_frames"]), 1)

    def test_merge_preserves_listing_fields_for_dianping_and_meituan(self):
        entries = [
            {
                "place": "hangzhou",
                "topic": "food",
                "url": "https://www.dianping.com/shop/1",
                "platform": "local-listing",
                "site": "dianping",
                "title": "外婆家",
                "shop_name": "外婆家",
                "address": "西湖区",
                "per_capita_range": "80-100",
                "recommended_dishes": ["茶香鸡"],
                "queue_pattern": "饭点排队",
                "review_themes": ["上菜快"],
                "pitfalls": ["周末提前取号"],
            }
        ]

        result = merge(entries)
        dianping = result["entries"][0]

        self.assertEqual(dianping["shop_name"], "外婆家")
        self.assertEqual(dianping["address"], "西湖区")
        self.assertEqual(dianping["per_capita_range"], "80-100")
        self.assertIn("茶香鸡", dianping["recommended_dishes"])
        self.assertIn("上菜快", dianping["review_themes"])
        self.assertIn("周末提前取号", dianping["pitfalls"])


if __name__ == "__main__":
    unittest.main()
