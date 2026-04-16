import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_structured_facts import extract  # noqa: E402


class ExtractStructuredFactsTest(unittest.TestCase):
    def test_extract_outputs_platform_normalized_records(self):
        payload = {
            "entries": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "platform": "social",
                    "site": "xiaohongshu",
                    "url": "https://www.xiaohongshu.com/explore/1",
                    "title": "西湖避开人流",
                    "author": "A",
                    "publish_time": "2026-04-01",
                    "page_body_full": "早上七点前到断桥，人会少很多。",
                    "comment_threads_full": [{"author": "B", "text": "六点半就有人了"}],
                    "comment_sample_size": 1,
                    "image_candidates": [{"url": "https://cdn.example.com/xhs-1.jpg"}],
                },
                {
                    "place": "hangzhou",
                    "topic": "risks",
                    "platform": "social",
                    "site": "douyin",
                    "url": "https://www.douyin.com/video/1",
                    "title": "灵隐寺避坑",
                    "author": "C",
                    "publish_time": "2026-04-02",
                    "summary": "节假日排队很长",
                    "transcript_segments": [{"start": 0, "end": 3, "text": "早上八点后排队会变长"}],
                    "visual_segments": [{"start": 0, "end": 3, "summary": "门口排队"}],
                    "timeline": [{"label": "queue", "start": 0, "end": 3}],
                    "shot_candidates": [{"local_path": "frame-001.jpg"}],
                    "selected_frames": [{"local_path": "frame-001.jpg", "selected_for_publish": True}],
                },
                {
                    "place": "hangzhou",
                    "topic": "food",
                    "platform": "local-listing",
                    "site": "dianping",
                    "url": "https://www.dianping.com/shop/1",
                    "shop_name": "外婆家",
                    "address": "西湖区",
                    "per_capita_range": "80-100",
                    "recommended_dishes": ["茶香鸡"],
                    "queue_pattern": "饭点排队 40 分钟",
                    "review_themes": ["上菜快", "排队久"],
                    "pitfalls": ["周末尽量提前取号"],
                },
            ]
        }

        result = extract(payload)
        normalized_records = result["normalized_records"]

        self.assertEqual(len(normalized_records), 3)

        xhs_record = next(item for item in normalized_records if item["site"] == "xiaohongshu")
        self.assertEqual(xhs_record["normalized_schema"], "xiaohongshu-note-v1")
        self.assertEqual(xhs_record["comment_sample_size"], 1)
        self.assertTrue(xhs_record["image_candidates"])

        douyin_record = next(item for item in normalized_records if item["site"] == "douyin")
        self.assertEqual(douyin_record["normalized_schema"], "video-post-v1")
        self.assertTrue(douyin_record["transcript_segments"])
        self.assertTrue(douyin_record["selected_frames"])

        dianping_record = next(item for item in normalized_records if item["site"] == "dianping")
        self.assertEqual(dianping_record["normalized_schema"], "local-listing-v1")
        self.assertEqual(dianping_record["shop_name"], "外婆家")
        self.assertIn("上菜快", dianping_record["review_themes"])

    def test_extract_accepts_common_listing_alias_fields(self):
        payload = {
            "entries": [
                {
                    "place": "hangzhou",
                    "topic": "food",
                    "platform": "local-listing",
                    "site": "meituan",
                    "raw_url": "https://i.meituan.com/shop/2",
                    "name": "绿茶",
                    "location": "西湖区龙井路",
                    "price": "90-110",
                    "recommended_items": ["龙井虾仁", "叫花鸡"],
                    "review_keywords": ["环境好", "排队久"],
                    "review_notes": ["热门时段提前排队"],
                }
            ]
        }

        result = extract(payload)
        record = result["normalized_records"][0]

        self.assertEqual(record["site"], "meituan")
        self.assertEqual(record["shop_name"], "绿茶")
        self.assertEqual(record["address"], "西湖区龙井路")
        self.assertEqual(record["per_capita_range"], "90-110")
        self.assertIn("龙井虾仁", record["recommended_dishes"])
        self.assertIn("环境好", record["review_themes"])
        self.assertIn("热门时段提前排队", record["pitfalls"])


if __name__ == "__main__":
    unittest.main()
