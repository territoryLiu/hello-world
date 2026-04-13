from pathlib import Path
import argparse
import json

from travel_paths import ensure_trip_layout


def build_main_plan(payload: dict) -> dict:
    return {
        "plan_id": "main",
        "title": "最推荐路线",
        "strategy": "首晚延吉，长白山前夜二道白河，按天池窗口安排山景日",
        "days": [
            {
                "day": 1,
                "base_city": "延吉",
                "theme": "进场与延吉初逛",
                "morning": ["南京出发，按高铁优先或空铁联运进东北"],
                "afternoon": ["到达延吉后办理入住，先看西市场或延边大学周边"],
                "evening": ["安排冷面、包饭或烧烤作为第一顿城市体验"],
                "transport": ["南京 -> 长春", "长春 -> 延吉"],
                "meals": ["服务大楼延吉冷面", "元奶奶包饭·参鸡汤"],
                "backup_spots": ["延吉水上市场", "延吉咖啡馆"],
            }
        ],
    }


def build_option_plans(payload: dict) -> dict:
    main_days = build_main_plan(payload)["days"]
    return {
        "plans": [
            {
                "plan_id": "rail-first",
                "title": "高铁优先方案",
                "fit_for": "节奏稳定",
                "tradeoffs": ["耗时更长"],
                "days": main_days,
            },
            {
                "plan_id": "flight-hybrid",
                "title": "空铁联运方案",
                "fit_for": "压缩远程移动",
                "tradeoffs": ["成本更高"],
                "days": main_days,
            },
            {
                "plan_id": "extended-nearby",
                "title": "周边延伸方案",
                "fit_for": "想加图们或长春停留",
                "tradeoffs": ["总天数更长"],
                "days": main_days,
            },
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    roots = ensure_trip_layout(Path(args.output_root), payload["trip_slug"])
    planning_root = roots["trip_root"] / "planning"
    (planning_root / "route-main.json").write_text(
        json.dumps(build_main_plan(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (planning_root / "route-options.json").write_text(
        json.dumps(build_option_plans(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
