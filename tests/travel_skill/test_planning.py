from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import SKILL_DIR, run_script


class PlanningTest(unittest.TestCase):
    def test_build_trip_planning_generates_day_expanded_main_and_options(self):
        approved_payload = {
            "trip_slug": "demo-trip",
            "title": "五一南京延吉长白山",
            "departure_city": "南京",
            "destinations": ["延吉", "长白山", "图们"],
            "date_range": {"start": "2026-04-30", "end": "2026-05-05"},
            "facts": [
                {"topic": "attractions", "place": "长白山北坡", "text": "建议上午进山", "suggested_duration": "整天"},
                {"topic": "food", "place": "延吉", "shop_name": "服务大楼延吉冷面", "text": "适合落地午餐"},
                {
                    "topic": "long_distance_transport",
                    "from": "南京",
                    "to": "长春",
                    "schedule": "G1236 10:34-20:12",
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


if __name__ == "__main__":
    unittest.main()
