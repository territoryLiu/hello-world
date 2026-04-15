from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import SKILL_DIR, run_script, write_sample_approved_research


def load_verify_trip_module():
    module_path = SKILL_DIR / "scripts" / "verify_trip.py"
    spec = importlib.util.spec_from_file_location("travel_skill_verify_trip", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyPipelineTest(unittest.TestCase):
    def test_verify_trip_reports_content_checks_for_guides_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = write_sample_approved_research(Path(tmp) / "approved_research.json")
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            report = output_root / "verify" / "report.json"
            guide_root = output_root / "guides" / "wuyi-yanji-changbaishan"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root, "--style", "all")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_DIR / "scripts" / "verify_trip.py"),
                    "--guide-root",
                    str(guide_root),
                    "--output",
                    str(report),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(report.read_text(encoding="utf-8"))

        self.assertIn("content_checks", payload)
        self.assertTrue(payload["content_checks"]["desktop_template_complete"])
        self.assertTrue(payload["content_checks"]["mobile_template_complete"])
        self.assertTrue(payload["content_checks"]["single_template_is_editorial"])
        self.assertTrue(payload["content_checks"]["no_sample_reference_in_publish"])
        self.assertTrue(payload["content_checks"]["no_fake_media_blocks"])
        self.assertTrue(payload["content_checks"]["research_report_present"])
        self.assertTrue(payload["content_checks"]["coverage_overview_present"])
        self.assertTrue(payload["content_checks"]["dual_time_layer_present"])
        self.assertEqual(result.returncode, 0)
        self.assertIn(payload["status"], {"pass", "warn"})

    def test_verify_trip_flags_fake_media_and_legacy_outputs(self):
        module = load_verify_trip_module()
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "guides" / "demo-trip"
            (guide_root / "desktop" / "route-first").mkdir(parents=True)
            (guide_root / "desktop" / "route-first" / "index.html").write_text(
                "瀵规爣鏍锋湰 sample.html B绔欐悳绱細闀跨櫧灞卞寳鍧℃敾鐣? text-citation-only",
                encoding="utf-8",
            )
            payload = module.verify_trip(guide_root)

        self.assertIn("no_sample_reference_in_publish", payload["content_checks"])
        self.assertFalse(payload["content_checks"]["no_sample_reference_in_publish"])
        self.assertFalse(payload["content_checks"]["no_fake_media_blocks"])
        self.assertFalse(payload["content_checks"]["desktop_template_complete"])
        self.assertFalse(payload["content_checks"]["single_template_is_editorial"])

    def test_verify_trip_fails_when_mobile_output_is_missing(self):
        module = load_verify_trip_module()
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "guides" / "demo-trip"
            (guide_root / "desktop" / "editorial").mkdir(parents=True)
            (guide_root / "desktop" / "editorial" / "index.html").write_text("涓枃椤甸潰", encoding="utf-8")
            payload = module.verify_trip(guide_root)

        self.assertEqual(payload["status"], "fail")
        self.assertFalse(payload["content_checks"]["mobile_template_complete"])

    def test_verify_trip_returns_nonzero_when_required_artifacts_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "missing-guide"
            report = Path(tmp) / "report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_DIR / "scripts" / "verify_trip.py"),
                    "--guide-root",
                    str(guide_root),
                    "--output",
                    str(report),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(report.read_text(encoding="utf-8"))

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["content_checks"]["single_template_is_editorial"])


if __name__ == "__main__":
    unittest.main()
