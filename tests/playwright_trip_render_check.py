from pathlib import Path
from typing import Optional
import argparse
from datetime import datetime
import os
import traceback
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
ARTIFACTS_ROOT = ROOT / "tests" / "artifacts"

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


def resolve_outdir(cli_outdir: Optional[str], run_id: Optional[str]) -> Path:
    env_outdir = os.environ.get("TRIP_RENDER_OUTDIR")
    base = Path(cli_outdir or env_outdir) if (cli_outdir or env_outdir) else ARTIFACTS_ROOT

    rid = run_id
    if not rid:
        # Make overwrites unlikely while keeping the path human-readable.
        rid = datetime.now().strftime("%Y%m%d-%H%M%S")
        rid = f"{rid}-pid{os.getpid()}"

    return base / rid


def wait_for_stable_render(page) -> None:
    # "load" can be too early for JS-rendered content; wait for a steadier state.
    page.wait_for_load_state("load")
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        # Some environments never reach networkidle (extensions, background fetches).
        pass

    # Ensure section shells and cards are present before taking screenshots/metrics.
    page.wait_for_function("() => document.querySelectorAll('section').length >= 9", timeout=10_000)
    page.wait_for_function("() => document.querySelectorAll('.card').length > 0", timeout=10_000)
    page.evaluate("() => (document.fonts ? document.fonts.ready : Promise.resolve())")

    # Two frames to let layout settle after DOM writes.
    page.evaluate(
        """
        () => new Promise((resolve) => {
          requestAnimationFrame(() => requestAnimationFrame(resolve));
        })
        """
    )


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
            if result.get("error"):
                failures.append(f"{page_name} {label} failed: {result.get('error')}")
                continue
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

def collect_report(outdir: Path):
    with sync_playwright() as p:
        browser_kwargs = {"headless": True}
        chrome_exe = resolve_chrome_executable()
        if chrome_exe:
            browser_kwargs["executable_path"] = str(chrome_exe)

        browser = p.chromium.launch(**browser_kwargs)
        try:
            report = {}
            for path in PAGES:
                page_results = {}
                try:
                    page_key = str(path.relative_to(GUIDE_ROOT))
                except ValueError:
                    page_key = str(path)

                safe_prefix = page_key.replace("\\", "_").replace("/", "_").replace(":", "")
                for label, viewport in VIEWPORTS:
                    context = None
                    page = None
                    try:
                        context = browser.new_context(
                            viewport=viewport,
                            device_scale_factor=1,
                            locale="zh-CN",
                            timezone_id="Asia/Shanghai",
                            color_scheme="light",
                            reduced_motion="reduce",
                        )
                        page = context.new_page()
                        page.goto(path.as_uri(), wait_until="domcontentloaded")
                        page.add_style_tag(
                            content="*{animation:none!important;transition:none!important;scroll-behavior:auto!important}"
                        )
                        wait_for_stable_render(page)
                        page.screenshot(path=str(outdir / f"{safe_prefix}-{label}.png"), full_page=True)
                        page_results[label] = inspect_page(page)
                    except Exception:
                        # Capture as much as possible for debugging; don't stop other viewports/pages.
                        err = traceback.format_exc(limit=8).strip().replace("\n", " | ")
                        try:
                            if page is not None:
                                page.screenshot(path=str(outdir / f"{safe_prefix}-{label}-error.png"), full_page=True)
                        except Exception:
                            pass
                        page_results[label] = {"error": err}
                    finally:
                        try:
                            if context is not None:
                                context.close()
                        except Exception:
                            pass

                report[page_key] = page_results
            return report
        finally:
            try:
                browser.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=None, help="Write artifacts under this directory (or use TRIP_RENDER_OUTDIR).")
    parser.add_argument("--run-id", default=None, help="Per-run subdirectory name under outdir (defaults to timestamp+pid).")
    args = parser.parse_args()

    outdir = resolve_outdir(args.outdir, args.run_id)
    outdir.mkdir(parents=True, exist_ok=True)

    report = {}
    err: Optional[BaseException] = None
    exit_code = 0
    try:
        report = collect_report(outdir)
        verify_report(report)
    except BaseException as e:
        err = e
        exit_code = 1
    finally:
        try:
            (outdir / "trip-render-report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # Best-effort artifact writing; don't mask the original error.
            pass

        try:
            print(json.dumps(report, ensure_ascii=False, indent=2))
            print(f"\nartifacts: {outdir}")
        except Exception:
            # Best-effort printing; don't mask the original error.
            pass

    if err is not None:
        raise err
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
