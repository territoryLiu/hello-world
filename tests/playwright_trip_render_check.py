from pathlib import Path
from playwright.sync_api import sync_playwright
import json


ROOT = Path(r"d:\vscode\hello-world")
PAGES = [
    ROOT / "trips" / "jilin-yanji-changbaishan" / "desktop" / "index.html",
    ROOT / "trips" / "jilin-yanji-changbaishan" / "mobile" / "index.html",
]
VIEWPORTS = [
    ("desktop", {"width": 1440, "height": 1400}),
    ("mobile", {"width": 390, "height": 844}),
]
OUTDIR = ROOT / "tests" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)


def resolve_chrome_executable() -> Path:
    candidates = [
        Path(
            r"C:\Users\Lenovo\AppData\Local\ms-playwright\chromium-1208\chrome-win64\chrome.exe"
        ),
        Path(
            r"C:\Users\Lenovo\AppData\Local\ms-playwright\chromium-1208\chrome-win\chrome.exe"
        ),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No Chromium/Chrome executable found for Playwright render check.")


def inspect_page(page):
    return page.evaluate(
        """
        () => {
          const overs = [...document.querySelectorAll('body *')].filter((el) => {
            const inScrollableNav = !!el.closest('.navin');
            if (inScrollableNav) return false;
            const rect = el.getBoundingClientRect();
            return rect.width > window.innerWidth + 1 || rect.right > window.innerWidth + 1;
          }).slice(0, 12).map((el) => ({
            tag: el.tagName,
            cls: el.className,
            width: Math.round(el.getBoundingClientRect().width),
            right: Math.round(el.getBoundingClientRect().right)
          }));

          const sections = [...document.querySelectorAll('section')].map((el) => ({
            id: el.id,
            height: Math.round(el.getBoundingClientRect().height)
          }));

          const nav = document.querySelector('.navin');
          const hero = document.querySelector('.hero');
          const tables = [...document.querySelectorAll('table')].map((el, idx) => ({
            index: idx,
            width: Math.round(el.getBoundingClientRect().width),
            scrollWidth: el.scrollWidth
          }));

          return {
            title: document.title,
            bodyScrollWidth: document.body.scrollWidth,
            docScrollWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : null,
            heroHeight: hero ? Math.round(hero.getBoundingClientRect().height) : null,
            sections,
            tables,
            overs
          };
        }
        """
    )


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=str(resolve_chrome_executable()),
        headless=True,
    )
    report = {}
    for path in PAGES:
      page_results = {}
      for label, viewport in VIEWPORTS:
        context = browser.new_context(viewport=viewport, device_scale_factor=1)
        page = context.new_page()
        page.goto(path.as_uri(), wait_until="load")
        page.screenshot(path=str(OUTDIR / f"{path.stem}-{label}.png"), full_page=True)
        page_results[label] = inspect_page(page)
        context.close()
      report[path.name] = page_results
    browser.close()

(OUTDIR / "trip-render-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
