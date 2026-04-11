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
        self.assertEqual(payload["unknown_fields"], ["must_go", "transport_preference"])

    def test_normalize_request_slug_is_non_empty_and_stable_for_unmapped_chinese_title(self):
        raw = {
            "title": "端午吉林慢游",
            "departure_city": "上海",
            "date_range": {"start": "2026-06-20", "end": "2026-06-24"},
            "travelers": {"count": 2, "profile": "情侣"},
            "budget": {"mode": "total", "min": 5000, "max": 8000},
        }
        normalized_first = self._normalize_payload(raw)
        normalized_second = self._normalize_payload(raw)
        self.assertNotEqual(normalized_first["trip_slug"], "")
        self.assertEqual(normalized_first["trip_slug"], normalized_second["trip_slug"])

    def test_normalize_request_unknown_fields_distinguishes_missing_and_explicit_empty(self):
        base = {
            "title": "五一延吉长白山",
            "departure_city": "南京",
            "date_range": {"start": "2026-04-30", "end": "2026-05-05"},
            "travelers": {"count": 4, "profile": "两男两女，8岁左右"},
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
        self.assertEqual(missing_case["unknown_fields"], ["must_go", "transport_preference"])
        self.assertEqual(explicit_empty_case["unknown_fields"], [])

    def test_build_research_tasks_expands_core_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            normalized = Path(tmp) / "normalized.json"
            tasks = Path(tmp) / "tasks.json"
            fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "trip_request_raw.json"
            run_script(SKILL_DIR / "scripts" / "normalize_request.py", "--input", fixture, "--output", normalized)
            run_script(SKILL_DIR / "scripts" / "build_research_tasks.py", "--input", normalized, "--output", tasks)
            payload = json.loads(tasks.read_text(encoding="utf-8"))
        categories = [item["category"] for item in payload["tasks"]]
        expected = {
            "transport": ["official", "platform"],
            "weather": ["official", "history"],
            "clothing": ["history", "social"],
            "attractions": ["official", "social"],
            "food": ["local-listing", "social"],
            "lodging": ["platform", "map"],
            "risk": ["official", "social"],
        }
        self.assertEqual(categories, list(expected.keys()))
        self.assertEqual(payload["trip_slug"], "wuyi-yanji-changbaishan")
        for task in payload["tasks"]:
            self.assertEqual(task["trip_slug"], payload["trip_slug"])
            self.assertEqual(task["required_sources"], expected[task["category"]])
            self.assertEqual(task["query_hint"], f"南京 五一延吉长白山 {task['category']}")


if __name__ == "__main__":
    unittest.main()
