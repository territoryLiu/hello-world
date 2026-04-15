import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
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

        output_root = Path(r"d:\vscode\video\travel-skill-test-output")
        persist(raw_payload, approved_payload, media_payload, coverage_payload, output_root)
        place_root = output_root / "places" / "hangzhou"
        self.assertTrue((place_root / "knowledge" / "recent.json").exists())
        self.assertTrue((place_root / "knowledge" / "last-year-same-period.json").exists())
        self.assertTrue((place_root / "coverage" / "site-coverage.json").exists())


if __name__ == "__main__":
    unittest.main()
