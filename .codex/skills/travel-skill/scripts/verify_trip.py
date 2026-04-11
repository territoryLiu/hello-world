from pathlib import Path
import argparse
import json
import subprocess
import sys


def collect_static(guide_root: Path, single_html: Path) -> dict:
    return {
        "desktop_exists": (guide_root / "desktop" / "index.html").exists(),
        "mobile_exists": (guide_root / "mobile" / "index.html").exists(),
        "single_html_exists": single_html.exists(),
        "sources_exists": (guide_root / "notes" / "sources.md").exists(),
    }


def checker_script_path() -> Path:
    return Path(__file__).resolve().parents[4] / "tests" / "playwright_trip_render_check.py"


def run_browser_check(guide_root: Path) -> str:
    checker = checker_script_path()
    if not checker.exists():
        raise FileNotFoundError(f"Playwright checker not found: {checker}")
    subprocess.run(
        [
            sys.executable,
            str(checker),
            "--guide-root",
            str(guide_root),
        ],
        check=True,
    )
    return "passed"


def has_static_failures(static_checks: dict) -> bool:
    return not all(bool(value) for value in static_checks.values())


def verify_trip(guide_root: Path, single_html: Path, skip_browser: bool) -> dict:
    result = {
        "static_checks": collect_static(guide_root, single_html),
        "browser_check": "skipped",
    }
    if not skip_browser:
        result["browser_check"] = run_browser_check(guide_root)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--single-html", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--skip-browser", action="store_true")
    args = parser.parse_args()

    guide_root = Path(args.guide_root)
    single_html = Path(args.single_html)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = verify_trip(guide_root, single_html, args.skip_browser)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if has_static_failures(payload["static_checks"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
