import sys
import unittest
import zipfile
from pathlib import Path
import shutil


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from package_skill_release import package_skill  # noqa: E402


class PackageSkillReleaseTest(unittest.TestCase):
    def test_package_skill_keeps_runtime_files_and_excludes_caches(self):
        root = TEST_TMP_ROOT / "package-skill-release" / "travel-skill"
        output_zip = TEST_TMP_ROOT / "package-skill-release" / "dist" / "travel-skill.zip"
        if root.parent.exists():
            shutil.rmtree(root.parent)
        (root / "scripts").mkdir(parents=True)
        (root / "references").mkdir(parents=True)
        (root / "assets" / "templates").mkdir(parents=True)
        (root / "tests").mkdir(parents=True)
        (root / "testdata").mkdir(parents=True)
        (root / "scripts" / "__pycache__").mkdir(parents=True)

        (root / "SKILL.md").write_text("skill", encoding="utf-8")
        (root / "scripts" / "main.py").write_text("print('ok')", encoding="utf-8")
        (root / "references" / "guide.md").write_text("docs", encoding="utf-8")
        (root / "assets" / "templates" / "base.css").write_text("body{}", encoding="utf-8")
        (root / "tests" / "test_smoke.py").write_text("pass", encoding="utf-8")
        (root / "testdata" / "sample.mp4").write_text("fake", encoding="utf-8")
        (root / "scripts" / "__pycache__" / "main.cpython-312.pyc").write_bytes(b"pyc")

        package_skill(root, output_zip)

        with zipfile.ZipFile(output_zip) as archive:
            names = set(archive.namelist())

        self.assertIn("travel-skill/SKILL.md", names)
        self.assertIn("travel-skill/scripts/main.py", names)
        self.assertIn("travel-skill/references/guide.md", names)
        self.assertIn("travel-skill/assets/templates/base.css", names)
        self.assertIn("travel-skill/tests/test_smoke.py", names)
        self.assertIn("travel-skill/testdata/sample.mp4", names)
        self.assertNotIn("travel-skill/scripts/__pycache__/main.cpython-312.pyc", names)


if __name__ == "__main__":
    unittest.main()
