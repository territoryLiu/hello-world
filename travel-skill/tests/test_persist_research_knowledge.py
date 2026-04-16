import sys
import unittest
from pathlib import Path
import json


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from persist_research_knowledge import persist  # noqa: E402


class PersistResearchKnowledgeTest(unittest.TestCase):
    def test_persist_writes_recent_and_last_year_layers(self):
        raw_payload = {"records": [{"place": "hangzhou", "site": "xiaohongshu", "topic": "attractions", "time_layer": "recent"}]}
        approved_payload = {
            "facts": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "text": "西湖早晨人少",
                    "time_layer": "last_year_same_period",
                }
            ]
        }
        media_payload = {"items": [{"place": "hangzhou", "kind": "keyframe", "path": "frame-001.jpg"}]}
        coverage_payload = {"trip_slug": "hangzhou", "by_topic": {"attractions": {"coverage_status": "complete"}}}

        output_root = TEST_TMP_ROOT / "persist-research-knowledge"
        if output_root.exists():
            import shutil
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root)
        place_root = output_root / "places" / "hangzhou"
        self.assertTrue((place_root / "knowledge" / "recent.json").exists())
        self.assertTrue((place_root / "knowledge" / "last-year-same-period.json").exists())
        self.assertTrue((place_root / "coverage" / "site-coverage.json").exists())

    def test_persist_writes_raw_normalized_media_and_knowledge_layers(self):
        raw_payload = {"records": [{"place": "hangzhou", "site": "xiaohongshu", "topic": "attractions", "time_layer": "recent"}]}
        approved_payload = {
            "facts": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "text": "西湖清晨人少",
                    "time_layer": "recent",
                }
            ]
        }
        media_payload = {"items": [{"place": "hangzhou", "kind": "keyframe", "path": "frame-001.jpg"}]}
        coverage_payload = {"trip_slug": "hangzhou", "by_topic": {"attractions": {"coverage_status": "complete"}}}

        output_root = TEST_TMP_ROOT / "persist-research-knowledge-layers"
        if output_root.exists():
            import shutil
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root)
        place_root = output_root / "places" / "hangzhou"

        self.assertTrue((place_root / "raw").exists())
        self.assertTrue((place_root / "normalized").exists())
        self.assertTrue((place_root / "media").exists())
        self.assertTrue((place_root / "knowledge").exists())

    def test_persist_links_raw_and_normalized_records_by_stable_id(self):
        raw_payload = {"records": [{"place": "hangzhou", "site": "xiaohongshu", "topic": "attractions", "time_layer": "recent"}]}
        approved_payload = {
            "facts": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "text": "西湖清晨人少",
                    "time_layer": "recent",
                }
            ]
        }
        media_payload = {"items": [{"place": "hangzhou", "kind": "keyframe", "path": "frame-001.jpg"}]}
        coverage_payload = {"trip_slug": "hangzhou", "by_topic": {"attractions": {"coverage_status": "complete"}}}

        output_root = TEST_TMP_ROOT / "persist-research-knowledge-record-id"
        if output_root.exists():
            import shutil
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root)
        records_path = output_root / "places" / "hangzhou" / "normalized" / "records.json"
        payload = json.loads(records_path.read_text(encoding="utf-8"))
        record = payload["records"][0]

        self.assertIn("record_id", record)
        self.assertIn("raw_ref", record)

    def test_persist_writes_platform_normalized_records_and_topic_knowledge(self):
        raw_payload = {
            "records": [
                {
                    "place": "hangzhou",
                    "site": "xiaohongshu",
                    "topic": "attractions",
                    "time_layer": "recent",
                },
                {
                    "place": "hangzhou",
                    "site": "dianping",
                    "topic": "food",
                    "time_layer": "recent",
                },
            ]
        }
        approved_payload = {
            "facts": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "text": "西湖工作日早上更容易出片",
                    "time_layer": "recent",
                    "source_url": "https://www.xiaohongshu.com/explore/1",
                },
                {
                    "place": "hangzhou",
                    "topic": "food",
                    "site": "dianping",
                    "text": "热门餐厅饭点排队明显",
                    "time_layer": "recent",
                    "source_url": "https://www.dianping.com/shop/1",
                },
            ],
            "normalized_records": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "site": "xiaohongshu",
                    "time_layer": "recent",
                    "normalized_schema": "xiaohongshu-note-v1",
                    "page_body_full": "西湖日出前后光线最好。",
                    "comment_sample_size": 5,
                },
                {
                    "place": "hangzhou",
                    "topic": "food",
                    "site": "dianping",
                    "time_layer": "recent",
                    "normalized_schema": "local-listing-v1",
                    "shop_name": "外婆家",
                    "queue_pattern": "饭点排队 40 分钟",
                },
            ],
            "knowledge_points": [
                {
                    "place": "hangzhou",
                    "topic": "attractions",
                    "time_layer": "recent",
                    "claim": "西湖工作日早上更容易出片",
                    "evidence_refs": ["https://www.xiaohongshu.com/explore/1"],
                },
                {
                    "place": "hangzhou",
                    "topic": "food",
                    "time_layer": "recent",
                    "claim": "热门餐厅饭点排队明显",
                    "evidence_refs": ["https://www.dianping.com/shop/1"],
                },
            ],
        }
        media_payload = {"items": []}
        coverage_payload = {
            "trip_slug": "hangzhou",
            "by_topic": {
                "attractions": {"coverage_status": "complete"},
                "food": {"coverage_status": "complete"},
            },
        }

        output_root = TEST_TMP_ROOT / "persist-research-knowledge-platform-records"
        if output_root.exists():
            import shutil
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root)
        place_root = output_root / "places" / "hangzhou"

        site_records = json.loads((place_root / "normalized" / "site-records.json").read_text(encoding="utf-8"))
        merged_topics = json.loads((place_root / "knowledge" / "merged-topics.json").read_text(encoding="utf-8"))

        self.assertEqual(len(site_records["records"]), 2)
        self.assertEqual(site_records["records"][0]["source_record_id"], "hangzhou-attractions-xiaohongshu-recent-001")
        self.assertIn("attractions", merged_topics["topics"])
        self.assertIn("food", merged_topics["topics"])


if __name__ == "__main__":
    unittest.main()
