from pathlib import Path
from typing import Optional
import os
from playwright.sync_api import sync_playwright
import json

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
GUIDE_ROOT = ROOT / "trips" / "jilin-yanji-changbaishan"
PAGES = [
    GUIDE_ROOT / "desktop" / "index.html",
    GUIDE_ROOT / "mobile" / "index.html",
]
VIEWPORTS = [
    ("desktop", {"width": 1440, "height": 1400}),
    ("mobile", {"width": 390, "height": 844}),
]
OUTDIR = ROOT / "tests" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)

REQUIRED_SECTIONS = {"overview", "recommended", "options", "attractions", "food", "season", "packing", "transport", "sources"}


def resolve_chrome_executable() -> Optional[Path]:
    env_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate

    for candidate in (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ):
        if candidate.exists():
            return candidate
    return None


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
            height: Math.round(el.getBoundingClientRect().height),
            dataPage: el.getAttribute('data-page')
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
            mode: document.body ? document.body.getAttribute('data-mode') : null,
            navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : null,
            heroHeight: hero ? Math.round(hero.getBoundingClientRect().height) : null,
            sections,
            tables,
            overs
          };
        }
        """
    )


def verify_report(report):
    failures = []
    for page_name, page_results in report.items():
        for label, result in page_results.items():
            sections = result.get("sections", [])
            found_ids = {sec.get("id") for sec in sections if sec.get("id")}
            missing = sorted(REQUIRED_SECTIONS - found_ids)
            if missing:
                failures.append(f"{page_name} {label} missing sections: {missing}")
            viewport_width = result.get("viewportWidth", 0)
            doc_width = result.get("docScrollWidth", 0)
            if doc_width > viewport_width + 1:
                failures.append(
                    f"{page_name} {label} has horizontal overflow (doc {doc_width} > viewport {viewport_width})"
                )
            overs = result.get("overs", [])
            if overs:
                sample = overs[:2]
                failures.append(
                    f"{page_name} {label} reports {len(overs)} oversize elements: {sample}"
                )

            # Mobile guide uses explicit pagination markers on each section shell.
            if result.get("mode") == "mobile":
                pages = [sec.get("dataPage") for sec in sections if sec.get("id")]
                missing_pages = [sec.get("id") for sec in sections if sec.get("id") and not sec.get("dataPage")]
                if missing_pages:
                    failures.append(f"{page_name} {label} missing data-page for sections: {missing_pages}")
                page_ints = []
                for value in pages:
                    try:
                        page_ints.append(int(value))
                    except (TypeError, ValueError):
                        failures.append(f"{page_name} {label} has non-numeric data-page: {value!r}")
                if page_ints:
                    expected = list(range(1, len(page_ints) + 1))
                    if sorted(page_ints) != expected:
                        failures.append(
                            f"{page_name} {label} has non-sequential data-page values: {sorted(page_ints)} (expected {expected})"
                        )
    if failures:
        raise AssertionError(" | ".join(failures))

with sync_playwright() as p:
    browser_kwargs = {"headless": True}
    chrome_exe = resolve_chrome_executable()
    if chrome_exe:
        browser_kwargs["executable_path"] = str(chrome_exe)
    browser = p.chromium.launch(**browser_kwargs)
    report = {}
    for path in PAGES:
        page_results = {}
        try:
            page_key = str(path.relative_to(GUIDE_ROOT))
        except ValueError:
            page_key = str(path)
        for label, viewport in VIEWPORTS:
            context = browser.new_context(viewport=viewport, device_scale_factor=1)
            page = context.new_page()
            page.goto(path.as_uri(), wait_until="load")
            safe_prefix = page_key.replace("\\", "_").replace("/", "_").replace(":", "")
            page.screenshot(path=str(OUTDIR / f"{safe_prefix}-{label}.png"), full_page=True)
            page_results[label] = inspect_page(page)
            context.close()
        report[page_key] = page_results
    browser.close()

(OUTDIR / "trip-render-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
verify_report(report)
print(json.dumps(report, ensure_ascii=False, indent=2))
