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

    def test_build_guide_model_uses_latest_searchable_schedule_when_target_date_not_on_sale(self):
        raw_model = {
            "trip_slug": "rail-fallback-demo",
            "title": "高铁兜底样例",
            "checked_at": "2026-04-12",
            "distance_km": 1260,
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "目标日期车票尚未开售，可先参考最近可售日班次。",
                    "source_url": "https://example.com/12306",
                    "source_title": "12306 时刻参考",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "fallback_strategy": "latest-searchable-date",
                    "checked_date_context": "2026-04-12",
                    "latest_searchable_schedule": {
                        "date": "2026-04-27",
                        "trains": ["G1234 08:12-18:46", "G2345 09:03-19:20"],
                    },
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        route_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["route_options"]
        )
        transport_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["transport_details"]
        )
        self.assertIn("最近可售日", route_text)
        self.assertIn("2026-04-27", route_text)
        self.assertIn("G1234 08:12-18:46", transport_text)
        self.assertIn("正式售票后", transport_text)

    def test_build_guide_model_renders_transport_metrics_and_seasonality_windows(self):
        raw_model = {
            "trip_slug": "v2-density-demo",
            "title": "第二版信息密度样例",
            "checked_at": "2026-04-12",
            "distance_km": 1420,
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "先用高铁做稳定主方案，再补空铁联运。",
                    "source_url": "https://example.com/rail",
                    "source_title": "12306 时刻参考",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "schedule": "G362 南京南 07:14 - 长春西 15:48",
                    "price_range": "二等座 785 元起",
                    "commute_duration": "约 8 小时 34 分",
                    "transport_modes": ["高铁", "飞机", "打车", "公交"],
                    "transfer_city": "长春",
                    "stopover_suggestion": "如果选空铁联运，可在长春停留半日吃锅包肉再接高铁。",
                },
                {
                    "topic": "seasonality",
                    "text": "长白山 9-10 月层林尽染，5 月能看残雪和新绿同框。",
                    "source_url": "https://example.com/season",
                    "source_title": "季节观察",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "best_months": ["9月", "10月"],
                    "current_window": "5 月适合看残雪、新绿、火山地貌。",
                    "not_best_now": "高山花海还在酝酿期。",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        route_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["route_options"]
        )
        clothing_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["clothing_guide"]
        )
        transport_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["transport_details"]
        )
        self.assertIn("G362 南京南 07:14 - 长春西 15:48", transport_text)
        self.assertIn("二等座 785 元起", transport_text)
        self.assertIn("约 8 小时 34 分", transport_text)
        self.assertIn("长春", route_text)
        self.assertIn("锅包肉", route_text)
        self.assertIn("9月、10月", clothing_text)
        self.assertIn("5 月适合看残雪、新绿、火山地貌", clothing_text)
        self.assertIn("高山花海还在酝酿期", clothing_text)

    def test_build_guide_model_groups_food_by_city_and_cuisine_and_exposes_transport_matrix(self):
        raw_model = {
            "trip_slug": "grouped-food-demo",
            "title": "分组样例",
            "checked_at": "2026-04-12",
            "distance_km": 1500,
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "优先高铁，再看空铁联运。",
                    "source_url": "https://example.com/transport",
                    "source_title": "综合交通整理",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "schedule": "G101 南京南 06:30 - 长春西 15:00",
                    "price_range": "二等座 780 元起",
                    "commute_duration": "约 8 小时 30 分",
                    "transport_modes": ["高铁", "飞机", "公交", "打车", "自驾"],
                    "transfer_city": "长春",
                    "stopover_suggestion": "空铁联运可在长春停半日逛这有山。",
                },
                {
                    "topic": "food",
                    "text": "适合安排在午餐时段。",
                    "place": "延吉",
                    "shop_name": "服务大楼冷面",
                    "address": "公园路 12 号",
                    "recommended_dishes": ["冷面", "锅包肉"],
                    "flavor_style": "朝鲜族",
                    "source_url": "https://example.com/food-1",
                    "source_title": "大众点评热榜",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "适合安排在晚餐时段。",
                    "place": "延吉",
                    "shop_name": "丰茂串城",
                    "address": "人民路 88 号",
                    "recommended_dishes": ["羊肉串", "拌饭"],
                    "flavor_style": "烧烤",
                    "source_url": "https://example.com/food-2",
                    "source_title": "美团必吃榜",
                    "source_type": "local-listing",
                    "site": "meituan",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "适合作为长白山落脚后的热汤补给。",
                    "place": "二道白河",
                    "shop_name": "铁锅炖",
                    "address": "白河大街 6 号",
                    "recommended_dishes": ["铁锅炖鱼"],
                    "flavor_style": "东北菜",
                    "source_url": "https://example.com/food-3",
                    "source_title": "小红书整理",
                    "source_type": "social",
                    "site": "xiaohongshu",
                    "checked_at": "2026-04-12",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        route_option = payload["outputs"]["recommended"]["route_options"][0]
        food_cards = payload["outputs"]["recommended"]["food_by_city"]
        joined_food = "\n".join(card["title"] + "\n" + "\n".join(card["points"]) for card in food_cards)
        self.assertIn("transport_matrix", route_option)
        self.assertEqual(len(route_option["transport_matrix"]), 3)
        self.assertIn("高铁优先", route_option["transport_matrix"][0]["name"])
        self.assertIn("延吉 · 朝鲜族", joined_food)
        self.assertIn("延吉 · 烧烤", joined_food)
        self.assertIn("二道白河 · 东北菜", joined_food)

    def test_build_guide_model_adds_transport_access_summaries_and_food_group_cards(self):
        raw_model = {
            "trip_slug": "density-v2-demo",
            "title": "第二版密度补强",
            "checked_at": "2026-04-12",
            "distance_km": 1480,
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "先用高铁锁定节奏，再补空铁联运与市内接驳。",
                    "source_url": "https://example.com/transport",
                    "source_title": "综合交通整理",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "schedule": "G360 南京南 07:12 - 长春西 15:40",
                    "price_range": "二等座 790 元起",
                    "commute_duration": "约 8 小时 28 分",
                    "transport_modes": ["高铁", "飞机", "公交", "地铁", "打车", "自驾"],
                    "transfer_city": "长春",
                    "stopover_suggestion": "如果走空铁联运，可在长春停留半日吃锅包肉再转高铁。",
                },
                {
                    "topic": "food",
                    "text": "午餐适合安排冷面。",
                    "place": "延吉",
                    "shop_name": "服务大楼冷面",
                    "address": "公园路 12 号",
                    "recommended_dishes": ["冷面", "锅包肉"],
                    "flavor_style": "朝鲜族",
                    "source_url": "https://example.com/food-a",
                    "source_title": "大众点评热榜",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "晚餐适合安排烤肉。",
                    "place": "延吉",
                    "shop_name": "丰茂串城",
                    "address": "人民路 88 号",
                    "recommended_dishes": ["羊肉串", "拌饭"],
                    "flavor_style": "烧烤",
                    "source_url": "https://example.com/food-b",
                    "source_title": "美团必吃榜",
                    "source_type": "local-listing",
                    "site": "meituan",
                    "checked_at": "2026-04-12",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        transport_details = payload["outputs"]["recommended"]["transport_details"]
        food_cards = payload["outputs"]["recommended"]["food_by_city"]
        access_cards = [item for item in transport_details if item.get("card_kind") == "transport-access"]
        food_group_cards = [item for item in food_cards if item.get("card_kind") == "food-group"]

        self.assertGreaterEqual(len(access_cards), 2)
        self.assertTrue(any("公交" in "\n".join(card["points"]) for card in access_cards))
        self.assertTrue(any("地铁" in "\n".join(card["points"]) for card in access_cards))
        self.assertTrue(any("打车" in "\n".join(card["points"]) for card in access_cards))
        self.assertTrue(any("自驾" in "\n".join(card["points"]) for card in access_cards))
        self.assertGreaterEqual(len(food_group_cards), 2)
        self.assertTrue(any(card["title"] == "延吉 · 朝鲜族概览" for card in food_group_cards))
        self.assertTrue(any("1 家可选" in "\n".join(card["points"]) for card in food_group_cards))

    def test_build_guide_model_enriches_daily_overview_into_time_buckets(self):
        raw_model = {
            "trip_slug": "daily-density-demo",
            "title": "逐日执行密度",
            "checked_at": "2026-04-12",
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "先坐高铁到长春，再转延吉。",
                    "source_url": "https://example.com/transport",
                    "source_title": "交通整理",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "schedule": "G360 南京南 07:12 - 长春西 15:40",
                },
                {
                    "topic": "attractions",
                    "text": "长白山北坡更适合留整天。",
                    "place": "长白山北坡",
                    "source_url": "https://example.com/a1",
                    "source_title": "景区公告",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "attractions",
                    "text": "延吉水上市场适合放在清晨。",
                    "place": "延吉水上市场",
                    "source_url": "https://example.com/a2",
                    "source_title": "玩法整理",
                    "source_type": "social",
                    "site": "xiaohongshu",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "午餐适合冷面。",
                    "place": "延吉",
                    "shop_name": "服务大楼冷面",
                    "recommended_dishes": ["冷面"],
                    "flavor_style": "朝鲜族",
                    "source_url": "https://example.com/f1",
                    "source_title": "大众点评热榜",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "晚餐适合烤肉。",
                    "place": "延吉",
                    "shop_name": "丰茂串城",
                    "recommended_dishes": ["羊肉串"],
                    "flavor_style": "烧烤",
                    "source_url": "https://example.com/f2",
                    "source_title": "美团必吃榜",
                    "source_type": "local-listing",
                    "site": "meituan",
                    "checked_at": "2026-04-12",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        daily_days = payload["outputs"]["daily-overview"]["days"]
        self.assertTrue(daily_days)
        self.assertTrue(any(item["title"].startswith("D1") for item in daily_days))
        joined = "\n".join(item["summary"] + "\n" + "\n".join(item["points"]) for item in daily_days)
        self.assertIn("上午：", joined)
        self.assertIn("下午：", joined)
        self.assertIn("晚间：", joined)
        self.assertIn("交通：", joined)
        self.assertIn("用餐：", joined)

    def test_build_guide_model_expands_attraction_and_transport_detail_fields(self):
        raw_model = {
            "trip_slug": "detail-density-demo",
            "title": "景点与交通细节密度",
            "checked_at": "2026-04-12",
            "facts": [
                {
                    "topic": "long_distance_transport",
                    "text": "高铁到站后再转景区接驳。",
                    "source_url": "https://example.com/transport",
                    "source_title": "交通整理",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "schedule": "G360 南京南 07:12 - 长春西 15:40",
                    "price_range": "二等座 790 元起",
                    "commute_duration": "约 8 小时 28 分",
                    "arrival_window": "建议 07:00 前到站",
                    "dropoff_point": "长春西站北广场网约车上客点",
                    "queue_peak": "五一前一天 06:30-07:30 进站更密集",
                },
                {
                    "topic": "attractions",
                    "text": "长白山北坡适合整天安排。",
                    "place": "长白山北坡",
                    "ticket_price": "225 元",
                    "reservation": "提前 3 天预约",
                    "reservation_window": "每日 20:00 后更适合复核余票",
                    "suggested_duration": "8 小时",
                    "arrival_window": "建议 08:30 前抵达集散中心",
                    "queue_peak": "10:00-12:00 换乘排队更集中",
                    "dropoff_point": "北坡集散中心落客区",
                    "source_url": "https://example.com/attraction",
                    "source_title": "景区公告",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        attraction_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["attractions"]
        )
        transport_text = "\n".join(
            item["summary"] + "\n" + "\n".join(item["points"])
            for item in payload["outputs"]["recommended"]["transport_details"]
        )
        self.assertIn("建议 08:30 前抵达集散中心", attraction_text)
        self.assertIn("10:00-12:00 换乘排队更集中", attraction_text)
        self.assertIn("北坡集散中心落客区", attraction_text)
        self.assertIn("每日 20:00 后更适合复核余票", attraction_text)
        self.assertIn("建议 07:00 前到站", transport_text)
        self.assertIn("长春西站北广场网约车上客点", transport_text)
        self.assertIn("五一前一天 06:30-07:30 进站更密集", transport_text)

    def test_build_guide_model_attaches_inline_source_meta_to_cards(self):
        raw_model = {
            "trip_slug": "source-inline-demo",
            "title": "卡内来源追溯",
            "checked_at": "2026-04-12",
            "facts": [
                {
                    "topic": "attractions",
                    "text": "长白山北坡适合整天安排。",
                    "place": "长白山北坡",
                    "source_url": "https://example.com/attraction",
                    "source_title": "景区公告",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "food",
                    "text": "午餐适合冷面。",
                    "place": "延吉",
                    "shop_name": "服务大楼冷面",
                    "source_url": "https://example.com/food",
                    "source_title": "大众点评热榜",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                },
                {
                    "topic": "long_distance_transport",
                    "text": "先看高铁，再看接驳。",
                    "source_url": "https://example.com/rail",
                    "source_title": "12306 时刻",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        attraction_card = payload["outputs"]["recommended"]["attractions"][0]
        food_detail_cards = [item for item in payload["outputs"]["recommended"]["food_by_city"] if item["title"] == "延吉 · 服务大楼冷面"]
        transport_card = payload["outputs"]["recommended"]["transport_details"][0]

        self.assertIn("source_meta", attraction_card)
        self.assertEqual(attraction_card["source_meta"]["site"], "official")
        self.assertEqual(attraction_card["source_meta"]["url"], "https://example.com/attraction")
        self.assertTrue(food_detail_cards)
        self.assertEqual(food_detail_cards[0]["source_meta"]["site"], "dianping")
        self.assertEqual(transport_card["source_meta"]["checked_at"], "2026-04-12")

    def test_build_guide_model_attaches_card_media_from_image_plan(self):
        raw_model = {
            "trip_slug": "card-media-demo",
            "title": "卡片媒体绑定",
            "checked_at": "2026-04-12",
            "facts": [
                {
                    "topic": "attractions",
                    "text": "长白山北坡适合整天安排。",
                    "place": "长白山北坡",
                    "source_url": "https://example.com/attraction",
                    "source_title": "景区公告",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                }
            ],
            "image_plan": {
                "cover": {"image_hint": "封面", "source_ref": "景区公告", "image_url": "https://cdn.example.com/cover.jpg"},
                "section_images": [
                    {
                        "section": "attractions",
                        "image_hint": "北坡栈道",
                        "source_ref": "景区公告",
                        "image_url": "https://cdn.example.com/attraction.jpg",
                        "image_source_kind": "timeline-shot",
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        attraction_card = payload["outputs"]["recommended"]["attractions"][0]
        self.assertIn("card_media", attraction_card)
        self.assertEqual(attraction_card["card_media"]["image_url"], "https://cdn.example.com/attraction.jpg")
        self.assertEqual(attraction_card["card_media"]["image_hint"], "北坡栈道")
        self.assertEqual(attraction_card["card_media"]["image_source_kind"], "timeline-shot")

    def test_build_guide_model_attaches_comment_highlights_to_cards(self):
        raw_model = {
            "trip_slug": "comment-highlight-demo",
            "title": "comment highlights",
            "checked_at": "2026-04-12",
            "facts": [
                {
                    "topic": "attractions",
                    "text": "north slope works for a full day",
                    "place": "Changbai North Slope",
                    "source_url": "https://example.com/attraction",
                    "source_title": "official scenic notice",
                    "source_type": "official",
                    "site": "official",
                    "checked_at": "2026-04-12",
                    "comment_highlights": [
                        "arrive before 08:30 for a smoother shuttle queue",
                        "the boardwalk photos look best before noon",
                    ],
                },
                {
                    "topic": "food",
                    "text": "cold noodles fit lunch well",
                    "place": "Yanji",
                    "shop_name": "Service Building Cold Noodles",
                    "source_url": "https://example.com/food",
                    "source_title": "dianping hot list",
                    "source_type": "local-listing",
                    "site": "dianping",
                    "checked_at": "2026-04-12",
                    "comment_highlights": [
                        "go before 11:30 to keep the wait short",
                        "combo ordering is easier for groups of four",
                    ],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "guide.json"
            input_path.write_text(json.dumps(raw_model, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        attraction_card = payload["outputs"]["recommended"]["attractions"][0]
        food_card = payload["outputs"]["recommended"]["food_by_city"][0]

        self.assertEqual(
            attraction_card["comment_highlights"],
            [
                "arrive before 08:30 for a smoother shuttle queue",
                "the boardwalk photos look best before noon",
            ],
        )
        self.assertEqual(
            food_card["comment_highlights"],
            [
                "go before 11:30 to keep the wait short",
                "combo ordering is easier for groups of four",
            ],
        )

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
