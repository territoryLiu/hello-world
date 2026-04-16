from pathlib import Path
import json
import tempfile
import unittest

from tests.helpers import ROOT, SKILL_DIR, run_script


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

        self.assertEqual(payload["trip_slug"], "五一延吉长白山")
        self.assertEqual(payload["share_mode"], "single-html")
        self.assertEqual(payload["review_mode"], "manual-gate")
        self.assertEqual(payload["missing_core_fields"], [])
        self.assertEqual(payload["missing_preference_fields"], ["must_go", "transport_preference"])
        self.assertEqual(payload["research_dimensions"], ["place", "topic", "platform", "site"])
        self.assertEqual(
            payload["data_layout"],
            {
                "places_root": "travel-data/places",
                "corridors_root": "travel-data/corridors",
                "trip_root": "travel-data/trips/五一延吉长白山",
                "guides_root": "travel-data/guides/五一延吉长白山",
            },
        )
        self.assertEqual(payload["sample_reference"]["path"], "")
        self.assertEqual(payload["sample_reference"]["density_mode"], "")
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

    def test_validate_request_gate_blocks_missing_core_fields(self):
        payload = {
            "title": "五一延吉长白山",
            "departure_city": "南京",
            "destinations": ["延吉", "长白山"],
            "travelers": {"count": 2, "adults": 2, "children": 0, "age_notes": ""},
            "budget": {"mode": "total", "min": 3000, "max": 6000},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "gate.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(
                SKILL_DIR / "scripts" / "validate_request_gate.py",
                "--input",
                input_path,
                "--output",
                output_path,
            )
            gate = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertFalse(gate["can_proceed"])
        self.assertIn("date_range", gate["blocking_fields"])
        self.assertTrue(gate["follow_up_questions"])

    def test_normalize_request_does_not_crash_when_core_fields_are_missing(self):
        payload = {
            "title": "测试行程",
            "departure_city": "南京",
            "destinations": ["延吉"],
            "travelers": {"count": 2, "adults": 2, "children": 0, "age_notes": ""},
            "budget": {"mode": "total", "min": 1000, "max": 2000},
        }
        normalized = self._normalize_payload(payload)
        self.assertEqual(normalized["intake_status"], "blocked")
        self.assertIn("date_range", normalized["blocking_fields"])

    def test_build_research_tasks_expands_place_topic_platform_site_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks = Path(tmp) / "tasks.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks)
            payload = json.loads(tasks.read_text(encoding="utf-8"))

        self.assertEqual(payload["trip_slug"], "五一延吉长白山")
        self.assertEqual(payload["research_dimensions"], ["place", "topic", "platform", "site", "time_layer"])
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

        self.assertEqual(payload["runner"], "travel-skill")
        self.assertIn("runs", payload)
        self.assertIn("site_coverage_targets", payload)
        self.assertIn("food", payload["site_coverage_targets"])
        self.assertIn("xiaohongshu", payload["site_coverage_targets"]["food"])
        self.assertIn("meituan", payload["site_coverage_targets"]["food"])
        self.assertIn("dianping", payload["site_coverage_targets"]["food"])
        first_run = payload["runs"][0]
        self.assertEqual(first_run["skill"], "travel-skill")
        self.assertTrue(first_run["prompt"].startswith("Use the standalone web-access skill"))
        self.assertIn(".codex/skills/travel/web-access", first_run["prompt"])
        self.assertIn("video fallback", first_run["prompt"])
        self.assertIn("coverage_status", first_run["prompt"])

    def test_build_web_research_runs_outputs_batch_manifest_consumable_by_aggregator(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks = Path(tmp) / "tasks.json"
            runs = Path(tmp) / "runs.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks)
            run_script(SKILL_DIR / "scripts" / "build_web_research_runs.py", "--input", tasks, "--output", runs)
            payload = json.loads(runs.read_text(encoding="utf-8"))

        self.assertIn("batch_id", payload)
        self.assertTrue(payload["batch_id"].endswith("-web-research"))
        self.assertIn("batch_manifest", payload)
        batch_manifest = payload["batch_manifest"]
        self.assertEqual(batch_manifest["batch_id"], payload["batch_id"])
        self.assertEqual(batch_manifest["trip_slug"], payload["trip_slug"])
        self.assertEqual(
            batch_manifest["aggregator_script"],
            "travel-skill/scripts/aggregate_web_research_batch.py",
        )
        self.assertEqual(len(batch_manifest["bundle_paths"]), len(payload["runs"]))
        for run in payload["runs"]:
            self.assertEqual(run["batch_id"], payload["batch_id"])
            self.assertIn(run["expected_bundle_path"], batch_manifest["bundle_paths"])
            self.assertIn(run["run_id"], batch_manifest["runs"])

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
            self.assertIn("coverage_status", task["must_capture_fields"])
            self.assertIn("failure_reason", task["must_capture_fields"])
            self.assertEqual(task["collection_method"], "travel-skill")

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
        self.assertIn("video fallback", douyin_run["prompt"].lower())
        self.assertIn("coverage_status", douyin_run["prompt"].lower())
        self.assertIn("failure", douyin_run["prompt"].lower())

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

            yanji_root = output_root / "places" / "延吉"
            changbai_root = output_root / "places" / "长白山"

            self.assertTrue((yanji_root / "raw-web-research.json").exists())
            self.assertTrue((yanji_root / "structured-facts.json").exists())
            self.assertTrue((yanji_root / "media-raw.json").exists())
            self.assertTrue((yanji_root / "site-coverage.json").exists())
            self.assertTrue((changbai_root / "raw-web-research.json").exists())

            yanji_facts = json.loads((yanji_root / "structured-facts.json").read_text(encoding="utf-8"))
            self.assertEqual(len(yanji_facts["facts"]), 1)
            self.assertEqual(yanji_facts["facts"][0]["place"], "延吉")

    def test_persist_research_knowledge_splits_places_and_corridors(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "facts": [
                {"place": "延吉", "topic": "food", "text": "冷面", "source_url": "https://example.com/a"},
                {"place": "长白山", "topic": "attractions", "text": "北坡", "source_url": "https://example.com/b"},
                {
                    "topic": "long_distance_transport",
                    "from": "南京",
                    "to": "长春",
                    "text": "高铁转乘",
                    "source_url": "https://example.com/c",
                },
            ],
        }
        media_payload = [
            {"place": "延吉", "platform": "bilibili", "url": "https://www.bilibili.com/video/BV1xx"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            approved_path = tmp_path / "approved.json"
            media_path = tmp_path / "media.json"
            coverage_path = tmp_path / "coverage.json"
            raw_path = tmp_path / "raw.json"
            output_root = tmp_path / "travel-data"
            approved_path.write_text(json.dumps(approved_payload, ensure_ascii=False), encoding="utf-8")
            media_path.write_text(json.dumps(media_payload, ensure_ascii=False), encoding="utf-8")
            coverage_path.write_text(json.dumps({"trip_slug": "demo-trip"}, ensure_ascii=False), encoding="utf-8")
            raw_path.write_text(json.dumps({"trip_slug": "demo-trip", "records": []}, ensure_ascii=False), encoding="utf-8")

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

            self.assertTrue((output_root / "places" / "延吉" / "structured-facts.json").exists())
            self.assertTrue((output_root / "corridors" / "南京-to-长春" / "transport.json").exists())

    def test_build_trip_snapshots_writes_linked_knowledge_and_corridors(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "travel-data"
            trip_root = data_root / "trips" / "demo-trip"
            (data_root / "places" / "延吉").mkdir(parents=True)
            (data_root / "corridors" / "南京-to-长春").mkdir(parents=True)
            input_path = Path(tmp) / "request.json"
            input_path.write_text(
                json.dumps(
                    {
                        "trip_slug": "demo-trip",
                        "departure_city": "南京",
                        "destinations": ["延吉"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            run_script(
                SKILL_DIR / "scripts" / "build_trip_snapshots.py",
                "--input",
                input_path,
                "--data-root",
                data_root,
            )

            self.assertTrue((trip_root / "snapshots" / "linked-knowledge.json").exists())
            self.assertTrue((trip_root / "snapshots" / "linked-corridors.json").exists())


    def test_ingest_web_research_bundle_normalizes_validates_and_persists(self):
        raw_web_payload = {
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
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "raw-web.json"
            bundle_output = tmp_path / "bundle.json"
            coverage_output = tmp_path / "coverage.json"
            output_root = tmp_path / "travel-data"
            input_path.write_text(json.dumps(raw_web_payload, ensure_ascii=False, indent=2), encoding="utf-8")

            run_script(
                SKILL_DIR / "scripts" / "ingest_web_research_bundle.py",
                "--input",
                input_path,
                "--bundle-output",
                bundle_output,
                "--coverage-output",
                coverage_output,
                "--output-root",
                output_root,
            )

            bundle = json.loads(bundle_output.read_text(encoding="utf-8"))
            coverage = json.loads(coverage_output.read_text(encoding="utf-8"))
            place_root = output_root / "places" / "hangzhou"

            self.assertEqual(bundle["trip_slug"], "hangzhou-trip")
            self.assertIn("structured", bundle)
            self.assertIn("by_site", coverage)
            self.assertTrue((place_root / "raw-web-research.json").exists())
            self.assertTrue((place_root / "structured-facts.json").exists())
            self.assertTrue((place_root / "site-coverage.json").exists())

    def test_finalize_web_research_run_merges_task_context_and_ingests(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            normalized = tmp_path / "normalized.json"
            tasks_path = tmp_path / "tasks.json"
            runs_path = tmp_path / "runs.json"
            run_path = tmp_path / "run.json"
            web_result_path = tmp_path / "web-result.json"
            bundle_output = tmp_path / "bundle.json"
            coverage_output = tmp_path / "coverage.json"
            output_root = tmp_path / "travel-data"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"

            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks_path)
            run_script(SKILL_DIR / "scripts" / "build_web_research_runs.py", "--input", tasks_path, "--output", runs_path)

            runs_payload = json.loads(runs_path.read_text(encoding="utf-8"))
            xhs_run = next(run for run in runs_payload["runs"] if run["task"]["site"] == "xiaohongshu")
            run_path.write_text(json.dumps(xhs_run, ensure_ascii=False, indent=2), encoding="utf-8")
            web_result_path.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "raw_url": "https://www.xiaohongshu.com/explore/1",
                                "title": "西湖晨拍",
                                "body": "七点前到断桥更容易拍空景。",
                                "comments": [{"author": "A", "text": "六点半已经有人了"}],
                                "images": [{"src": "https://cdn.example.com/xhs-1.jpg"}],
                                "checked_at": "2026-04-16T08:00:00",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            run_script(
                SKILL_DIR / "scripts" / "finalize_web_research_run.py",
                "--run-file",
                run_path,
                "--web-result",
                web_result_path,
                "--bundle-output",
                bundle_output,
                "--coverage-output",
                coverage_output,
                "--output-root",
                output_root,
            )

            bundle = json.loads(bundle_output.read_text(encoding="utf-8"))
            record = bundle["structured"]["normalized_records"][0]
            self.assertTrue(record["place"])
            self.assertTrue(record["topic"])
            self.assertEqual(record["site"], "xiaohongshu")
            self.assertTrue((output_root / "places").exists())

    def test_execute_web_research_batch_finalizes_runs_and_aggregates_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs_path = tmp_path / "runs.json"
            web_results_dir = tmp_path / "web-results"
            output_root = tmp_path / "travel-data"
            batch_output = tmp_path / "batch-bundle.json"
            coverage_output = tmp_path / "batch-coverage.json"
            report_output = tmp_path / "execution-report.json"
            review_dir = tmp_path / "review"
            web_results_dir.mkdir(parents=True)

            run_one_id = "hangzhou-trip-001-hangzhou-attractions-xiaohongshu-recent"
            run_two_id = "hangzhou-trip-002-hangzhou-food-meituan-recent"
            runs_payload = {
                "runner": "travel-skill",
                "trip_slug": "hangzhou-trip",
                "batch_id": "hangzhou-trip-web-research",
                "batch_manifest": {
                    "trip_slug": "hangzhou-trip",
                    "batch_id": "hangzhou-trip-web-research",
                    "aggregator_script": "travel-skill/scripts/aggregate_web_research_batch.py",
                    "bundle_paths": [
                        "travel-data/trips/hangzhou-trip/research/web-runs/"
                        f"{run_one_id}/bundle.json",
                        "travel-data/trips/hangzhou-trip/research/web-runs/"
                        f"{run_two_id}/bundle.json",
                    ],
                    "runs": {
                        run_one_id: {
                            "bundle_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                            f"{run_one_id}/bundle.json",
                            "coverage_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                            f"{run_one_id}/coverage.json",
                            "site": "xiaohongshu",
                            "topic": "attractions",
                            "time_layer": "recent",
                        },
                        run_two_id: {
                            "bundle_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                            f"{run_two_id}/bundle.json",
                            "coverage_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                            f"{run_two_id}/coverage.json",
                            "site": "meituan",
                            "topic": "food",
                            "time_layer": "recent",
                        },
                    },
                },
                "runs": [
                    {
                        "run_id": run_one_id,
                        "batch_id": "hangzhou-trip-web-research",
                        "expected_bundle_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                        f"{run_one_id}/bundle.json",
                        "expected_coverage_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                        f"{run_one_id}/coverage.json",
                        "task": {
                            "trip_slug": "hangzhou-trip",
                            "place": "hangzhou",
                            "topic": "attractions",
                            "platform": "social",
                            "site": "xiaohongshu",
                            "time_layer": "recent",
                            "collection_method": "travel-skill",
                            "raw_capture_policy": "full",
                            "media_policy": "page-images",
                            "normalized_schema": "xiaohongshu-note-v1",
                            "sample_target": 20,
                            "retry_policy": "retry_same_mode",
                            "fallback_policy": "page_first_then_fallback",
                            "evidence_level": "supporting",
                        },
                    },
                    {
                        "run_id": run_two_id,
                        "batch_id": "hangzhou-trip-web-research",
                        "expected_bundle_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                        f"{run_two_id}/bundle.json",
                        "expected_coverage_path": "travel-data/trips/hangzhou-trip/research/web-runs/"
                        f"{run_two_id}/coverage.json",
                        "task": {
                            "trip_slug": "hangzhou-trip",
                            "place": "hangzhou",
                            "topic": "food",
                            "platform": "local-listing",
                            "site": "meituan",
                            "time_layer": "recent",
                            "collection_method": "travel-skill",
                            "raw_capture_policy": "listing+reviews",
                            "media_policy": "listing-evidence",
                            "normalized_schema": "local-listing-v1",
                            "sample_target": 15,
                            "retry_policy": "retry_same_mode",
                            "fallback_policy": "page_first_then_fallback",
                            "evidence_level": "primary",
                        },
                    },
                ],
            }
            runs_path.write_text(json.dumps(runs_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            (web_results_dir / f"{run_one_id}.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "raw_url": "https://www.xiaohongshu.com/explore/1",
                                "title": "West Lake sunrise",
                                "body": "Arrive before 7am for lighter crowds.",
                                "comments": [{"author": "A", "text": "6:30am already has people."}],
                                "images": [{"src": "https://cdn.example.com/xhs-1.jpg"}],
                                "checked_at": "2026-04-16T08:00:00",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (web_results_dir / f"{run_two_id}.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "raw_url": "https://i.meituan.com/shop/2",
                                "name": "Green Tea",
                                "location": "West Lake Longjing Road",
                                "price": "90-110",
                                "recommended_items": ["Longjing shrimp"],
                                "review_notes": ["Take a queue number before noon."],
                                "checked_at": "2026-04-16T10:00:00",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            run_script(
                SKILL_DIR / "scripts" / "execute_web_research_batch.py",
                "--runs-file",
                runs_path,
                "--web-results-dir",
                web_results_dir,
                "--output-root",
                output_root,
                "--batch-bundle-output",
                batch_output,
                "--batch-coverage-output",
                coverage_output,
                "--review-output-dir",
                review_dir,
                "--execution-report-output",
                report_output,
            )

            batch_payload = json.loads(batch_output.read_text(encoding="utf-8"))
            coverage_payload = json.loads(coverage_output.read_text(encoding="utf-8"))
            report_payload = json.loads(report_output.read_text(encoding="utf-8"))

            run_one_bundle_exists = (
                output_root
                / "trips"
                / "hangzhou-trip"
                / "research"
                / "web-runs"
                / run_one_id
                / "bundle.json"
            ).exists()
            review_html_exists = (review_dir / "research-packet.html").exists()

        self.assertEqual(batch_payload["trip_slug"], "hangzhou-trip")
        self.assertEqual(len(batch_payload["raw_items"]), 2)
        self.assertIn("food", coverage_payload["by_topic"])
        self.assertEqual(report_payload["trip_slug"], "hangzhou-trip")
        self.assertEqual(report_payload["finalized_runs"], 2)
        self.assertEqual(report_payload["missing_results"], [])
        self.assertTrue(run_one_bundle_exists)
        self.assertTrue(review_html_exists)


if __name__ == "__main__":
    unittest.main()
