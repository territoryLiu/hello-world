from pathlib import Path
import argparse
import html


LAYER_LABELS = {
    "daily-overview": "每日行程速览",
    "recommended": "最推荐攻略",
    "comprehensive": "最全面攻略",
}


def _load_template() -> str:
    template_path = Path(__file__).resolve().parents[1] / "assets" / "templates" / "portal.html"
    return template_path.read_text(encoding="utf-8")


def _links(items: list[tuple[str, str]]) -> str:
    return "".join(f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>' for label, href in items)


def build_portal(guide_root: Path, output_path: Path) -> Path:
    title = guide_root.name
    desktop_links = [(label, f"../trips/{guide_root.name}/desktop/{layer}/index.html") for layer, label in LAYER_LABELS.items()]
    mobile_links = [(label, f"../trips/{guide_root.name}/mobile/{layer}/index.html") for layer, label in LAYER_LABELS.items()]
    share_links = [
        ("最推荐攻略", "recommended.html"),
        ("最全面攻略", "comprehensive.html"),
    ]

    html_text = _load_template()
    replacements = {
        "{{TITLE}}": html.escape(title),
        "{{SUMMARY}}": html.escape("通过入口页快速跳转到桌面端、手机端和单文件分享版。"),
        "{{DESKTOP_LINKS}}": _links(desktop_links),
        "{{MOBILE_LINKS}}": _links(mobile_links),
        "{{SHARE_LINKS}}": _links(share_links),
    }
    for key, value in replacements.items():
        html_text = html_text.replace(key, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    build_portal(Path(args.guide_root), Path(args.output))


if __name__ == "__main__":
    main()
