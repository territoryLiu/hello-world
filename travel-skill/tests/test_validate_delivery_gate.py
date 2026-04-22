import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_delivery_gate import infer_trip_root, validate_delivery_gate  # noqa: E402


class ValidateDeliveryGateTest(unittest.TestCase):
    def test_infers_trip_root_from_guide_root(self):
        guide_root = REPO_ROOT / "travel-data" / "guides" / "demo-trip"
        inferred = infer_trip_root(guide_root)
        self.assertEqual(inferred, REPO_ROOT / "travel-data" / "trips" / "demo-trip")

    def test_fails_when_gate_and_coverage_are_missing(self):
        root = TEST_TMP_ROOT / "validate-delivery-gate-missing"
        if root.exists():
            import shutil

            shutil.rmtree(root)
        guide_root = root / "travel-data" / "guides" / "demo-trip"
        trip_root = root / "travel-data" / "trips" / "demo-trip"
        guide_root.mkdir(parents=True, exist_ok=True)
        trip_root.mkdir(parents=True, exist_ok=True)

        report = validate_delivery_gate(guide_root, trip_root)
        self.assertEqual(report["status"], "fail")
        self.assertIn("intake_gate", report["failed_checks"])
        self.assertIn("cdp_or_web_access", report["failed_checks"])
        self.assertIn("platform_coverage", report["failed_checks"])

    def test_passes_with_gate_web_access_record_and_required_site_statuses(self):
        root = TEST_TMP_ROOT / "validate-delivery-gate-pass"
        if root.exists():
            import shutil

            shutil.rmtree(root)
        guide_root = root / "travel-data" / "guides" / "demo-trip"
        trip_root = root / "travel-data" / "trips" / "demo-trip"
        (trip_root / "request").mkdir(parents=True, exist_ok=True)
        (trip_root / "research" / "web-results").mkdir(parents=True, exist_ok=True)
        guide_root.mkdir(parents=True, exist_ok=True)

        (trip_root / "request" / "gate-report.json").write_text(
            json.dumps({"can_proceed": True}, ensure_ascii=False),
            encoding="utf-8",
        )
        (trip_root / "research" / "web-results" / "one-run.json").write_text("{}", encoding="utf-8")
        (trip_root / "research" / "batch-coverage.json").write_text(
            json.dumps(
                {
                    "by_site": {
                        "xiaohongshu": {"coverage_status": "failed"},
                        "douyin": {"coverage_status": "partial"},
                        "bilibili": {"coverage_status": "complete"},
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        report = validate_delivery_gate(guide_root, trip_root)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["checks"]["platform_coverage"]["site_statuses"]["xiaohongshu"], "failed")

    def test_fails_when_required_site_has_no_coverage_status(self):
        root = TEST_TMP_ROOT / "validate-delivery-gate-missing-status"
        if root.exists():
            import shutil

            shutil.rmtree(root)
        guide_root = root / "travel-data" / "guides" / "demo-trip"
        trip_root = root / "travel-data" / "trips" / "demo-trip"
        (trip_root / "request").mkdir(parents=True, exist_ok=True)
        (trip_root / "research").mkdir(parents=True, exist_ok=True)
        guide_root.mkdir(parents=True, exist_ok=True)

        (trip_root / "request" / "gate-report.json").write_text(
            json.dumps({"can_proceed": True}, ensure_ascii=False),
            encoding="utf-8",
        )
        (trip_root / "research" / "cdp-status.json").write_text(
            json.dumps({"chrome": "ok", "proxy": "ready"}, ensure_ascii=False),
            encoding="utf-8",
        )
        (trip_root / "research" / "batch-coverage.json").write_text(
            json.dumps(
                {
                    "by_site": {
                        "xiaohongshu": {"coverage_status": "failed"},
                        "douyin": {"coverage_status": ""},
                        "bilibili": {"coverage_status": "complete"},
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        report = validate_delivery_gate(guide_root, trip_root)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["checks"]["platform_coverage"]["reason"], "coverage_status_missing")
        self.assertIn("douyin", report["checks"]["platform_coverage"]["missing_status_sites"])


if __name__ == "__main__":
    unittest.main()
