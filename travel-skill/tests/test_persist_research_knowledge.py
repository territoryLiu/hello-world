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


if __name__ == "__main__":
    unittest.main()
