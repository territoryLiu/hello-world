from pathlib import Path
import argparse
import base64
import json
import os


def _coerce_tags(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _heuristic_score(raw: dict) -> dict:
    label = str(raw.get("label") or "")
    evidence_score = 0.9 if any(token in label for token in ["queue", "menu", "ticket", "view"]) else 0.6
    selected = evidence_score >= 0.8
    return {
        **raw,
        "evidence_score": evidence_score,
        "visual_score": 0.5,
        "selected": selected,
        "selected_for_publish": selected,
        "travel_signal_tags": _coerce_tags(raw.get("travel_signal_tags")),
        "selection_rationale": str(raw.get("selection_rationale") or "heuristic travel-signal scoring").strip(),
    }


def _multimodal_enabled() -> bool:
    flag = str(os.environ.get("TRAVEL_SKILL_ENABLE_MULTIMODAL") or "").strip().lower()
    return flag in {"1", "true", "yes", "on"} or bool(os.environ.get("TRAVEL_SKILL_MULTIMODAL_MODEL"))


def _image_data_url(frame: dict) -> str:
    path = Path(str(frame.get("local_path") or frame.get("path") or "")).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"frame image not found: {path}")
    suffix = path.suffix.lower().lstrip(".") or "jpeg"
    if suffix == "jpg":
        suffix = "jpeg"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{suffix};base64,{payload}"


def _build_multimodal_analyzer():
    if not _multimodal_enabled() or not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None

    model = str(os.environ.get("TRAVEL_SKILL_MULTIMODAL_MODEL") or "gpt-5").strip()
    detail = str(os.environ.get("TRAVEL_SKILL_MULTIMODAL_DETAIL") or "low").strip() or "low"
    client = OpenAI()

    def analyze(frame: dict) -> dict:
        prompt = (
            "Score this travel-research video keyframe. "
            "Return JSON only with keys: evidence_score, visual_score, selected, "
            "travel_signal_tags, selection_rationale. "
            "Prefer travel-information value over aesthetics. "
            "Evidence score means usefulness for queues, tickets, transport, view conditions, menus, signage, or crowd level. "
            f"Frame label: {str(frame.get('label') or '')}. "
            f"Timestamp: {str(frame.get('timestamp') or '')}."
        )
        response = client.responses.create(
            model=model,
            max_output_tokens=220,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": _image_data_url(frame), "detail": detail},
                    ],
                }
            ],
        )
        text = str(getattr(response, "output_text", "") or "").strip()
        if not text:
            raise ValueError("empty multimodal output")
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("multimodal output is not an object")
        selected = bool(payload.get("selected"))
        return {
            "evidence_score": float(payload.get("evidence_score", 0)),
            "visual_score": float(payload.get("visual_score", 0)),
            "selected": selected,
            "selected_for_publish": selected,
            "travel_signal_tags": _coerce_tags(payload.get("travel_signal_tags")),
            "selection_rationale": str(payload.get("selection_rationale") or "").strip(),
        }

    return analyze


def score_manifest(payload: dict, analyzer=None) -> dict:
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    frame_scores = []
    selected_frames = []
    analyzer = analyzer if analyzer is not None else _build_multimodal_analyzer()

    for raw in items:
        if not isinstance(raw, dict):
            continue
        heuristic = _heuristic_score(raw)
        if analyzer is None:
            scored = {**heuristic, "score_source": "heuristic"}
        else:
            try:
                multimodal = analyzer(raw)
            except Exception as exc:
                scored = {
                    **heuristic,
                    "score_source": "heuristic-fallback",
                    "analysis_error": str(exc),
                }
            else:
                scored = {
                    **raw,
                    "evidence_score": float(multimodal.get("evidence_score", heuristic["evidence_score"])),
                    "visual_score": float(multimodal.get("visual_score", heuristic["visual_score"])),
                    "selected": bool(multimodal.get("selected")),
                    "selected_for_publish": bool(multimodal.get("selected_for_publish", multimodal.get("selected"))),
                    "travel_signal_tags": _coerce_tags(multimodal.get("travel_signal_tags")),
                    "selection_rationale": str(
                        multimodal.get("selection_rationale") or heuristic["selection_rationale"]
                    ).strip(),
                    "score_source": "multimodal",
                }
        frame_scores.append(scored)
        if scored.get("selected"):
            selected_frames.append(scored)
    return {
        "all_keyframes": items,
        "frame_scores": frame_scores,
        "selected_frames": selected_frames,
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
