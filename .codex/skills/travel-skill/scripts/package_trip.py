from pathlib import Path
import argparse
import zipfile


def build_summary(guide_root: Path, portal: Path, recommended_html: Path, comprehensive_html: Path) -> str:
    slug = guide_root.name
    return "\n".join(
        [
            f"trip_slug: {slug}",
            "included_files:",
            f"- {portal.name}",
            f"- {recommended_html.name}",
            f"- {comprehensive_html.name}",
            "- trip-summary.txt",
            "- notes/sources.md",
            "",
            "share_notes:",
            "- 单文件 HTML 适合直接转发。",
            "- ZIP 适合归档和打包分享。",
        ]
    ) + "\n"


def package_trip(guide_root: Path, portal: Path, recommended_html: Path, comprehensive_html: Path, output_zip: Path) -> Path:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    summary_path = output_zip.parent / "trip-summary.txt"
    summary_path.write_text(build_summary(guide_root, portal, recommended_html, comprehensive_html), encoding="utf-8")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(portal, arcname=portal.name)
        archive.write(recommended_html, arcname=recommended_html.name)
        archive.write(comprehensive_html, arcname=comprehensive_html.name)
        archive.write(summary_path, arcname="trip-summary.txt")
        archive.write(guide_root / "notes" / "sources.md", arcname="notes/sources.md")
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
