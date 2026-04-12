from pathlib import Path
import argparse
import zipfile


def build_summary(guide_root: Path, portal: Path, recommended_html: Path, share_html: Path) -> str:
    slug = guide_root.name
    style_dirs = sorted(
        child.name
        for child in (guide_root / "desktop").iterdir()
        if child.is_dir() and child.name in {"classic", "minimalist", "original", "vintage", "zen"}
    ) if (guide_root / "desktop").exists() else []
    return "\n".join(
        [
            f"trip_slug: {slug}",
            f"styles: {', '.join(style_dirs) if style_dirs else 'legacy-only'}",
            "included_files:",
            f"- {portal.name}",
            f"- {recommended_html.name}",
            f"- {share_html.name}",
            "- notes/sources.md",
            "- notes/sources.html",
            "- trip-summary.txt",
            "",
            "share_notes:",
            "- share.html 是优先转发的完整单文件分享版。",
            "- recommended.html 适合更轻量的最推荐阅读版本。",
            "- notes/sources.html 用于按 site、topic、checked_at 和 time-sensitive 快速复核。",
            "- ZIP 适合归档和整包分发。",
        ]
    ) + "\n"


def package_trip(guide_root: Path, portal: Path, recommended_html: Path, share_html: Path, output_zip: Path) -> Path:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    summary_path = output_zip.parent / "trip-summary.txt"
    summary_path.write_text(build_summary(guide_root, portal, recommended_html, share_html), encoding="utf-8")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(portal, arcname=portal.name)
        archive.write(recommended_html, arcname=recommended_html.name)
        archive.write(share_html, arcname=share_html.name)
        archive.write(summary_path, arcname="trip-summary.txt")
        archive.write(guide_root / "notes" / "sources.md", arcname="notes/sources.md")
        archive.write(guide_root / "notes" / "sources.html", arcname="notes/sources.html")
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
