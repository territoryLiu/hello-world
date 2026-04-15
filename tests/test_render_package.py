from pathlib import Path
import json
import tempfile
import unittest
import zipfile

from tests.helpers import ROOT, SKILL_DIR, run_script, write_sample_approved_research


class RenderPackageTest(unittest.TestCase):
    TEMPLATE_IDS = [
        "editorial",
    ]

    def _guide_root(self, output_root: Path, slug: str) -> Path:
        return output_root / "guides" / slug

    def _template_html(self, guide_root: Path, template_id: str = "editorial", device: str = "desktop") -> str:
        return (guide_root / device / template_id / "index.html").read_text(encoding="utf-8")

    def test_only_five_template_dash_first_assets_drive_rendering(self):
        template_dir = SKILL_DIR / "assets" / "templates"
        active_templates = sorted(path.name for path in template_dir.glob("template-*.html"))
        legacy_templates = sorted(
            path.name
            for path in template_dir.iterdir()
            if path.is_file() and path.name.startswith(("guide-template-", "desktop-index", "mobile-"))
        )

        self.assertEqual(active_templates, ["template-editorial.html"])
        self.assertEqual(legacy_templates, [])

    def test_render_trip_site_emits_exactly_five_template_variants_under_guides_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = write_sample_approved_research(Path(tmp) / "approved_research.json")
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            payload = json.loads(model.read_text(encoding="utf-8"))
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root, "--style", "all")
            guide_root = self._guide_root(output_root, payload["meta"]["trip_slug"])
            required = [
                guide_root / "assets" / "base.css",
                guide_root / "assets" / "render-guide.js",
                guide_root / "assets" / "guide-content.js",
                guide_root / "notes" / "sources.md",
                guide_root / "notes" / "sources.html",
            ]
            required.extend(guide_root / "desktop" / template_id / "index.html" for template_id in self.TEMPLATE_IDS)
            required.extend(guide_root / "mobile" / template_id / "index.html" for template_id in self.TEMPLATE_IDS)
            desktop_html = self._template_html(guide_root, "editorial", "desktop")
            mobile_html = self._template_html(guide_root, "editorial", "mobile")
            sources_md = (guide_root / "notes" / "sources.md").read_text(encoding="utf-8")
            missing = [str(path) for path in required if not path.exists()]
            desktop_dirs = sorted(p.name for p in (guide_root / "desktop").iterdir() if p.is_dir())
            mobile_dirs = sorted(p.name for p in (guide_root / "mobile").iterdir() if p.is_dir())

        self.assertEqual(missing, [])
        self.assertEqual(desktop_dirs, self.TEMPLATE_IDS)
        self.assertEqual(mobile_dirs, self.TEMPLATE_IDS)
        self.assertFalse((output_root / "trips").exists())
        self.assertIn('data-template="editorial"', desktop_html)
        self.assertIn('data-device="desktop"', desktop_html)
        self.assertIn('data-template="editorial"', mobile_html)
        self.assertIn('data-device="mobile"', mobile_html)
        self.assertIn("site:", sources_md)
        self.assertIn("topic:", sources_md)
        self.assertIn("time_sensitive:", sources_md)

    def test_render_trip_site_renders_media_cards_and_source_metadata(self):
        model_payload = {
            "meta": {
                "trip_slug": "media-demo",
                "title": "Media Demo",
                "checked_at": "2026-04-12",
                "source_count": 1,
                "sample_reference": {"path": "sample.html", "density_mode": "match-sample"},
                "traveler_constraints": {
                    "has_children": True,
                    "has_seniors": False,
                    "requires_accessible_pace": True,
                    "avoid_long_unbroken_walks": True,
                },
                "distance_km": 1420,
                "transport_rule": {"long_distance": "over-1000km"},
            },
            "outputs": {
                "daily-overview": {
                    "summary": "先看整体安排",
                    "days": [
                        {
                            "title": "D1",
                            "summary": "到达后先在延吉市区轻松活动。",
                            "points": ["先吃午饭，再逛公园"],
                            "is_placeholder": False,
                        }
                    ],
                    "wearing": [],
                    "transport": [],
                    "alerts": [],
                    "sources": [],
                },
                "recommended": {
                    "recommended_route": [
                        {
                            "title": "南京出发高铁优先",
                            "summary": "超 1000km 时同步提供空铁联运备选。",
                            "points": ["步行段拆短，午后留出休息时间"],
                            "is_placeholder": False,
                        }
                    ],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [
                        {
                            "title": "长白山北坡",
                            "summary": "预留整天游玩会更从容。",
                            "points": ["门票 225 元", "建议提前 3 天预约"],
                            "is_placeholder": False,
                        }
                    ],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [
                        {
                            "title": "B站旅行 vlog",
                            "url": "https://example.com/video",
                            "type": "social",
                            "checked_at": "2026-04-12",
                            "site": "bilibili",
                            "topic": "attractions",
                            "time_sensitive": "no",
                        }
                    ],
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
            "sources": [
                {
                    "title": "B站旅行 vlog",
                    "url": "https://example.com/video",
                    "type": "social",
                    "checked_at": "2026-04-12",
                    "site": "bilibili",
                    "topic": "attractions",
                    "time_sensitive": "no",
                }
            ],
            "image_plan": {
                "cover": {
                    "image_hint": "天池晨雾",
                    "source_ref": "B站旅行 vlog",
                    "image_url": "https://cdn.example.com/bili-cover.jpg",
                },
                "section_images": [
                    {
                        "section": "attractions",
                        "image_hint": "长白山北坡栈道",
                        "source_ref": "B站旅行 vlog",
                        "image_url": "https://cdn.example.com/bili-shot.jpg",
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "media-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "media-demo")
            html = self._template_html(guide_root, "editorial", "desktop")
            sources_html = (guide_root / "notes" / "sources.html").read_text(encoding="utf-8")

        self.assertIn("天池晨雾", html)
        self.assertIn("长白山北坡栈道", html)
        self.assertIn("over-1000km", html)
        self.assertIn("bilibili", html)
        self.assertIn("https://cdn.example.com/bili-cover.jpg", html)
        self.assertIn("https://cdn.example.com/bili-shot.jpg", html)
        self.assertIn("<img", html)
        self.assertIn("attractions", sources_html)
        self.assertIn("time-sensitive", sources_html)

    def test_render_trip_site_skips_media_block_when_asset_not_publishable(self):
        model_payload = {
            "meta": {"trip_slug": "gate-demo", "title": "Gate Demo", "checked_at": "2026-04-13", "source_count": 1},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {
                "cover": {
                    "image_hint": "B站搜索：长白山北坡攻略",
                    "source_ref": "B站搜索：长白山北坡攻略",
                    "image_url": "",
                    "publish_state": "text-citation-only",
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "gate-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertNotIn("参考画面", html)
        self.assertNotIn("B站搜索：长白山北坡攻略", html)

    def test_render_trip_site_sanitizes_script_boundaries_and_unsafe_urls(self):
        model_payload = {
            "meta": {
                "trip_slug": "unsafe-demo",
                "title": "Unsafe Demo",
                "checked_at": "2026-04-11",
                "source_count": 1,
            },
            "outputs": {
                "daily-overview": {
                    "summary": "先看整体安排",
                    "days": [
                        {
                            "title": "D1",
                            "summary": "</script><script>alert(1)</script>",
                            "points": ["保持离线可分享"],
                            "is_placeholder": False,
                        }
                    ],
                    "wearing": [],
                    "transport": [],
                    "alerts": [],
                    "sources": [],
                },
                "recommended": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [
                        {
                            "title": "Unsafe Link",
                            "url": "javascript:alert(1)",
                            "type": "social",
                            "checked_at": "2026-04-11",
                            "site": "xiaohongshu",
                            "topic": "tips",
                            "time_sensitive": "yes",
                        }
                    ],
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
            "sources": [
                {
                    "title": "Unsafe Link",
                    "url": "javascript:alert(1)",
                    "type": "social",
                    "checked_at": "2026-04-11",
                    "site": "xiaohongshu",
                    "topic": "tips",
                    "time_sensitive": "yes",
                }
            ],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "unsafe-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            guide_root = self._guide_root(output_root, "unsafe-demo")
            html = self._template_html(guide_root, "editorial", "desktop")
            guide_js = (guide_root / "assets" / "guide-content.js").read_text(encoding="utf-8")

        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("\\u003c/script\\u003e\\u003cscript\\u003ealert(1)\\u003c/script\\u003e", guide_js)
        self.assertNotIn('href="javascript:alert(1)"', html)
        self.assertIn("暂无链接", html)

    def test_render_trip_site_daily_overview_uses_timeline_markup(self):
        model_payload = {
            "meta": {"trip_slug": "timeline-demo", "title": "Timeline Demo", "checked_at": "2026-04-12", "source_count": 0},
            "outputs": {
                "daily-overview": {
                    "summary": "两屏内先看全局安排",
                    "days": [
                        {"title": "D1 延吉", "summary": "早市加市区慢逛", "points": ["上午 早市", "下午 民俗园", "晚上 烧烤"], "is_placeholder": False},
                        {"title": "D2 长白山", "summary": "北坡整天", "points": ["上午 集散中心", "下午 天池瀑布", "晚上 二道白河"], "is_placeholder": False},
                    ],
                    "wearing": [],
                    "transport": [],
                    "alerts": [],
                    "sources": [],
                },
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "timeline-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "timeline-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertIn("timeline-stack", html)
        self.assertIn("timeline-card", html)
        self.assertIn("D1 延吉", html)

    def test_render_trip_site_renders_transport_matrix_and_grouped_food_titles(self):
        model_payload = {
            "meta": {"trip_slug": "matrix-demo", "title": "Matrix Demo", "checked_at": "2026-04-12", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {
                    "recommended_route": [],
                    "route_options": [
                        {
                            "title": "交通决策",
                            "summary": "先看大交通方案。",
                            "points": ["高铁优先最稳妥。"],
                            "transport_matrix": [
                                {"name": "高铁优先", "schedule": "G101 06:30-15:00", "price": "780 元起", "duration": "8小时30分"},
                                {"name": "空铁联运", "schedule": "MU+高铁", "price": "950 元起", "duration": "6小时40分"},
                            ],
                            "is_placeholder": False,
                        }
                    ],
                    "clothing_guide": [],
                    "attractions": [],
                    "transport_details": [],
                    "food_by_city": [
                        {"title": "延吉 · 朝鲜族", "summary": "冷面与包饭", "points": ["服务大楼冷面"], "is_placeholder": False},
                        {"title": "延吉 · 烧烤", "summary": "晚餐氛围更足", "points": ["丰茂串城"], "is_placeholder": False},
                    ],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "matrix-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "matrix-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertIn("transport-matrix", html)
        self.assertIn("高铁优先", html)
        self.assertIn("延吉 · 朝鲜族", html)
        self.assertIn("延吉 · 烧烤", html)

    def test_render_trip_site_renders_transport_access_cards_and_food_group_cards(self):
        model_payload = {
            "meta": {"trip_slug": "density-render-demo", "title": "Density Render Demo", "checked_at": "2026-04-12", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [],
                    "transport_details": [
                        {
                            "title": "全景接驳总览",
                            "summary": "把大交通和落地接驳放在一张卡里。",
                            "points": ["公交可补位", "地铁可覆盖城市段", "打车更省时", "自驾更灵活"],
                            "card_kind": "transport-access",
                            "is_placeholder": False,
                        }
                    ],
                    "food_by_city": [
                        {
                            "title": "延吉 · 朝鲜族概览",
                            "summary": "先看这组代表性店铺。",
                            "points": ["1 家可选", "代表菜：冷面、锅包肉"],
                            "card_kind": "food-group",
                            "is_placeholder": False,
                        },
                        {
                            "title": "延吉 · 朝鲜族",
                            "summary": "午餐适合安排冷面。",
                            "points": ["店名：服务大楼冷面"],
                            "is_placeholder": False,
                        },
                    ],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "density-render-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "density-render-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertIn("transport-access-card", html)
        self.assertIn("food-group-card", html)
        self.assertIn("延吉 · 朝鲜族概览", html)
        self.assertIn("公交可补位", html)

    def test_render_trip_site_renders_inline_source_meta_on_cards(self):
        model_payload = {
            "meta": {"trip_slug": "inline-source-demo", "title": "Inline Source Demo", "checked_at": "2026-04-12", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [
                        {
                            "title": "长白山北坡",
                            "summary": "适合整天安排。",
                            "points": ["费用参考：225 元"],
                            "source_meta": {
                                "title": "景区公告",
                                "url": "https://example.com/attraction",
                                "type": "official",
                                "checked_at": "2026-04-12",
                                "site": "official",
                                "topic": "attractions",
                                "time_sensitive": "no",
                            },
                            "is_placeholder": False,
                        }
                    ],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "inline-source-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "inline-source-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertIn("card-source-meta", html)
        self.assertIn("景区公告", html)
        self.assertIn("official", html)
        self.assertIn("2026-04-12", html)
        self.assertIn("https://example.com/attraction", html)

    def test_render_trip_site_renders_inline_card_media(self):
        model_payload = {
            "meta": {"trip_slug": "card-media-render-demo", "title": "Card Media Render Demo", "checked_at": "2026-04-12", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [
                        {
                            "title": "长白山北坡",
                            "summary": "适合整天安排。",
                            "points": ["费用参考：225 元"],
                            "card_media": {
                                "image_hint": "北坡栈道",
                                "source_ref": "景区公告",
                                "image_url": "https://cdn.example.com/attraction.jpg",
                                "image_source_kind": "timeline-shot",
                            },
                            "is_placeholder": False,
                        }
                    ],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "card-media-render-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "card-media-render-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertIn("card-inline-media", html)
        self.assertIn("北坡栈道", html)
        self.assertIn("https://cdn.example.com/attraction.jpg", html)

    def test_render_trip_site_renders_comment_highlights_on_cards(self):
        model_payload = {
            "meta": {"trip_slug": "comment-render-demo", "title": "Comment Render Demo", "checked_at": "2026-04-12", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {
                    "recommended_route": [],
                    "route_options": [],
                    "clothing_guide": [],
                    "attractions": [
                        {
                            "title": "Changbai North Slope",
                            "summary": "full day route",
                            "points": ["ticket: 225 CNY"],
                            "comment_highlights": [
                                "arrive before 08:30 for a smoother shuttle queue",
                                "the boardwalk photos look best before noon",
                            ],
                            "is_placeholder": False,
                        }
                    ],
                    "transport_details": [],
                    "food_by_city": [],
                    "tips": [],
                    "sources": [],
                },
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "comment-render-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root, "--style", "editorial")
            guide_root = self._guide_root(output_root, "comment-render-demo")
            html = self._template_html(guide_root, "editorial", "desktop")

        self.assertIn("card-comment-strip", html)
        self.assertIn("card-comment-list", html)
        self.assertIn("arrive before 08:30 for a smoother shuttle queue", html)
        self.assertIn("the boardwalk photos look best before noon", html)

    def test_render_trip_site_default_emits_all_five_templates(self):
        model_payload = {
            "meta": {"trip_slug": "render-default-demo", "title": "Render Default Demo", "checked_at": "2026-04-13", "source_count": 0},
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            desktop_dirs = sorted(
                p.name for p in (output_root / "guides" / "render-default-demo" / "desktop").iterdir() if p.is_dir()
            )

        self.assertEqual(desktop_dirs, self.TEMPLATE_IDS)

    def test_render_trip_site_never_renders_sample_reference_chip(self):
        model_payload = {
            "meta": {
                "trip_slug": "sample-leak-demo",
                "title": "Sample Leak Demo",
                "checked_at": "2026-04-13",
                "source_count": 0,
                "sample_reference": {"path": "sample.html", "density_mode": "match-sample"},
            },
            "outputs": {
                "daily-overview": {"summary": "", "days": [], "wearing": [], "transport": [], "alerts": [], "sources": []},
                "recommended": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
                "comprehensive": {"recommended_route": [], "route_options": [], "clothing_guide": [], "attractions": [], "transport_details": [], "food_by_city": [], "tips": [], "sources": []},
            },
            "sources": [],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            html = (
                output_root / "guides" / "sample-leak-demo" / "desktop" / "editorial" / "index.html"
            ).read_text(encoding="utf-8")

        self.assertNotIn("对标样本", html)
        self.assertNotIn("sample.html", html)

    def test_build_image_plan_preserves_publish_state_for_render_gate(self):
        payload = {
            "items": [
                {
                    "title": "B站攻略",
                    "publish_state": "text-citation-only",
                    "recommended_usage": "attractions.hero",
                    "shot_candidates": [{"label": "无真实图片"}],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "output.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "build_image_plan.py", "--input", input_path, "--output", output_path)
            image_plan = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(image_plan["cover"]["publish_state"], "text-citation-only")
        self.assertEqual(image_plan["cover"]["image_url"], "")

    def test_export_single_html_and_package_trip_outputs_share_html_zip_and_portal_descriptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = write_sample_approved_research(Path(tmp) / "approved_research.json")
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            dist = output_root / "dist"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            payload = json.loads(model.read_text(encoding="utf-8"))
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root, "--style", "all")
            guide_root = self._guide_root(output_root, payload["meta"]["trip_slug"])
            run_script(SKILL_DIR / "scripts" / "build_portal.py", "--guide-root", guide_root, "--output", dist / "portal.html")
            run_script(
                SKILL_DIR / "scripts" / "export_single_html.py",
                "--guide-root",
                guide_root,
                "--template",
                "editorial",
                "--output",
                dist / "recommended.html",
            )
            run_script(
                SKILL_DIR / "scripts" / "export_single_html.py",
                "--guide-root",
                guide_root,
                "--template",
                "editorial",
                "--output",
                dist / "share.html",
            )
            run_script(
                SKILL_DIR / "scripts" / "package_trip.py",
                "--guide-root",
                guide_root,
                "--portal",
                dist / "portal.html",
                "--recommended-html",
                dist / "recommended.html",
                "--comprehensive-html",
                dist / "share.html",
                "--output",
                dist / "wuyi-yanji-changbaishan.zip",
            )
            portal_html = (dist / "portal.html").read_text(encoding="utf-8")
            recommended_html = (dist / "recommended.html").read_text(encoding="utf-8")
            share_html = (dist / "share.html").read_text(encoding="utf-8")
            with zipfile.ZipFile(dist / "wuyi-yanji-changbaishan.zip") as archive:
                names = sorted(archive.namelist())

        self.assertIn("桌面端", portal_html)
        self.assertIn("手机端", portal_html)
        self.assertIn("单文件", portal_html)
        self.assertIn("来源说明", portal_html)
        self.assertIn("ZIP", portal_html)
        self.assertNotIn('href="../../assets/base.css"', recommended_html)
        self.assertNotIn("<script src=", recommended_html)
        self.assertNotIn('href="../../assets/base.css"', share_html)
        self.assertIn("portal.html", names)
        self.assertIn("recommended.html", names)
        self.assertIn("share.html", names)
        self.assertIn("notes/sources.md", names)
        self.assertIn("notes/sources.html", names)
        self.assertIn("trip-summary.txt", names)

    def test_render_trip_site_can_emit_all_template_variants_and_portal_lists_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = write_sample_approved_research(Path(tmp) / "approved_research.json")
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            dist = output_root / "dist"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            payload = json.loads(model.read_text(encoding="utf-8"))
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root, "--style", "all")
            guide_root = self._guide_root(output_root, payload["meta"]["trip_slug"])
            run_script(SKILL_DIR / "scripts" / "build_portal.py", "--guide-root", guide_root, "--output", dist / "portal.html")
            run_script(
                SKILL_DIR / "scripts" / "export_single_html.py",
                "--guide-root",
                guide_root,
                "--template",
                "editorial",
                "--output",
                dist / "editorial.html",
            )
            portal_html = (dist / "portal.html").read_text(encoding="utf-8")
            lifestyle_html = (dist / "editorial.html").read_text(encoding="utf-8")
            for template_id in self.TEMPLATE_IDS:
                self.assertTrue((guide_root / "desktop" / template_id / "index.html").exists())
                self.assertTrue((guide_root / "mobile" / template_id / "index.html").exists())
                self.assertIn(template_id, portal_html)
            self.assertNotIn('href="../../assets/base.css"', lifestyle_html)


if __name__ == "__main__":
    unittest.main()
