from pathlib import Path
import argparse
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import SORTED_TEMPLATE_IDS as EXPECTED_TEMPLATES
from verify_render_with_playwright import verify_render as verify_render_with_playwright


def scan_html_text(root: Path) -> str:
    if not root.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.html"))


def _template_dirs(root: Path, device: str) -> list[str]:
    template_root = root / device
    if not template_root.exists():
        return []
    return sorted(path.name for path in template_root.iterdir() if path.is_dir())


def verify_trip(guide_root: Path) -> dict:
    html_blob = scan_html_text(guide_root)
    desktop_templates = _template_dirs(guide_root, "desktop")
    mobile_templates = _template_dirs(guide_root, "mobile")
    content_checks = {
        "all_primary_text_in_zh": "Travel Skill" not in html_blob,
        "desktop_templates_complete": desktop_templates == EXPECTED_TEMPLATES,
        "mobile_templates_complete": mobile_templates == EXPECTED_TEMPLATES,
        "share_artifacts_present": all(
            (guide_root / "notes" / name).exists()
            for name in ["sources.md", "sources.html"]
        ),
        "no_sample_reference_in_publish": "对标样本" not in html_blob and "sample.html" not in html_blob,
        "no_fake_media_blocks": (
            "B站搜索：" not in html_blob
            and "抖音搜索：" not in html_blob
            and "来源参考：" not in html_blob
            and "text-citation-only" not in html_blob
        ),
    }
    content_checks["exactly_five_templates"] = (
        content_checks["desktop_templates_complete"] and content_checks["mobile_templates_complete"]
    )
    warnings = []
    browser_check = verify_render_with_playwright(guide_root)
    if browser_check.get("status") == "warn":
        warnings.append(browser_check.get("reason", "browser verification skipped"))
    status = "pass" if all(content_checks.values()) else "fail"
    return {
        "content_checks": content_checks,
        "status": status,
        "warnings": warnings,
        "playwright_check": browser_check,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    guide_root = Path(args.guide_root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = verify_trip(guide_root)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
