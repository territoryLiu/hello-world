from pathlib import Path
import argparse
import zipfile


def build_summary(guide_root: Path, single_html: Path) -> str:
    slug = guide_root.name
    return "\n".join(
        [
            f"trip_slug: {slug}",
            f"single_html: {single_html.name}",
            "included_files:",
            f"- {single_html.name}",
            "- trip-summary.txt",
            "- notes/sources.md",
            "",
            "share_notes:",
            "- 单文件 HTML 可直接转发。",
            "- ZIP 适合归档或打包给别人查看。",
        ]
    ) + "\n"


def package_trip(guide_root: Path, single_html: Path, output_zip: Path) -> Path:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    summary_path = output_zip.parent / "trip-summary.txt"
    summary_path.write_text(build_summary(guide_root, single_html), encoding="utf-8")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(single_html, arcname=single_html.name)
        archive.write(summary_path, arcname="trip-summary.txt")
        archive.write(guide_root / "notes" / "sources.md", arcname="notes/sources.md")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--single-html", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    package_trip(Path(args.guide_root), Path(args.single_html), Path(args.output))


if __name__ == "__main__":
    main()
