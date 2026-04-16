from pathlib import Path
import argparse
import json


def score_manifest(payload: dict) -> dict:
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    frame_scores = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label") or "")
        evidence_score = 0.9 if any(token in label for token in ["queue", "menu", "ticket", "view"]) else 0.6
        scored = {
            **raw,
            "evidence_score": evidence_score,
            "visual_score": 0.5,
            "selected": evidence_score >= 0.8,
            "travel_signal_tags": raw.get("travel_signal_tags") if isinstance(raw.get("travel_signal_tags"), list) else [],
        }
        frame_scores.append(scored)
    return {
        "all_keyframes": items,
        "frame_scores": frame_scores,
        "selected_frames": [item for item in frame_scores if item["selected"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = score_manifest(payload if isinstance(payload, dict) else {})
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
