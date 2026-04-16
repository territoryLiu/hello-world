from pathlib import Path
import argparse
import zipfile


EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".bak", ".log"}


def _include(path: Path, source_root: Path) -> bool:
    if not path.is_file():
        return False
    relative = path.relative_to(source_root)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def package_skill(source_root: Path, output_zip: Path) -> Path:
    source_root = Path(source_root)
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_root.rglob("*")):
            if not _include(path, source_root):
                continue
            arcname = Path(source_root.name) / path.relative_to(source_root)
            archive.write(path, arcname.as_posix())
    return output_zip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[2] / "dist" / "travel-skill.zip"))
    args = parser.parse_args()

    package_skill(Path(args.source_root), Path(args.output))


if __name__ == "__main__":
    main()
