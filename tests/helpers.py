import json
from pathlib import Path
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
HOST_ROOT = ROOT.parents[1] if ROOT.parent.name == ".worktrees" else ROOT
TEST_TMP_ROOT = HOST_ROOT / ".tmp-tests"
SKILL_DIR = ROOT / "travel-skill"
if not SKILL_DIR.exists():
    SKILL_DIR = ROOT / ".codex" / "skills" / "travel-skill"
PYTHON = sys.executable


def run_script(*parts):
    cmd = [PYTHON, *(str(part) for part in parts)]
    env = os.environ.copy()
    env["TMPDIR"] = str(TEST_TMP_ROOT)
    env["TMP"] = str(TEST_TMP_ROOT)
    env["TEMP"] = str(TEST_TMP_ROOT)
    return subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(ROOT), env=env)


def write_sample_approved_research(path: Path) -> Path:
    payload = {
        "trip_slug": "wuyi-yanji-changbaishan",
        "title": "五一延吉长白山",
        "checked_at": "2026-04-11",
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
                "checked_at": "2026-04-11",
                "schedule": "G1234 08:12-18:46",
                "price_range": "二等座 785 元起",
                "commute_duration": "约 8 小时 34 分",
                "transport_modes": ["高铁", "飞机", "打车"],
                "transfer_city": "长春",
                "stopover_suggestion": "如果选空铁联运，可在长春停留半日。",
            },
            {
                "topic": "weather",
                "text": "五一气温波动较大，建议分层穿衣。",
                "source_url": "https://example.com/weather",
                "source_title": "天气参考",
                "source_type": "official",
                "site": "official",
                "checked_at": "2026-04-11",
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
                "checked_at": "2026-04-11",
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
                "checked_at": "2026-04-11",
            },
            {
                "topic": "risks",
                "text": "不要赶太满，避免连续走太久。",
                "source_url": "https://example.com/tips",
                "source_title": "小红书经验",
                "source_type": "social",
                "site": "xiaohongshu",
                "checked_at": "2026-04-11",
            },
        ],
        "image_plan": {
            "cover": {
                "image_hint": "天池晨雾",
                "source_ref": "B站旅行 vlog",
                "image_url": "https://cdn.example.com/cover.jpg",
            },
            "section_images": [
                {
                    "section": "attractions",
                    "image_hint": "长白山北坡栈道",
                    "source_ref": "B站旅行 vlog",
                    "image_url": "https://cdn.example.com/attraction.jpg",
                }
            ],
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
