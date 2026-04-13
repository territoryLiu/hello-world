from pathlib import Path


def travel_roots(data_root: Path, trip_slug: str) -> dict[str, Path]:
    data_root = Path(data_root)
    return {
        "places_root": data_root / "places",
        "corridors_root": data_root / "corridors",
        "trips_root": data_root / "trips",
        "trip_root": data_root / "trips" / trip_slug,
        "guides_root": data_root / "guides" / trip_slug,
    }


def ensure_trip_layout(data_root: Path, trip_slug: str) -> dict[str, Path]:
    roots = travel_roots(data_root, trip_slug)
    for key in ["places_root", "corridors_root", "trips_root", "trip_root", "guides_root"]:
        roots[key].mkdir(parents=True, exist_ok=True)
    (roots["trip_root"] / "request").mkdir(parents=True, exist_ok=True)
    (roots["trip_root"] / "planning").mkdir(parents=True, exist_ok=True)
    (roots["trip_root"] / "snapshots").mkdir(parents=True, exist_ok=True)
    for child in ["desktop", "mobile", "share", "package", "verify"]:
        (roots["guides_root"] / child).mkdir(parents=True, exist_ok=True)
    return roots
