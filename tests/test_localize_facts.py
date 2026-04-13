from pathlib import Path
import json
import tempfile

from tests.travel_skill.helpers import SKILL_DIR, run_script


def test_localize_facts_normalizes_english_transport_copy():
    payload = {
        "facts": [
            {"topic": "long_distance_transport", "text": "ticket: 225 CNY", "source_title": "Official notice"},
            {"topic": "risks", "text": "arrive before 08:30 for smoother queue", "source_title": "social note"},
        ]
    }
    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "input.json"
        output_path = Path(tmp) / "output.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        run_script(SKILL_DIR / "scripts" / "localize_facts.py", "--input", input_path, "--output", output_path)
        localized = json.loads(output_path.read_text(encoding="utf-8"))

    assert "票价" in localized["facts"][0]["text_zh"]
    assert "错峰" in localized["facts"][1]["text_zh"]
