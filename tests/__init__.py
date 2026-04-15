import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
HOST_ROOT = ROOT.parents[1] if ROOT.parent.name == ".worktrees" else ROOT
TEST_TMP_ROOT = HOST_ROOT / ".tmp-tests"
TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["TMPDIR"] = str(TEST_TMP_ROOT)
os.environ["TMP"] = str(TEST_TMP_ROOT)
os.environ["TEMP"] = str(TEST_TMP_ROOT)
tempfile.tempdir = str(TEST_TMP_ROOT)


class _WorkspaceTemporaryDirectory:
    def __init__(self, suffix="", prefix="tmp", dir=None, ignore_cleanup_errors=False):
        base_dir = Path(dir) if dir else TEST_TMP_ROOT
        token = f"{prefix}{uuid4().hex}{suffix}"
        self.name = str(base_dir / token)
        self._ignore_cleanup_errors = ignore_cleanup_errors

    def __enter__(self):
        Path(self.name).mkdir(parents=True, exist_ok=False)
        return self.name

    def cleanup(self):
        shutil.rmtree(self.name, ignore_errors=self._ignore_cleanup_errors)

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()


tempfile.TemporaryDirectory = _WorkspaceTemporaryDirectory
