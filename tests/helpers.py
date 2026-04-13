from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".codex" / "skills" / "travel-skill"
PYTHON = sys.executable


def run_script(*parts):
    cmd = [PYTHON, *(str(part) for part in parts)]
    return subprocess.run(cmd, check=True, capture_output=True, text=True)
