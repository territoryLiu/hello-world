from pathlib import Path
import argparse
import json


def verify_render(guide_root: Path) -> dict:
    return {
        "checked": False,
        "reason": "Playwright check not executed in unit-test mode",
        "status": "warn",
        "guide_root": str(guide_root),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guide-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = verify_render(Path(args.guide_root))
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
