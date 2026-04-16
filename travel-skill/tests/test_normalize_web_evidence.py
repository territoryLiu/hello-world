import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from normalize_web_evidence import normalize_payload  # noqa: E402


class NormalizeWebEvidenceTest(unittest.TestCase):
    def test_normalize_payload_builds_page_video_media_and_structured_outputs(self):
        payload = {
            "trip_slug": "hangzhou-trip",
            "items": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "platform": "social",
                    "raw_url": "https://www.xiaohongshu.com/explore/1",
                    "title": "西湖晨拍",
                    "body": "七点前到断桥更容易拍空景。",
                    "comments": [{"author": "A", "text": "六点半已经有人了"}],
                    "images": [{"src": "https://cdn.example.com/xhs-1.jpg"}],
                    "checked_at": "2026-04-16T08:00:00",
                },
                {
                    "place": "hangzhou",
                    "topic": "risks",
                    "site": "douyin",
                    "platform": "douyin",
                    "url": "https://www.douyin.com/video/1",
                    "title": "灵隐寺避坑",
                    "description": "八点后排队明显变长。",
                    "comments": ["七点半还行"],
                    "transcript": {"segments": [{"start": 0, "end": 3, "text": "八点后排队明显变长"}]},
                    "screenshots": [{"image_url": "frame-001.jpg"}],
                    "checked_at": "2026-04-16T09:00:00",
                },
                {
                    "place": "hangzhou",
                    "topic": "food",
                    "site": "meituan",
                    "platform": "local-listing",
                    "raw_url": "https://i.meituan.com/shop/2",
                    "name": "绿茶",
                    "location": "西湖区龙井路",
                    "price": "90-110",
                    "recommended_items": ["龙井虾仁"],
                    "review_keywords": ["环境好"],
                    "review_notes": ["热门时段提前取号"],
                    "checked_at": "2026-04-16T10:00:00",
                },
            ],
        }

        result = normalize_payload(payload)

        self.assertEqual(result["trip_slug"], "hangzhou-trip")
        self.assertEqual(len(result["page_evidence"]["items"]), 1)
        self.assertEqual(len(result["video_records"]["items"]), 1)
        self.assertEqual(len(result["media_candidates"]["items"]), 3)
        self.assertEqual(len(result["merged"]["entries"]), 3)
        self.assertEqual(len(result["structured"]["normalized_records"]), 3)

        xhs = next(item for item in result["merged"]["entries"] if item["site"] == "xiaohongshu")
        self.assertEqual(xhs["page_body_full"], "七点前到断桥更容易拍空景。")

        douyin = next(item for item in result["structured"]["normalized_records"] if item["site"] == "douyin")
        self.assertEqual(douyin["normalized_schema"], "video-post-v1")
        self.assertTrue(douyin["transcript_segments"])

        meituan = next(item for item in result["structured"]["normalized_records"] if item["site"] == "meituan")
        self.assertEqual(meituan["shop_name"], "绿茶")
        self.assertIn("热门时段提前取号", meituan["pitfalls"])


if __name__ == "__main__":
    unittest.main()
