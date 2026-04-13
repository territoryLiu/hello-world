from pathlib import Path
import argparse
import json


EXPECTED_TEMPLATES = ["decision-first", "destination-first", "lifestyle-first", "route-first", "transport-first"]


def scan_html_text(root: Path) -> str:
    if not root.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.html"))


def verify_trip(guide_root: Path) -> dict:
    html_blob = scan_html_text(guide_root)
    template_dirs = sorted(p.name for p in (guide_root / "desktop").iterdir() if p.is_dir()) if (guide_root / "desktop").exists() else []
    content_checks = {
        "all_primary_text_in_zh": "Travel Skill" not in html_blob,
        "no_sample_reference_in_publish": "对标样本" not in html_blob and "sample.html" not in html_blob,
        "no_fake_media_blocks": "B站搜索：" not in html_blob and "抖音搜索：" not in html_blob and "来源参考：" not in html_blob,
        "exactly_five_templates": template_dirs == EXPECTED_TEMPLATES,
    }
    status = "pass" if all(content_checks.values()) else "fail"
    return {"content_checks": content_checks, "status": status}


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
