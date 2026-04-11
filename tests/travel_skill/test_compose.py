from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class ComposeGuideModelTest(unittest.TestCase):
    SECTION_KEYS = [
        "overview",
        "recommended",
        "options",
        "attractions",
        "food",
        "season",
        "packing",
        "transport",
        "sources",
    ]
    EXECUTION_KEYS = ["booking_order", "daily_table", "budget_bands"]

    def _assert_content_item_shape(self, item):
        self.assertIsInstance(item, dict)
        self.assertIn("title", item)
        self.assertIn("summary", item)
        self.assertIn("points", item)
        self.assertIn("is_placeholder", item)
        self.assertIsInstance(item["title"], str)
        self.assertIsInstance(item["summary"], str)
        self.assertIsInstance(item["points"], list)
        self.assertTrue(all(isinstance(point, str) for point in item["points"]))
        self.assertIsInstance(item["is_placeholder"], bool)

    def _assert_source_shape(self, source):
        self.assertIsInstance(source, dict)
        self.assertEqual(list(source.keys()), ["title", "url", "type", "checked_at"])
        self.assertTrue(all(isinstance(source[field], str) for field in source.keys()))

    def test_build_guide_model_outputs_required_schema_keys(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            built = Path(tmp) / "guide-model.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", built)
            payload = json.loads(built.read_text(encoding="utf-8"))

        self.assertIn("meta", payload)
        self.assertIn("sections", payload)
        self.assertIn("execution", payload)

        self.assertEqual(list(payload["sections"].keys()), self.SECTION_KEYS)
        self.assertEqual(list(payload["execution"].keys()), self.EXECUTION_KEYS)

        for key in self.SECTION_KEYS:
            self.assertIn(key, payload["sections"], f"missing section key: {key}")

        for key in self.EXECUTION_KEYS:
            self.assertIn(key, payload["execution"], f"missing execution key: {key}")

        for key in [item for item in self.SECTION_KEYS if item != "sources"]:
            self.assertIsInstance(payload["sections"][key], list)
            for content_item in payload["sections"][key]:
                self._assert_content_item_shape(content_item)
                self.assertFalse(content_item["is_placeholder"])

        self.assertIsInstance(payload["sections"]["sources"], list)
        for source in payload["sections"]["sources"]:
            self._assert_source_shape(source)

        for key in self.EXECUTION_KEYS:
            self.assertIsInstance(payload["execution"][key], list)
            for content_item in payload["execution"][key]:
                self._assert_content_item_shape(content_item)

        self.assertEqual(payload["meta"]["source_count"], len(payload["sections"]["sources"]))

    def test_fill_missing_sections_enforces_sample_style_gap_defaults(self):
        raw_model = {
            "meta": {"trip_slug": "demo"},
            "sections": {
                "overview": [
                    {
                        "title": "行程概览",
                        "summary": "两天一晚轻量行程。",
                        "points": ["D1 城市漫游"],
                        "is_placeholder": False,
                    }
                ],
                "recommended": [],
                "options": [],
                "attractions": [{"title": "A景点", "summary": "必打卡", "points": [], "is_placeholder": False}],
                "food": [],
                "season": [],
                "packing": [],
                "transport": [],
                "sources": []
            },
            "execution": {
                "booking_order": [],
                "daily_table": [],
                "budget_bands": []
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "filled.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertTrue(payload["execution"]["booking_order"])
        self.assertTrue(payload["execution"]["daily_table"])
        self.assertTrue(payload["execution"]["budget_bands"])

        for key in [item for item in self.SECTION_KEYS if item != "sources"]:
            for content_item in payload["sections"][key]:
                self._assert_content_item_shape(content_item)
        for key in self.EXECUTION_KEYS:
            for content_item in payload["execution"][key]:
                self._assert_content_item_shape(content_item)

        self.assertTrue(any(item["is_placeholder"] for item in payload["sections"]["food"]))
        self.assertTrue(any(item["is_placeholder"] for item in payload["sections"]["season"]))
        self.assertTrue(any(item["is_placeholder"] for item in payload["sections"]["packing"]))
        self.assertTrue(any(item["is_placeholder"] for item in payload["sections"]["transport"]))
        self.assertTrue(any(item["is_placeholder"] for item in payload["execution"]["booking_order"]))
        self.assertTrue(any(item["is_placeholder"] for item in payload["execution"]["budget_bands"]))

        def flatten(items):
            text = []
            for item in items:
                text.extend([item.get("title", ""), item.get("summary", ""), *item.get("points", [])])
            return "\n".join(text)

        self.assertIn("店铺级推荐", flatten(payload["sections"]["food"]))
        self.assertIn("历史体感", flatten(payload["sections"]["season"]))
        self.assertIn("分层穿衣", flatten(payload["sections"]["packing"]))
        self.assertIn("逐段交通", flatten(payload["sections"]["transport"]))
        self.assertIn("订票顺序", flatten(payload["execution"]["booking_order"]))
        self.assertIn("价格区间", flatten(payload["execution"]["budget_bands"]))

    def test_build_then_fill_preserves_sources_and_backfills_execution(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            built = Path(tmp) / "guide-model.json"
            filled = Path(tmp) / "guide-model-filled.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", built)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", built, "--output", filled)
            payload = json.loads(filled.read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(payload["sections"]["sources"]), 3)
        self.assertTrue(any("http" in item.get("url", "") for item in payload["sections"]["sources"]))
        self.assertTrue(payload["execution"]["booking_order"])
        self.assertTrue(payload["execution"]["budget_bands"])
        self.assertEqual(payload["meta"]["source_count"], len(payload["sections"]["sources"]))

    def test_fill_missing_sections_sanitizes_dirty_input_instead_of_stringifying(self):
        dirty_model = {
            "meta": {"trip_slug": "dirty", "source_count": 999},
            "sections": {
                "overview": ["dirty-string", 123, {"bad": "shape"}, {"title": "ok", "summary": "ok", "points": ["p"], "is_placeholder": False}],
                "recommended": [None],
                "options": [{}],
                "attractions": [{"title": "A", "summary": "S", "points": ["x", 1], "is_placeholder": "no"}],
                "food": "not-a-list",
                "season": [{"title": "T"}],
                "packing": [{"summary": "only summary"}],
                "transport": [{"title": "T", "summary": "S", "points": "not-list"}],
                "sources": [None, "bad", {"url": 1}, {"title": "src", "url": "https://example.com", "type": "official"}],
            },
            "execution": {
                "booking_order": ["bad"],
                "daily_table": [{"title": "D1", "summary": "S", "points": [], "is_placeholder": False}],
                "budget_bands": [5, {"title": "预算", "summary": "S", "points": ["x"], "is_placeholder": False}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "dirty.json"
            output_path = Path(tmp) / "clean.json"
            input_path.write_text(json.dumps(dirty_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(list(payload["sections"].keys()), self.SECTION_KEYS)
        self.assertEqual(list(payload["execution"].keys()), self.EXECUTION_KEYS)

        for key in [item for item in self.SECTION_KEYS if item != "sources"]:
            for content_item in payload["sections"][key]:
                self._assert_content_item_shape(content_item)
                self.assertNotEqual(content_item["summary"], "dirty-string")
        for source in payload["sections"]["sources"]:
            self._assert_source_shape(source)

        for key in self.EXECUTION_KEYS:
            for content_item in payload["execution"][key]:
                self._assert_content_item_shape(content_item)

        self.assertEqual(len(payload["sections"]["sources"]), 1)
        self.assertEqual(payload["sections"]["sources"][0]["url"], "https://example.com")
        cleaned_attractions = payload["sections"]["attractions"]
        self.assertTrue(cleaned_attractions)
        self.assertFalse(cleaned_attractions[0]["is_placeholder"])
        self.assertEqual(payload["meta"]["source_count"], len(payload["sections"]["sources"]))


if __name__ == "__main__":
    unittest.main()
