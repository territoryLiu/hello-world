import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
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

    def test_xiaohongshu_tasks_capture_raw_body_comments_and_images(self):
        tasks = [
            task for task in build_tasks(self.payload)["tasks"]
            if task["site"] == "xiaohongshu"
        ]
        self.assertTrue(tasks)
        for task in tasks:
            self.assertEqual(task["raw_capture_policy"], "full")
            self.assertEqual(task["media_policy"], "page-images")
            self.assertIn("page_body_full", task["must_capture_fields"])
            self.assertIn("comment_threads_full", task["must_capture_fields"])
            self.assertIn("image_candidates", task["must_capture_fields"])


if __name__ == "__main__":
    unittest.main()
