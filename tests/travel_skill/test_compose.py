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
        self.assertEqual(
            list(source.keys()),
            ["title", "url", "type", "checked_at", "site", "topic", "time_sensitive"],
        )
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

    def test_build_guide_model_applies_constraints_distance_rules_and_sample_reference(self):
        raw_model = {
            "trip_slug": "family-yanji",
            "title": "五一延吉长白山亲子游",
            "checked_at": "2026-04-12",
            "departure_city": "南京",
            "destinations": ["延吉", "长白山"],
            "distance_km": 1420,
            "sample_reference": {"path": "sample.html", "density_mode": "match-sample"},
            "traveler_constraints": {
                "has_children": True,
                "has_seniors": True,
                "requires_accessible_pace": True,
                "avoid_long_unbroken_walks": True,
            },
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "南京出发优先看高铁，再补空铁联运。",
                    "source_url": "https://example.com/rail",
                    "source_title": "12306 时刻表",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "city_transport",
                    "text": "景点间接驳以短步行和打车结合会更省力。",
                    "source_url": "https://example.com/city",
                    "source_title": "本地交通",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "延吉午餐可安排冷面和烤肉组合。",
                    "place": "延吉",
                    "shop_name": "顺姬冷面",
                    "address": "延吉市公园路 1 号",
                    "recommended_dishes": ["冷面", "烤肉"],
                    "flavor_style": "朝鲜族风味",
                    "queue_tip": "11:00 前到店会更从容",
                    "backup_options": ["服务大楼冷面"],
                    "source_url": "https://example.com/food",
                    "source_title": "大众点评热榜",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "attractions",
                    "text": "长白山北坡适合预留整天，节奏放松一些会更舒服。",
                    "place": "长白山",
                    "ticket_price": "225 元",
                    "reservation": "提前 3 天预约",
                    "suggested_duration": "8 小时",
                    "source_url": "https://example.com/cbs",
                    "source_title": "长白山景区公告",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "risks",
                    "text": "不要赶太满，避免连续走太久。",
                    "source_url": "https://example.com/tips",
                    "source_title": "小红书经验",
                    "source_type": "social",
                    "site": "xiaohongshu",
                    "checked_at": "2026-04-12",
                },
            ],
            "image_plan": {
                "cover": {"image_hint": "天池晨雾", "source_ref": "B站旅行 vlog"},
                "section_images": [
                    {"section": "attractions", "image_hint": "长白山北坡栈道", "source_ref": "B站旅行 vlog"}
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["meta"]["sample_reference"]["path"], "sample.html")
        self.assertTrue(payload["meta"]["traveler_constraints"]["requires_accessible_pace"])
        self.assertEqual(payload["meta"]["distance_km"], 1420)
        self.assertEqual(payload["meta"]["transport_rule"]["long_distance"], "over-600km")
        route_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["route_options"]
        )
        self.assertIn("高铁优先", route_text)
        self.assertIn("空铁联运", route_text)
        tip_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["tips"]
        )
        self.assertIn("节奏", tip_text)
        self.assertNotIn("不要", tip_text)
        self.assertNotIn("避免", tip_text)

    def test_build_guide_model_builds_detailed_food_cards_and_preserves_image_plan(self):
        raw_model = {
            "trip_slug": "food-demo",
            "title": "延吉美食样例",
            "checked_at": "2026-04-12",
            "facts": [
                {
                    "topic": "food",
                    "text": "延吉午餐可安排冷面和烤肉组合。",
                    "place": "延吉",
                    "shop_name": "顺姬冷面",
                    "address": "延吉市公园路 1 号",
                    "recommended_dishes": ["冷面", "烤肉"],
                    "flavor_style": "朝鲜族风味",
                    "queue_tip": "11:00 前到店会更从容",
                    "backup_options": ["服务大楼冷面", "元奶奶包饭"],
                    "source_url": "https://example.com/food",
                    "source_title": "大众点评热榜",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                }
            ],
            "image_plan": {
                "cover": {"image_hint": "冷面特写", "source_ref": "大众点评图集"},
                "section_images": [{"section": "food_by_city", "image_hint": "门头招牌", "source_ref": "大众点评图集"}],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        food_card = payload["outputs"]["recommended"]["food_by_city"][0]
        self.assertEqual(food_card["title"], "延吉 · 顺姬冷面")
        joined_points = "\n".join(food_card["points"])
        self.assertIn("地址：延吉市公园路 1 号", joined_points)
        self.assertIn("招牌菜：冷面、烤肉", joined_points)
        self.assertIn("排队提示：11:00 前到店会更从容", joined_points)
        self.assertIn("备选店：服务大楼冷面、元奶奶包饭", joined_points)
        self.assertIn("来源站点：dianping", joined_points)
        self.assertEqual(payload["image_plan"]["cover"]["image_hint"], "冷面特写")

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
                    "attractions": [{"title": "A 景点", "summary": "必打卡", "points": [], "is_placeholder": False}],
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


if __name__ == "__main__":
    unittest.main()
