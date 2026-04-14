from pathlib import Path
import argparse
import html
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from travel_config import PUBLISH_ARTIFACTS, SORTED_TEMPLATE_IDS as TEMPLATES


def _render_links(items: list[tuple[str, str]]) -> str:
    return "".join(
        f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
        for label, href in items
    )


def _template_links(guide_root: Path, device: str) -> list[tuple[str, str]]:
    return [
        (template_id, f"../guides/{guide_root.name}/{device}/{template_id}/index.html")
        for template_id in TEMPLATES
        if (guide_root / device / template_id / "index.html").exists()
    ]


def build_portal(guide_root: Path, output_path: Path) -> Path:
    title = guide_root.name
    desktop_links = _template_links(guide_root, "desktop")
    mobile_links = _template_links(guide_root, "mobile")
    share_links = [
        ("单文件分享版", PUBLISH_ARTIFACTS["share"]),
        ("主推荐分享页", PUBLISH_ARTIFACTS["recommended"]),
        ("来源说明", f"../guides/{guide_root.name}/{PUBLISH_ARTIFACTS['sources_html']}"),
    ]
    package_links = [
        ("ZIP 打包说明", "#zip-notes"),
        ("来源 Markdown", f"../guides/{guide_root.name}/{PUBLISH_ARTIFACTS['sources_markdown']}"),
    ]

    html_text = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)} · 分享入口</title>
    <style>
      body {{
        margin: 0;
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
        background: linear-gradient(180deg, #f8f4ed 0%, #efe6da 100%);
        color: #2b241d;
      }}
      .shell {{
        width: min(1100px, calc(100% - 24px));
        margin: 0 auto;
        padding: 32px 0 40px;
      }}
      .hero, .group {{
        background: rgba(255, 250, 244, 0.94);
        border: 1px solid rgba(43, 36, 29, 0.08);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 16px 36px rgba(43, 36, 29, 0.08);
      }}
      .hero {{ margin-bottom: 18px; }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }}
      .group h2 {{ margin: 0 0 10px; }}
      .group p {{
        margin: 0 0 12px;
        color: #5c5348;
        line-height: 1.7;
      }}
      a {{
        display: block;
        margin-bottom: 10px;
        color: inherit;
        text-decoration: none;
        padding: 12px 14px;
        border-radius: 16px;
        background: #fff;
        border: 1px solid rgba(43, 36, 29, 0.08);
      }}
      @media (max-width: 720px) {{
        .grid {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="shell">
        <section class="hero">
          <p>旅行分享入口</p>
          <h1>{html.escape(title)}</h1>
          <p>这里汇总当前默认杂志版的桌面端、手机端、单文件分享页、来源说明和 ZIP 交付入口。</p>
        </section>
      <div class="grid">
        <section class="group">
          <h2>桌面端</h2>
          <p>适合完整阅读路线、景点、交通细节和来源卡片。</p>
          {_render_links(desktop_links)}
        </section>
        <section class="group">
          <h2>手机端</h2>
          <p>适合触屏阅读和碎片化查看，结构与桌面端共用同一事实集。</p>
          {_render_links(mobile_links)}
        </section>
        <section class="group">
          <h2>单文件</h2>
          <p>`{PUBLISH_ARTIFACTS["share"]}` 适合直接转发，`{PUBLISH_ARTIFACTS["recommended"]}` 作为当前主推荐分享入口。</p>
          {_render_links(share_links)}
        </section>
        <section class="group" id="zip-notes">
          <h2>ZIP</h2>
          <p>适合归档和整包交付，压缩包会附带来源说明和摘要。</p>
          {_render_links(package_links)}
        </section>
      </div>
    </div>
  </body>
</html>
"""

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
