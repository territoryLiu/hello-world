from pathlib import Path
import argparse
import json


DEFAULT_REQUIRED_SITES = ("xiaohongshu", "douyin", "bilibili")


def _load_json_if_exists(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def infer_trip_root(guide_root: Path) -> Path:
    guide_root = guide_root.resolve()
    if guide_root.parent.name == "guides" and guide_root.parent.parent.name == "travel-data":
        return guide_root.parent.parent / "trips" / guide_root.name
    return guide_root


def _has_web_access_execution_record(trip_root: Path) -> bool:
    research_root = trip_root / "research"
    if not research_root.exists():
        return False
    if (research_root / "web-results").exists() and any((research_root / "web-results").glob("*.json")):
        return True
    if (research_root / "web-runs").exists() and any((research_root / "web-runs").glob("*/bundle.json")):
        return True
    return False


def _cdp_check(trip_root: Path) -> dict:
    cdp_status_path = trip_root / "research" / "cdp-status.json"
    payload = _load_json_if_exists(cdp_status_path)
    if isinstance(payload, dict):
        chrome_value = str(payload.get("chrome") or "").lower()
        proxy_value = str(payload.get("proxy") or "").lower()
        chrome_ready = chrome_value == "ok" or payload.get("chrome_ready") is True
        proxy_ready = proxy_value == "ready" or payload.get("proxy_ready") is True
        if chrome_ready and proxy_ready:
            return {
                "passed": True,
                "source": str(cdp_status_path),
                "reason": "",
            }
    if _has_web_access_execution_record(trip_root):
        return {
            "passed": True,
            "source": "web-access-execution-record",
            "reason": "",
        }
    return {
        "passed": False,
        "source": "",
        "reason": "missing_cdp_status_or_web_access_execution_record",
    }


def _gate_report_check(trip_root: Path) -> dict:
    gate_path = trip_root / "request" / "gate-report.json"
    payload = _load_json_if_exists(gate_path)
    if isinstance(payload, dict) and payload.get("can_proceed") is True:
        return {"passed": True, "source": str(gate_path), "reason": ""}
    return {"passed": False, "source": str(gate_path), "reason": "gate_report_missing_or_blocked"}


def _coverage_payload(trip_root: Path):
    research_root = trip_root / "research"
    for name in ("batch-coverage.json", "coverage.json"):
        payload = _load_json_if_exists(research_root / name)
        if isinstance(payload, dict):
            return payload, str(research_root / name)
    return None, ""


def _coverage_check(trip_root: Path, required_sites: tuple[str, ...]) -> dict:
    payload, source = _coverage_payload(trip_root)
    if not isinstance(payload, dict):
        return {
            "passed": False,
            "source": source,
            "reason": "coverage_report_missing",
            "required_sites": list(required_sites),
            "missing_sites": list(required_sites),
            "missing_status_sites": [],
            "site_statuses": {},
        }

    by_site = payload.get("by_site")
    if not isinstance(by_site, dict):
        by_site = {}

    site_statuses = {}
    missing_sites = []
    missing_status_sites = []
    for site in required_sites:
        bucket = by_site.get(site)
        if not isinstance(bucket, dict):
            missing_sites.append(site)
            continue
        status = str(bucket.get("coverage_status") or "").strip()
        site_statuses[site] = status
        if not status:
            missing_status_sites.append(site)

    passed = not missing_sites and not missing_status_sites
    reason = ""
    if missing_sites:
        reason = "required_sites_missing"
    elif missing_status_sites:
        reason = "coverage_status_missing"
    return {
        "passed": passed,
        "source": source,
        "reason": reason,
        "required_sites": list(required_sites),
        "missing_sites": missing_sites,
        "missing_status_sites": missing_status_sites,
        "site_statuses": site_statuses,
    }


def validate_delivery_gate(
    guide_root: Path,
    trip_root: Path | None = None,
    required_sites: tuple[str, ...] = DEFAULT_REQUIRED_SITES,
) -> dict:
    resolved_trip_root = (trip_root or infer_trip_root(guide_root)).resolve()
    checks = {
        "intake_gate": _gate_report_check(resolved_trip_root),
        "cdp_or_web_access": _cdp_check(resolved_trip_root),
        "platform_coverage": _coverage_check(resolved_trip_root, required_sites),
    }
    failures = [name for name, result in checks.items() if not result.get("passed")]
    return {
        "status": "pass" if not failures else "fail",
        "guide_root": str(Path(guide_root).resolve()),
        "trip_root": str(resolved_trip_root),
        "required_sites": list(required_sites),
        "failed_checks": failures,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--trip-root")
    parser.add_argument("--output", required=True)
    parser.add_argument("--required-sites", nargs="*")
    args = parser.parse_args()

    required_sites = tuple(args.required_sites) if args.required_sites else DEFAULT_REQUIRED_SITES
    payload = validate_delivery_gate(
        Path(args.guide_root),
        Path(args.trip_root) if args.trip_root else None,
        required_sites,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
