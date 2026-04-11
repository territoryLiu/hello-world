from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

import tests.playwright_trip_render_check as render_check
from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


def load_verify_trip_module():
    module_path = SKILL_DIR / "scripts" / "verify_trip.py"
    spec = importlib.util.spec_from_file_location("travel_skill_verify_trip", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyPipelineTest(unittest.TestCase):
    def test_verify_trip_reports_required_files_without_browser(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            report = output_root / "verify" / "report.json"
            single_html = output_root / "dist" / "wuyi-yanji-changbaishan.html"
            guide_root = output_root / "trips" / "wuyi-yanji-changbaishan"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root)
            run_script(SKILL_DIR / "scripts" / "export_single_html.py", "--guide-root", guide_root, "--output", single_html)
            run_script(
                SKILL_DIR / "scripts" / "verify_trip.py",
                "--guide-root",
                guide_root,
                "--single-html",
                single_html,
                "--report",
                report,
                "--skip-browser",
            )
            payload = json.loads(report.read_text(encoding="utf-8"))

        self.assertTrue(payload["static_checks"]["desktop_exists"])
        self.assertTrue(payload["static_checks"]["mobile_exists"])
        self.assertTrue(payload["static_checks"]["single_html_exists"])
        self.assertTrue(payload["static_checks"]["sources_exists"])
        self.assertEqual(payload["browser_check"], "skipped")

    def test_playwright_checker_resolves_relative_guide_root(self):
        guide_root = render_check.resolve_guide_root(Path(".\\trips\\jilin-yanji-changbaishan"))
        pages = render_check.pages_for(guide_root)

        self.assertTrue(guide_root.is_absolute())
        self.assertTrue(all(page.is_absolute() for page in pages))

    def test_verify_trip_resolves_existing_checker_script(self):
        module = load_verify_trip_module()
        checker_path = module.checker_script_path()

        self.assertTrue(checker_path.exists())
        self.assertEqual(checker_path.name, "playwright_trip_render_check.py")

    def test_verify_trip_returns_nonzero_when_required_artifacts_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "missing-guide"
            single_html = Path(tmp) / "missing.html"
            report = Path(tmp) / "report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_DIR / "scripts" / "verify_trip.py"),
                    "--guide-root",
                    str(guide_root),
                    "--single-html",
                    str(single_html),
                    "--report",
                    str(report),
                    "--skip-browser",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(report.read_text(encoding="utf-8"))

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["static_checks"]["desktop_exists"])
        self.assertFalse(payload["static_checks"]["mobile_exists"])
        self.assertFalse(payload["static_checks"]["single_html_exists"])
        self.assertFalse(payload["static_checks"]["sources_exists"])


if __name__ == "__main__":
    unittest.main()
