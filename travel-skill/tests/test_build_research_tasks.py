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

    def test_web_runs_prompt_mentions_capture_policy_and_schema(self):
        tasks = build_tasks(self.payload)["tasks"]
        douyin_task = next(task for task in tasks if task["site"] == "douyin")
        planned = build_runs({"trip_slug": "hangzhou-spring-trip", "tasks": [douyin_task]})
        prompt = planned["runs"][0]["prompt"]
        self.assertIn("raw_capture_policy=page+video-fallback", prompt)
        self.assertIn("media_policy=video-keyframes", prompt)
        self.assertIn("normalized_schema=video-post-v1", prompt)

    def test_web_runs_expose_postprocess_contract_for_ingest(self):
        tasks = build_tasks(self.payload)["tasks"]
        xhs_task = next(task for task in tasks if task["site"] == "xiaohongshu")
        planned = build_runs({"trip_slug": "hangzhou-spring-trip", "tasks": [xhs_task]})
        run = planned["runs"][0]
        self.assertEqual(run["result_schema"], "travel-skill-web-evidence-v1")
        self.assertIn("finalize_web_research_run.py", run["postprocess_script"])

    def test_web_runs_emit_batch_manifest_and_expected_bundle_paths(self):
        tasks = build_tasks(self.payload)["tasks"]
        planned = build_runs({"trip_slug": "hangzhou-spring-trip", "tasks": tasks[:2]})

        self.assertEqual(planned["batch_id"], "hangzhou-spring-trip-web-research")
        self.assertIn("batch_manifest", planned)

        batch_manifest = planned["batch_manifest"]
        self.assertEqual(batch_manifest["batch_id"], planned["batch_id"])
        self.assertEqual(
            batch_manifest["aggregator_script"],
            "travel-skill/scripts/aggregate_web_research_batch.py",
        )
        self.assertEqual(len(batch_manifest["bundle_paths"]), 2)

        for run, bundle_path in zip(planned["runs"], batch_manifest["bundle_paths"]):
            self.assertIn("run_id", run)
            self.assertEqual(run["batch_id"], planned["batch_id"])
            self.assertTrue(run["run_id"].startswith("hangzhou-spring-trip-"))
            self.assertEqual(run["expected_bundle_path"], bundle_path)
            self.assertIn(run["run_id"], run["expected_bundle_path"])
            self.assertTrue(run["expected_bundle_path"].endswith("bundle.json"))
            self.assertTrue(run["expected_coverage_path"].endswith("coverage.json"))

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

    def test_tasks_assign_platform_specific_capture_policies(self):
        tasks = build_tasks(self.payload)["tasks"]
        by_site = {}
        for task in tasks:
            by_site.setdefault(task["site"], task)

        self.assertEqual(by_site["xiaohongshu"]["normalized_schema"], "xiaohongshu-note-v1")
        self.assertEqual(by_site["xiaohongshu"]["raw_capture_policy"], "full")
        self.assertEqual(by_site["xiaohongshu"]["media_policy"], "page-images")

        self.assertEqual(by_site["douyin"]["normalized_schema"], "video-post-v1")
        self.assertEqual(by_site["douyin"]["raw_capture_policy"], "page+video-fallback")
        self.assertEqual(by_site["douyin"]["media_policy"], "video-keyframes")

        self.assertEqual(by_site["bilibili"]["normalized_schema"], "video-post-v1")
        self.assertEqual(by_site["bilibili"]["raw_capture_policy"], "page+video-fallback")
        self.assertEqual(by_site["bilibili"]["media_policy"], "video-keyframes")

        self.assertEqual(by_site["dianping"]["normalized_schema"], "local-listing-v1")
        self.assertEqual(by_site["dianping"]["raw_capture_policy"], "listing+reviews")
        self.assertEqual(by_site["dianping"]["media_policy"], "listing-evidence")

        self.assertEqual(by_site["meituan"]["normalized_schema"], "local-listing-v1")
        self.assertEqual(by_site["meituan"]["raw_capture_policy"], "listing+reviews")
        self.assertEqual(by_site["meituan"]["media_policy"], "listing-evidence")


if __name__ == "__main__":
    unittest.main()
