from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import SKILL_DIR, run_script


class PlanningTest(unittest.TestCase):
    def test_build_trip_planning_generates_day_expanded_main_and_options(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "title": "端午上海苏州杭州",
            "departure_city": "上海",
            "destinations": ["苏州", "杭州"],
            "date_range": {"start": "2026-04-30", "end": "2026-05-05"},
            "facts": [
                {"topic": "attractions", "place": "拙政园", "text": "适合上午入园", "suggested_duration": "半天"},
                {"topic": "food", "place": "苏州", "shop_name": "得月楼", "text": "适合落地午餐"},
                {
                    "topic": "long_distance_transport",
                    "from": "上海",
                    "to": "苏州",
                    "schedule": "G7001 09:12-09:42",
                    "checked_at": "2026-04-13",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "approved.json"
            output_root = Path(tmp) / "travel-data"
            input_path.write_text(json.dumps(approved_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(
                SKILL_DIR / "scripts" / "build_trip_planning.py",
                "--input",
                input_path,
                "--output-root",
                output_root,
            )
            planning_root = output_root / "trips" / "demo-trip" / "planning"
            route_main = json.loads((planning_root / "route-main.json").read_text(encoding="utf-8"))
            route_options = json.loads((planning_root / "route-options.json").read_text(encoding="utf-8"))
            self.assertTrue(route_main["days"])
            self.assertTrue(route_options["plans"])
            self.assertIn("morning", route_main["days"][0])
            self.assertIn("transport", route_main["days"][0])
            self.assertIn("backup_spots", route_main["days"][0])
            joined = json.dumps(route_main, ensure_ascii=False)
            self.assertIn("上海", joined)
            self.assertIn("苏州", joined)
            self.assertNotIn("延吉", joined)
            self.assertNotIn("长白山", joined)
            self.assertNotIn("二道白河", joined)

    def test_build_trip_planning_generates_independent_option_days(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "title": "短途测试",
            "departure_city": "长春",
            "destinations": ["吉林", "松花湖"],
            "distance_km": 120,
            "facts": [
                {"topic": "attractions", "place": "松花湖", "text": "适合半日到一日"},
                {"topic": "food", "place": "吉林", "shop_name": "乌拉火锅", "text": "适合晚餐"},
                {
                    "topic": "long_distance_transport",
                    "from": "长春",
                    "to": "吉林",
                    "schedule": "C123",
                    "checked_at": "2026-04-13",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "approved.json"
            output_root = Path(tmp) / "travel-data"
            input_path.write_text(json.dumps(approved_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_trip_planning.py", "--input", input_path, "--output-root", output_root)
            route_options = json.loads(
                (output_root / "trips" / "demo-trip" / "planning" / "route-options.json").read_text(encoding="utf-8")
            )

        self.assertGreaterEqual(len(route_options["plans"]), 2)
        self.assertNotEqual(route_options["plans"][0]["days"], route_options["plans"][1]["days"])


if __name__ == "__main__":
    unittest.main()
