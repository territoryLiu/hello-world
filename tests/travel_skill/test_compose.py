from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class ComposeGuideModelTest(unittest.TestCase):
    OUTPUT_KEYS = ["comprehensive", "daily-overview", "recommended"]
    ROUTE_KEYS = [
        "recommended_route",
        "route_options",
        "clothing_guide",
        "attractions",
        "transport_details",
        "food_by_city",
        "tips",
        "sources",
    ]

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

    def test_build_guide_model_outputs_required_v2_layers(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            built = Path(tmp) / "guide-model.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", built)
            payload = json.loads(built.read_text(encoding="utf-8"))

        self.assertIn("meta", payload)
        self.assertIn("outputs", payload)
        self.assertIn("sources", payload)
        self.assertIn("image_plan", payload)
        self.assertEqual(sorted(payload["outputs"].keys()), self.OUTPUT_KEYS)
        self.assertEqual(payload["meta"]["checked_at"], "2026-04-11")

        daily = payload["outputs"]["daily-overview"]
        self.assertIsInstance(daily["summary"], str)
        for key in ["days", "wearing", "transport", "alerts", "sources"]:
            self.assertIsInstance(daily[key], list)

        recommended = payload["outputs"]["recommended"]
        comprehensive = payload["outputs"]["comprehensive"]
        for key in self.ROUTE_KEYS:
            self.assertIsInstance(recommended[key], list)
            self.assertIsInstance(comprehensive[key], list)

        for layer_name, layer_payload in payload["outputs"].items():
            for key, value in layer_payload.items():
                if key == "summary":
                    continue
                if key == "sources":
                    for source in value:
                        self._assert_source_shape(source)
                    continue
                for content_item in value:
                    self._assert_content_item_shape(content_item)
                    self.assertFalse(content_item["is_placeholder"], f"{layer_name}.{key} unexpectedly placeholder")

        self.assertGreaterEqual(len(payload["sources"]), 3)
        self.assertEqual(payload["meta"]["source_count"], len(payload["sources"]))

    def test_fill_missing_sections_enforces_route_and_share_defaults(self):
        raw_model = {
            "meta": {"trip_slug": "demo"},
            "outputs": {
                "daily-overview": {
                    "summary": "两天一夜轻量行程",
                    "days": [{"title": "D1", "summary": "城市漫游", "points": ["先逛市区"], "is_placeholder": False}],
                    "wearing": [],
                    "transport": [],
                    "alerts": [],
                    "sources": [],
                },
                "recommended": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [{"title": "A景点", "summary": "必打卡", "points": [], "is_placeholder": False}],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "filled.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertTrue(payload["outputs"]["daily-overview"]["wearing"])
        self.assertTrue(payload["outputs"]["recommended"]["route_options"])
        self.assertTrue(payload["outputs"]["recommended"]["clothing_guide"])
        self.assertTrue(payload["outputs"]["comprehensive"]["transport_details"])

        def flatten(items):
            text = []
            for item in items:
                text.extend([item.get("title", ""), item.get("summary", ""), *item.get("points", [])])
            return "\n".join(text)

        self.assertIn("分层穿衣", flatten(payload["outputs"]["daily-overview"]["wearing"]))
        self.assertIn("高铁", flatten(payload["outputs"]["recommended"]["route_options"]))
        self.assertIn("交通", flatten(payload["outputs"]["comprehensive"]["transport_details"]))
        self.assertTrue(any(item["is_placeholder"] for item in payload["outputs"]["recommended"]["clothing_guide"]))

    def test_build_then_fill_preserves_sources_and_backfills_required_lists(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            built = Path(tmp) / "guide-model.json"
            filled = Path(tmp) / "guide-model-filled.json"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", built)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", built, "--output", filled)
            payload = json.loads(filled.read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(payload["sources"]), 3)
        self.assertTrue(any("http" in item.get("url", "") for item in payload["sources"]))
        self.assertTrue(payload["outputs"]["recommended"]["route_options"])
        self.assertTrue(payload["outputs"]["recommended"]["clothing_guide"])
        self.assertTrue(payload["outputs"]["comprehensive"]["transport_details"])
        self.assertEqual(payload["meta"]["source_count"], len(payload["sources"]))

    def test_fill_missing_sections_sanitizes_dirty_v2_model(self):
        dirty_model = {
            "meta": {"trip_slug": "dirty", "source_count": 999},
            "outputs": {
                "daily-overview": {
                    "summary": 123,
                    "days": ["dirty-string", {"title": "D1", "summary": "ok", "points": ["p"], "is_placeholder": False}],
                    "wearing": [{"summary": "only summary"}],
                    "transport": [{"title": "T", "summary": "S", "points": "not-list"}],
                    "alerts": [None],
                    "sources": [None, {"url": 1}, {"title": "src", "url": "https://example.com", "type": "official"}],
                },
                "recommended": {
                    "recommended_route": [None],
                    "route_options": [{}],
                    "clothing_guide": [],
                    "attractions": [{"title": "A", "summary": "S", "points": ["x", 1], "is_placeholder": "no"}],
                    "transport_details": "not-a-list",
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {
                    "recommended_route": [],
                    "route_options": ["bad"],
                    "clothing_guide": [],
                    "attractions": [],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
            },
            "sources": [None, {"title": "src", "url": "https://example.com", "type": "official"}],
            "image_plan": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "dirty.json"
            output_path = Path(tmp) / "clean.json"
            input_path.write_text(json.dumps(dirty_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(sorted(payload["outputs"].keys()), self.OUTPUT_KEYS)
        for layer_payload in payload["outputs"].values():
            for key, value in layer_payload.items():
                if key == "summary":
                    self.assertIsInstance(value, str)
                    continue
                if key == "sources":
                    for source in value:
                        self._assert_source_shape(source)
                    continue
                for content_item in value:
                    self._assert_content_item_shape(content_item)
                    self.assertNotEqual(content_item["summary"], "dirty-string")

        self.assertEqual(len(payload["sources"]), 1)
        self.assertEqual(payload["sources"][0]["url"], "https://example.com")
        self.assertEqual(payload["meta"]["source_count"], len(payload["sources"]))


if __name__ == "__main__":
    unittest.main()
