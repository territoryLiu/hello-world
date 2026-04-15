from pathlib import Path
import argparse
import json

from normalize_request import slugify
from travel_paths import ensure_trip_layout


def corridor_slug(from_place: str, to_place: str) -> str:
    return f"{slugify(from_place)}-to-{slugify(to_place)}"


def build_snapshots(payload: dict, data_root: Path) -> None:
    roots = ensure_trip_layout(data_root, payload["trip_slug"])
    knowledge = [
        {"slug": slugify(place), "path": f"places/{slugify(place)}"}
        for place in payload.get("destinations", [])
    ]
    corridors = []
    departure_city = payload.get("departure_city", "")
    for place in payload.get("destinations", []):
        slug = corridor_slug(departure_city, place)
        corridors.append({"slug": slug, "path": f"corridors/{slug}"})
    snapshot_root = roots["trip_root"] / "snapshots"
    (snapshot_root / "linked-knowledge.json").write_text(
        json.dumps({"items": knowledge}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (snapshot_root / "linked-corridors.json").write_text(
        json.dumps({"items": corridors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    build_snapshots(payload, Path(args.data_root))


if __name__ == "__main__":
    main()
