from pathlib import Path
import json
import tempfile
import unittest
import zipfile

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class RenderPackageTest(unittest.TestCase):
    def test_render_trip_site_creates_required_structure(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            trip_root = output_root / "trips" / "wuyi-yanji-changbaishan"
            required = [
                trip_root / "desktop" / "index.html",
                trip_root / "mobile" / "index.html",
                trip_root / "assets" / "base.css",
                trip_root / "assets" / "render-guide.js",
                trip_root / "assets" / "guide-content.js",
                trip_root / "notes" / "sources.md",
            ]
            self.assertEqual([str(path) for path in required if not path.exists()], [])

    def test_export_single_html_and_package_trip_inline_assets(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            dist = output_root / "dist"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            trip_root = output_root / "trips" / "wuyi-yanji-changbaishan"
            run_script(SKILL_DIR / "scripts" / "export_single_html.py", "--guide-root", trip_root, "--output", dist / "wuyi-yanji-changbaishan.html")
            run_script(
                SKILL_DIR / "scripts" / "package_trip.py",
                "--guide-root",
                trip_root,
                "--single-html",
                dist / "wuyi-yanji-changbaishan.html",
                "--output",
                dist / "wuyi-yanji-changbaishan.zip",
            )
            html = (dist / "wuyi-yanji-changbaishan.html").read_text(encoding="utf-8")
            with zipfile.ZipFile(dist / "wuyi-yanji-changbaishan.zip") as archive:
                names = sorted(archive.namelist())
        self.assertNotIn("href=\"../assets/base.css\"", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("../assets", html)
        self.assertIn("class=\"is-placeholder\"", html)
        self.assertIn("wuyi-yanji-changbaishan.html", names)
        self.assertIn("trip-summary.txt", names)
        self.assertIn("notes/sources.md", names)

    def test_render_and_export_sanitize_script_boundaries_and_unsafe_urls(self):
        model_payload = {
            "meta": {
                "trip_slug": "unsafe-demo",
                "title": "Unsafe Demo",
                "checked_at": "2026-04-11",
                "source_count": 1,
            },
            "sections": {
                "overview": [
                    {
                        "title": "概览",
                        "summary": "</script><script>alert(1)</script>",
                        "points": ["保持离线可分享"],
                        "is_placeholder": False,
                    }
                ],
                "recommended": [],
                "options": [],
                "attractions": [],
                "food": [],
                "season": [],
                "packing": [],
                "transport": [],
                "sources": [
                    {
                        "title": "Unsafe Link",
                        "url": "javascript:alert(1)",
                        "type": "social",
                        "checked_at": "2026-04-11",
                    }
                ],
            },
            "execution": {
                "booking_order": [],
                "daily_table": [],
                "budget_bands": [],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "unsafe-model.json"
            output_root = Path(tmp) / "out"
            single_html = output_root / "dist" / "unsafe-demo.html"
            input_path.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", input_path, "--output-root", output_root)
            run_script(SKILL_DIR / "scripts" / "export_single_html.py", "--guide-root", output_root / "trips" / "unsafe-demo", "--output", single_html)
            html = single_html.read_text(encoding="utf-8")

        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("\\u003c/script\\u003e\\u003cscript\\u003ealert(1)\\u003c/script\\u003e", html)
        self.assertNotIn('href="javascript:alert(1)"', html)
        self.assertIn("暂无链接", html)


if __name__ == "__main__":
    unittest.main()
