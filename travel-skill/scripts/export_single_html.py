from pathlib import Path
import argparse
import re


ASSET_PATTERNS = {
    "css": re.compile(r'<link rel="stylesheet" href="(?:\.\./)+assets/base\.css" />'),
    "guide": re.compile(r'<script src="(?:\.\./)+assets/guide-content\.js"></script>'),
    "render": re.compile(r'<script src="(?:\.\./)+assets/render-guide\.js"></script>'),
}


def _html_path(guide_root: Path, template_id: str, device: str) -> Path:
    html_path = guide_root / device / template_id / "index.html"
    if not html_path.exists():
        raise FileNotFoundError(f"Cannot find HTML file: {html_path}")
    return html_path


def inline_assets(guide_root: Path, template_id: str, device: str = "desktop") -> str:
    html_path = _html_path(guide_root, template_id, device)
    html_text = html_path.read_text(encoding="utf-8")
    css = (guide_root / "assets" / "base.css").read_text(encoding="utf-8")
    guide_content = (guide_root / "assets" / "guide-content.js").read_text(encoding="utf-8")
    render_js = (guide_root / "assets" / "render-guide.js").read_text(encoding="utf-8")

    html_text = ASSET_PATTERNS["css"].sub(f"<style>\n{css}\n</style>", html_text)
    html_text = ASSET_PATTERNS["guide"].sub(f"<script>\n{guide_content}\n</script>", html_text)
    html_text = ASSET_PATTERNS["render"].sub(f"<script>\n{render_js}\n</script>", html_text)
    return html_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="desktop", choices=["desktop", "mobile"])
    args = parser.parse_args()

    guide_root = Path(args.guide_root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        inline_assets(guide_root, args.template, args.device),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
