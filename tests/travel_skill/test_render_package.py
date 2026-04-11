from pathlib import Path
import json
import tempfile
import unittest
import zipfile

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class RenderPackageTest(unittest.TestCase):
    def test_render_trip_site_creates_required_layered_structure(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            payload = json.loads(model.read_text(encoding="utf-8"))
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            trip_root = output_root / "trips" / payload["meta"]["trip_slug"]
            required = [
                trip_root / "desktop" / "daily-overview" / "index.html",
                trip_root / "desktop" / "recommended" / "index.html",
                trip_root / "desktop" / "comprehensive" / "index.html",
                trip_root / "mobile" / "daily-overview" / "index.html",
                trip_root / "mobile" / "recommended" / "index.html",
                trip_root / "mobile" / "comprehensive" / "index.html",
                trip_root / "assets" / "base.css",
                trip_root / "assets" / "render-guide.js",
                trip_root / "assets" / "guide-content.js",
                trip_root / "notes" / "sources.md",
            ]
            desktop_html = (trip_root / "desktop" / "recommended" / "index.html").read_text(encoding="utf-8")
            mobile_html = (trip_root / "mobile" / "recommended" / "index.html").read_text(encoding="utf-8")
            css = (trip_root / "assets" / "base.css").read_text(encoding="utf-8")
            missing = [str(path) for path in required if not path.exists()]

        self.assertEqual(missing, [])
        self.assertIn('data-layer="recommended"', desktop_html)
        self.assertIn('data-device="desktop"', desktop_html)
        self.assertIn('data-layer="recommended"', mobile_html)
        self.assertIn('data-device="mobile"', mobile_html)
        self.assertIn("--theme-accent", css)
        self.assertIn('id="recommended_route"', desktop_html)
        self.assertIn('id="route_options"', desktop_html)
        self.assertIn('id="clothing_guide"', desktop_html)
        self.assertIn('id="transport_details"', desktop_html)

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
                }
            ],
            "image_plan": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "unsafe-model.json"
            output_root = Path(tmp) / "out"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            html = (output_root / "trips" / "unsafe-demo" / "desktop" / "daily-overview" / "index.html").read_text(encoding="utf-8")
            guide_js = (output_root / "trips" / "unsafe-demo" / "assets" / "guide-content.js").read_text(encoding="utf-8")

        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("\\u003c/script\\u003e\\u003cscript\\u003ealert(1)\\u003c/script\\u003e", guide_js)
        self.assertNotIn('href="javascript:alert(1)"', html)
        self.assertIn("暂无链接", html)

    def test_export_single_html_and_package_trip_outputs_share_html_and_zip(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            dist = output_root / "dist"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            payload = json.loads(model.read_text(encoding="utf-8"))
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            trip_root = output_root / "trips" / payload["meta"]["trip_slug"]
            run_script(SKILL_DIR / "scripts" / "build_portal.py", "--guide-root", trip_root, "--output", dist / "portal.html")
            run_script(
                SKILL_DIR / "scripts" / "export_single_html.py",
                "--guide-root",
                trip_root,
                "--layer",
                "recommended",
                "--output",
                dist / "recommended.html",
            )
            run_script(
                SKILL_DIR / "scripts" / "export_single_html.py",
                "--guide-root",
                trip_root,
                "--layer",
                "comprehensive",
                "--output",
                dist / "share.html",
            )
            run_script(
                SKILL_DIR / "scripts" / "package_trip.py",
                "--guide-root",
                trip_root,
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

        self.assertIn("share.html", portal_html)
        self.assertIn("recommended.html", portal_html)
        self.assertNotIn('href="../../assets/base.css"', recommended_html)
        self.assertNotIn("<script src=", recommended_html)
        self.assertNotIn('href="../../assets/base.css"', share_html)
        self.assertIn("portal.html", names)
        self.assertIn("recommended.html", names)
        self.assertIn("share.html", names)
        self.assertIn("notes/sources.md", names)
        self.assertIn("trip-summary.txt", names)


if __name__ == "__main__":
    unittest.main()
