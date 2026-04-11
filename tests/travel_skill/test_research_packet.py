from pathlib import Path
import json
import tempfile
import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR, run_script


class ResearchPacketTest(unittest.TestCase):
    def _run_merge(self, input_path: Path) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.json"
            run_script(SKILL_DIR / "scripts" / "merge_sources.py", "--input", input_path, "--output", merged)
            return json.loads(merged.read_text(encoding="utf-8"))

    def test_merge_sources_deduplicates_and_merges_metadata_by_latest_checked_at(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "source_notes.json"
        payload = self._run_merge(fixture)
        self.assertEqual([item["category"] for item in payload["entries"]], ["food", "risk", "transport"])

        transport = next(item for item in payload["entries"] if item["category"] == "transport")
        self.assertEqual(transport["checked_at"], "2026-04-12")
        self.assertEqual(transport["title"], "12306 南京到延吉（更新）")
        self.assertEqual(transport["source_type"], "official")
        self.assertEqual(len(transport["facts"]), 3)

    def test_merge_sources_fact_order_is_deterministic_for_same_set(self):
        original_notes = [
            {
                "category": "transport",
                "title": "t1",
                "url": "https://example.com/t",
                "checked_at": "2026-04-10",
                "source_type": "official",
                "facts": ["fact-a", "fact-c"],
            },
            {
                "category": "transport",
                "title": "t2",
                "url": "https://example.com/t",
                "checked_at": "2026-04-11",
                "source_type": "official",
                "facts": ["fact-b"],
            },
        ]
        reversed_notes = list(reversed(original_notes))
        with tempfile.TemporaryDirectory() as tmp:
            original_fixture = Path(tmp) / "source_notes_original.json"
            reversed_fixture = Path(tmp) / "source_notes_reversed.json"
            original_fixture.write_text(
                json.dumps(original_notes, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            reversed_fixture.write_text(
                json.dumps(reversed_notes, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            merged_a = self._run_merge(original_fixture)
            merged_b = self._run_merge(reversed_fixture)

        transport_a = next(item for item in merged_a["entries"] if item["category"] == "transport")
        transport_b = next(item for item in merged_b["entries"] if item["category"] == "transport")
        self.assertEqual(transport_a["facts"], transport_b["facts"])

    def test_extract_outputs_fact_level_schema_with_source_granularity(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "source_notes.json"
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.json"
            facts = Path(tmp) / "facts.json"
            run_script(SKILL_DIR / "scripts" / "merge_sources.py", "--input", fixture, "--output", merged)
            run_script(SKILL_DIR / "scripts" / "extract_structured_facts.py", "--input", merged, "--output", facts)
            payload = json.loads(facts.read_text(encoding="utf-8"))

        self.assertIn("transport", payload["categories"])
        transport_facts = payload["categories"]["transport"]
        self.assertTrue(len(transport_facts) >= 3)
        for fact in transport_facts:
            self.assertIn("text", fact)
            self.assertIn("source_url", fact)
            self.assertIn("checked_at", fact)
            self.assertIn("source_type", fact)
        self.assertIn("高峰时段需尽早锁票", [item["text"] for item in transport_facts])

    def test_generate_review_packet_blocks_dangerous_urls_and_sanitizes_markdown(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "source_notes.json"
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.json"
            facts = Path(tmp) / "facts.json"
            packet_dir = Path(tmp) / "review"
            run_script(SKILL_DIR / "scripts" / "merge_sources.py", "--input", fixture, "--output", merged)
            run_script(SKILL_DIR / "scripts" / "extract_structured_facts.py", "--input", merged, "--output", facts)
            run_script(SKILL_DIR / "scripts" / "generate_review_packet.py", "--input", facts, "--output-dir", packet_dir)
            md = (packet_dir / "research-packet.md").read_text(encoding="utf-8")
            html = (packet_dir / "research-packet.html").read_text(encoding="utf-8")

        self.assertIn("## Verified", md)
        self.assertIn("<h2>Pending Confirmation</h2>", html)
        self.assertIn("javascript:alert(1)", html)
        self.assertNotIn('href="javascript:alert(1)"', html)

        self.assertNotIn("raw <b>tag</b> [danger] `code` & symbol", md)
        self.assertIn("raw &lt;b&gt;tag&lt;/b&gt; \\[danger\\] \\`code\\` &amp; symbol", md)


if __name__ == "__main__":
    unittest.main()
