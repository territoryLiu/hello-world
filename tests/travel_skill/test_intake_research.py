from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class IntakeResearchTest(unittest.TestCase):
    def _normalize_payload(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output = Path(tmp) / "normalized.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", input_path, "--output", output)
            return json.loads(output.read_text(encoding="utf-8"))

    def test_normalize_request_sets_defaults(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "normalized.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", output)
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["trip_slug"], "wuyi-yanji-changbaishan")
        self.assertEqual(payload["share_mode"], "single-html")
        self.assertEqual(payload["review_mode"], "manual-gate")
        self.assertEqual(payload["missing_core_fields"], [])
        self.assertEqual(payload["missing_preference_fields"], ["must_go", "transport_preference"])
        self.assertEqual(payload["research_dimensions"], ["place", "topic", "platform", "site"])
        self.assertEqual(payload["sample_reference"]["path"], "sample.html")
        self.assertEqual(payload["sample_reference"]["density_mode"], "match-sample")
        self.assertEqual(
            payload["traveler_profile"],
            {
                "adults": 3,
                "children": 1,
                "age_notes": "1 位 7 岁儿童，2 位 60+ 长辈",
            },
        )
        self.assertEqual(
            payload["traveler_constraints"],
            {
                "has_children": True,
                "has_seniors": True,
                "requires_accessible_pace": True,
                "avoid_long_unbroken_walks": True,
            },
        )

    def test_normalize_request_slug_is_non_empty_and_stable_for_unmapped_chinese_title(self):
        raw = {
            "title": "端午吉林松花湖旅行",
            "departure_city": "上海",
            "destinations": ["吉林"],
            "date_range": {"start": "2026-06-20", "end": "2026-06-24"},
            "travelers": {"count": 2, "adults": 2, "children": 0, "age_notes": "", "profile": "情侣"},
            "budget": {"mode": "total", "min": 5000, "max": 8000},
        }
        normalized_first = self._normalize_payload(raw)
        normalized_second = self._normalize_payload(raw)
        self.assertNotEqual(normalized_first["trip_slug"], "")
        self.assertEqual(normalized_first["trip_slug"], normalized_second["trip_slug"])

    def test_normalize_request_unknown_fields_distinguishes_missing_and_explicit_empty(self):
        base = {
            "title": "五一延吉长白山行程",
            "departure_city": "南京",
            "destinations": ["延吉", "长白山"],
            "date_range": {"start": "2026-04-30", "end": "2026-05-05"},
            "travelers": {
                "count": 4,
                "adults": 3,
                "children": 1,
                "age_notes": "1 位 7 岁儿童，2 位 60+ 长辈",
            },
            "budget": {"mode": "per_person", "min": 3000, "max": 5000},
        }
        missing_case = self._normalize_payload(base)
        explicit_empty_case = self._normalize_payload(
            {
                **base,
                "must_go": [],
                "transport_preference": "",
            }
        )
        self.assertEqual(missing_case["missing_preference_fields"], ["must_go", "transport_preference"])
        self.assertEqual(explicit_empty_case["missing_preference_fields"], [])

    def test_build_research_tasks_expands_place_topic_platform_site_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks = Path(tmp) / "tasks.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks)
            payload = json.loads(tasks.read_text(encoding="utf-8"))

        self.assertEqual(payload["trip_slug"], "wuyi-yanji-changbaishan")
        self.assertEqual(payload["research_dimensions"], ["place", "topic", "platform", "site"])
        task_sites = {(item["place"], item["topic"], item["site"]) for item in payload["tasks"]}
        self.assertIn(("延吉", "food", "meituan"), task_sites)
        self.assertIn(("延吉", "food", "dianping"), task_sites)
        self.assertIn(("延吉", "food", "xiaohongshu"), task_sites)
        self.assertIn(("长白山", "attractions", "douyin"), task_sites)
        self.assertIn(("长白山", "attractions", "bilibili"), task_sites)
        self.assertIn(("延吉", "risks", "xiaohongshu"), task_sites)
        self.assertIn(("延吉", "city_transport", "map"), task_sites)
        for task in payload["tasks"]:
            self.assertIn("site", task)
            self.assertIn("site_query", task)
            self.assertIn("collection_method", task)
            self.assertIn("must_capture_fields", task)
            self.assertIn("evidence_level", task)

    def test_build_web_research_runs_outputs_web_access_calls_and_site_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks = Path(tmp) / "tasks.json"
            runs = Path(tmp) / "runs.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks)
            run_script(SKILL_DIR / "scripts" / "build_web_research_runs.py", "--input", tasks, "--output", runs)
            payload = json.loads(runs.read_text(encoding="utf-8"))

        self.assertEqual(payload["runner"], "web-access")
        self.assertIn("runs", payload)
        self.assertIn("site_coverage_targets", payload)
        self.assertIn("food", payload["site_coverage_targets"])
        self.assertIn("xiaohongshu", payload["site_coverage_targets"]["food"])
        self.assertIn("meituan", payload["site_coverage_targets"]["food"])
        self.assertIn("dianping", payload["site_coverage_targets"]["food"])
        first_run = payload["runs"][0]
        self.assertEqual(first_run["skill"], "web-access")
        self.assertTrue(first_run["prompt"].startswith("Use web-access"))

    def test_social_tasks_require_comment_capture_and_transport_tasks_include_latest_searchable_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks_path = Path(tmp) / "tasks.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks_path)
            payload = json.loads(tasks_path.read_text(encoding="utf-8"))

        social_tasks = [
            task
            for task in payload["tasks"]
            if task["site"] in {"xiaohongshu", "douyin", "bilibili"}
        ]
        self.assertTrue(social_tasks)
        for task in social_tasks:
            self.assertIn("comment_highlights", task["must_capture_fields"])
            self.assertIn("comment_capture_status", task["must_capture_fields"])
            self.assertIn("comment_sample_size", task["must_capture_fields"])

        transport_tasks = [task for task in payload["tasks"] if task["topic"] == "long_distance_transport"]
        self.assertTrue(transport_tasks)
        official_transport = next(task for task in transport_tasks if task["site"] == "official")
        self.assertIn("latest_searchable_schedule", official_transport["must_capture_fields"])
        self.assertIn("fallback_strategy", official_transport["must_capture_fields"])
        self.assertIn("checked_date_context", official_transport["must_capture_fields"])

    def test_build_web_research_runs_prompt_requires_body_comment_and_failure_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks_path = Path(tmp) / "tasks.json"
            runs_path = Path(tmp) / "runs.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks_path)
            run_script(SKILL_DIR / "scripts" / "build_web_research_runs.py", "--input", tasks_path, "--output", runs_path)
            payload = json.loads(runs_path.read_text(encoding="utf-8"))

        douyin_run = next(run for run in payload["runs"] if run["task"]["site"] == "douyin")
        self.assertIn("comments", douyin_run["prompt"].lower())
        self.assertIn("timeline", douyin_run["prompt"].lower())
        self.assertIn("failed", douyin_run["prompt"].lower())

    def test_persist_research_knowledge_writes_reusable_place_buckets(self):
        raw_payload = {
            "trip_slug": "demo-trip",
            "records": [
                {"place": "延吉", "topic": "food", "site": "dianping", "status": "success"},
                {"place": "长白山", "topic": "attractions", "site": "official", "status": "success"},
            ],
        }
        approved_payload = {
            "trip_slug": "demo-trip",
            "facts": [
                {"place": "延吉", "topic": "food", "site": "dianping", "text": "冷面"},
                {"place": "长白山", "topic": "attractions", "site": "official", "text": "北坡整天"},
            ],
        }
        media_payload = [
            {"place": "延吉", "platform": "bilibili", "title": "延吉 vlog"},
            {"place": "长白山", "platform": "douyin", "title": "北坡 vlog"},
        ]
        coverage_payload = {
            "trip_slug": "demo-trip",
            "by_topic": {
                "food": {"seen_sites": ["dianping"], "missing_required_sites": ["meituan", "xiaohongshu"]},
                "attractions": {"seen_sites": ["official"], "missing_required_sites": ["xiaohongshu", "douyin", "bilibili"]},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_path = tmp_path / "raw.json"
            approved_path = tmp_path / "approved.json"
            media_path = tmp_path / "media.json"
            coverage_path = tmp_path / "coverage.json"
            output_root = tmp_path / "travel-data"
            raw_path.write_text(json.dumps(raw_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            approved_path.write_text(json.dumps(approved_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            media_path.write_text(json.dumps(media_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            coverage_path.write_text(json.dumps(coverage_payload, ensure_ascii=False, indent=2), encoding="utf-8")

            run_script(
                SKILL_DIR / "scripts" / "persist_research_knowledge.py",
                "--raw-research",
                raw_path,
                "--approved-research",
                approved_path,
                "--media-raw",
                media_path,
                "--site-coverage",
                coverage_path,
                "--output-root",
                output_root,
            )

            yanji_root = output_root / "places" / "yanji"
            changbai_root = output_root / "places" / "changbaishan"

            self.assertTrue((yanji_root / "raw-web-research.json").exists())
            self.assertTrue((yanji_root / "structured-facts.json").exists())
            self.assertTrue((yanji_root / "media-raw.json").exists())
            self.assertTrue((yanji_root / "site-coverage.json").exists())
            self.assertTrue((changbai_root / "raw-web-research.json").exists())

            yanji_facts = json.loads((yanji_root / "structured-facts.json").read_text(encoding="utf-8"))
            self.assertEqual(len(yanji_facts["facts"]), 1)
            self.assertEqual(yanji_facts["facts"][0]["place"], "延吉")


if __name__ == "__main__":
    unittest.main()
