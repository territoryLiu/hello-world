import sys
import unittest
from pathlib import Path
import shutil


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from package_trip import package_trip  # noqa: E402


class PackageTripTest(unittest.TestCase):
    def test_package_trip_blocks_when_delivery_gate_fails(self):
        root = TEST_TMP_ROOT / "package-trip-gate"
        if root.exists():
            shutil.rmtree(root)

        guide_root = root / "travel-data" / "guides" / "demo-trip"
        trip_root = root / "travel-data" / "trips" / "demo-trip"
        output_root = root / "dist"
        guide_root.mkdir(parents=True, exist_ok=True)
        trip_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)

        portal = guide_root / "portal.html"
        recommended = guide_root / "recommended.html"
        share = guide_root / "share.html"
        notes = guide_root / "notes"
        notes.mkdir(parents=True, exist_ok=True)

        portal.write_text("<html></html>", encoding="utf-8")
        recommended.write_text("<html></html>", encoding="utf-8")
        share.write_text("<html></html>", encoding="utf-8")
        (notes / "sources.md").write_text("sources", encoding="utf-8")
        (notes / "sources.html").write_text("<html></html>", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "delivery gate failed"):
            package_trip(guide_root, portal, recommended, share, output_root / "demo.zip")


if __name__ == "__main__":
    unittest.main()
