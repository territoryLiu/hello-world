from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import ROOT, SKILL_DIR, run_script


def load_verify_trip_module():
    module_path = SKILL_DIR / "scripts" / "verify_trip.py"
    spec = importlib.util.spec_from_file_location("travel_skill_verify_trip", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyPipelineTest(unittest.TestCase):
    def test_verify_trip_reports_content_checks_for_guides_root(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "approved_research.json"
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "guide-content.json"
            output_root = Path(tmp) / "out"
            report = output_root / "verify" / "report.json"
            guide_root = output_root / "guides" / "wuyi-yanji-changbaishan"
            run_script(SKILL_DIR / "scripts" / "build_guide_model.py", "--input", fixture, "--output", model)
            run_script(SKILL_DIR / "scripts" / "fill_missing_sections.py", "--input", model, "--output", model)
            run_script(SKILL_DIR / "scripts" / "render_trip_site.py", "--input", model, "--output-root", output_root, "--style", "all")
            run_script(
                SKILL_DIR / "scripts" / "verify_trip.py",
                "--guide-root",
                guide_root,
                "--output",
                report,
            )
            payload = json.loads(report.read_text(encoding="utf-8"))

        self.assertIn("content_checks", payload)
        self.assertTrue(payload["content_checks"]["exactly_five_templates"])
        self.assertTrue(payload["content_checks"]["no_sample_reference_in_publish"])
        self.assertTrue(payload["content_checks"]["no_fake_media_blocks"])
        self.assertIn(payload["status"], {"pass", "warn"})

    def test_verify_trip_flags_fake_media_and_legacy_outputs(self):
        module = load_verify_trip_module()
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "guides" / "demo-trip"
            (guide_root / "desktop" / "route-first").mkdir(parents=True)
            (guide_root / "desktop" / "route-first" / "index.html").write_text(
                "对标样本 B站搜索：长白山北坡攻略",
                encoding="utf-8",
            )
            payload = module.verify_trip(guide_root)

        self.assertIn("no_sample_reference_in_publish", payload["content_checks"])
        self.assertFalse(payload["content_checks"]["no_sample_reference_in_publish"])
        self.assertFalse(payload["content_checks"]["no_fake_media_blocks"])
        self.assertFalse(payload["content_checks"]["exactly_five_templates"])

    def test_verify_trip_fails_when_mobile_output_is_missing(self):
        module = load_verify_trip_module()
        with tempfile.TemporaryDirectory() as tmp:
            guide_root = Path(tmp) / "guides" / "demo-trip"
            for template_id in ["decision-first", "destination-first", "lifestyle-first", "route-first", "transport-first"]:
                (guide_root / "desktop" / template_id).mkdir(parents=True)
                (guide_root / "desktop" / template_id / "index.html").write_text("中文页面", encoding="utf-8")
            payload = module.verify_trip(guide_root)

        self.assertEqual(payload["status"], "fail")
        self.assertFalse(payload["content_checks"]["mobile_templates_complete"])

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
        self.assertFalse(payload["content_checks"]["exactly_five_templates"])


if __name__ == "__main__":
    unittest.main()
