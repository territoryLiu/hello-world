import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_research_tasks import build_tasks  # noqa: E402
from build_web_research_runs import build_runs  # noqa: E402


class BuildResearchTasksTest(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "trip_slug": "hangzhou-spring-trip",
            "title": "杭州春季自由行",
            "departure_city": "上海",
            "destinations": ["杭州"],
            "required_topics": ["attractions", "food", "risks"],
        }

    def test_tasks_include_dual_layers_for_social_topics(self):
        tasks = build_tasks(self.payload)["tasks"]
        xhs_layers = {task["time_layer"] for task in tasks if task["site"] == "xiaohongshu"}
        self.assertEqual(xhs_layers, {"recent", "last_year_same_period"})

    def test_tasks_include_heavy_sample_targets(self):
        tasks = build_tasks(self.payload)["tasks"]
        douyin_targets = {task["sample_target"] for task in tasks if task["site"] == "douyin"}
        self.assertEqual(douyin_targets, {10})

    def test_web_runs_prompt_mentions_time_layer_and_sample_target(self):
        planned = build_runs({"trip_slug": "hangzhou-spring-trip", "tasks": build_tasks(self.payload)["tasks"]})
        prompt = planned["runs"][0]["prompt"]
        self.assertIn("time_layer=", prompt)
        self.assertIn("sample_target=", prompt)


if __name__ == "__main__":
    unittest.main()
