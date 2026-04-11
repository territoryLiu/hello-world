from pathlib import Path
import argparse


def inline_assets(guide_root: Path) -> str:
    desktop_html = (guide_root / "desktop" / "index.html").read_text(encoding="utf-8")
    css = (guide_root / "assets" / "base.css").read_text(encoding="utf-8")
    guide_content = (guide_root / "assets" / "guide-content.js").read_text(encoding="utf-8")
    render_js = (guide_root / "assets" / "render-guide.js").read_text(encoding="utf-8")
    html = desktop_html.replace('<link rel="stylesheet" href="../assets/base.css" />', f"<style>\n{css}\n</style>")
    html = html.replace('<script src="../assets/guide-content.js"></script>', f"<script>\n{guide_content}\n</script>")
    html = html.replace('<script src="../assets/render-guide.js"></script>', f"<script>\n{render_js}\n</script>")
    return html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    guide_root = Path(args.guide_root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(inline_assets(guide_root), encoding="utf-8")


if __name__ == "__main__":
    main()
