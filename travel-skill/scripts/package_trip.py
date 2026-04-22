from pathlib import Path
import argparse
import sys
import zipfile

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import PUBLISH_ARTIFACTS, SORTED_TEMPLATE_IDS as TEMPLATES
from validate_delivery_gate import validate_delivery_gate


def build_summary(guide_root: Path, portal: Path, recommended_html: Path, share_html: Path) -> str:
    slug = guide_root.name
    template_dirs = sorted(
        child.name for child in (guide_root / "desktop").iterdir() if child.is_dir() and child.name in TEMPLATES
    ) if (guide_root / "desktop").exists() else []
    return "\n".join(
        [
            f"trip_slug: {slug}",
            f"templates: {', '.join(template_dirs) if template_dirs else 'missing'}",
            "included_files:",
            f"- {portal.name}",
            f"- {recommended_html.name}",
            f"- {share_html.name}",
            f"- {PUBLISH_ARTIFACTS['sources_markdown']}",
            f"- {PUBLISH_ARTIFACTS['sources_html']}",
            f"- {PUBLISH_ARTIFACTS['summary']}",
            "",
            "share_notes:",
            f"- {PUBLISH_ARTIFACTS['share']} 是优先转发的完整单文件分享版。",
            f"- {PUBLISH_ARTIFACTS['recommended']} 是当前主推荐分享入口。",
            f"- {PUBLISH_ARTIFACTS['sources_html']} 用于按 site、topic、checked_at 和 time-sensitive 快速复核。",
            "- ZIP 适合归档和整包分发。",
        ]
    ) + "\n"


def package_trip(guide_root: Path, portal: Path, recommended_html: Path, share_html: Path, output_zip: Path) -> Path:
    delivery_gate = validate_delivery_gate(guide_root)
    if delivery_gate["status"] != "pass":
        raise ValueError(f"delivery gate failed: {', '.join(delivery_gate['failed_checks'])}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    summary_path = output_zip.parent / PUBLISH_ARTIFACTS["summary"]
    summary_path.write_text(build_summary(guide_root, portal, recommended_html, share_html), encoding="utf-8")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(portal, arcname=portal.name)
        archive.write(recommended_html, arcname=recommended_html.name)
        archive.write(share_html, arcname=share_html.name)
        archive.write(summary_path, arcname=PUBLISH_ARTIFACTS["summary"])
        archive.write(guide_root / PUBLISH_ARTIFACTS["sources_markdown"], arcname=PUBLISH_ARTIFACTS["sources_markdown"])
        archive.write(guide_root / PUBLISH_ARTIFACTS["sources_html"], arcname=PUBLISH_ARTIFACTS["sources_html"])
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--portal", required=True)
    parser.add_argument("--recommended-html", required=True)
    parser.add_argument("--comprehensive-html", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    package_trip(
        Path(args.guide_root),
        Path(args.portal),
        Path(args.recommended_html),
        Path(args.comprehensive_html),
        Path(args.output),
    )


if __name__ == "__main__":
    main()
