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
        self.assertEqual(payload["summary"]["topics"], ["food", "long_distance_transport", "risks"])
        self.assertEqual(payload["summary"]["places"], ["changbaishan", "yanbian-route", "yanji"])
        self.assertIn("yanji", payload["normalized"])
        self.assertIn("food", payload["normalized"]["yanji"])

        transport = next(item for item in payload["entries"] if item["topic"] == "long_distance_transport")
        self.assertEqual(transport["checked_at"], "2026-04-12")
        self.assertEqual(transport["source_type"], "official")
        self.assertEqual(transport["place"], "yanbian-route")
        self.assertEqual(transport["platform"], "official")
        self.assertIn("site", transport)
        self.assertTrue(len(transport["facts"]) >= 1)

    def test_extract_outputs_fact_level_schema_with_site(self):
        fixture = ROOT / "tests" / "fixtures" / "travel_skill" / "source_notes.json"
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.json"
            facts = Path(tmp) / "facts.json"
            run_script(SKILL_DIR / "scripts" / "merge_sources.py", "--input", fixture, "--output", merged)
            run_script(SKILL_DIR / "scripts" / "extract_structured_facts.py", "--input", merged, "--output", facts)
            payload = json.loads(facts.read_text(encoding="utf-8"))

        self.assertIn("by_place", payload)
        self.assertIn("yanbian-route", payload["by_place"])
        transport_facts = payload["by_place"]["yanbian-route"]["long_distance_transport"]
        self.assertTrue(len(transport_facts) >= 1)
        for fact in transport_facts:
            self.assertIn("text", fact)
            self.assertIn("place", fact)
            self.assertIn("topic", fact)
            self.assertIn("platform", fact)
            self.assertIn("site", fact)
            self.assertIn("source_url", fact)
            self.assertIn("checked_at", fact)
            self.assertIn("source_type", fact)

    def test_generate_review_packet_includes_site_coverage_and_sanitizes_links(self):
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
        self.assertIn("## Site Coverage", md)
        self.assertIn("<h2>Pending Confirmation</h2>", html)
        self.assertIn("javascript:alert(1)", html)
        self.assertNotIn('href="javascript:alert(1)"', html)

    def test_validate_site_coverage_reports_missing_required_sites(self):
        coverage_input = {
            "facts": [
                {
                    "place": "yanji",
                    "topic": "food",
                    "site": "meituan",
                    "platform": "local-listing",
                    "text": "鍖呴キ搴楁帹鑽?",
                    "source_url": "https://example.com/meituan",
                    "checked_at": "2026-04-11",
                    "source_type": "platform",
                    "source_title": "缇庡洟",
                },
                {
                    "place": "yanji",
                    "topic": "attractions",
                    "site": "official",
                    "platform": "official",
                    "text": "鏅尯鍏憡",
                    "source_url": "https://example.com/official",
                    "checked_at": "2026-04-11",
                    "source_type": "official",
                    "source_title": "瀹樻柟",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "facts.json"
            output_path = Path(tmp) / "coverage.json"
            input_path.write_text(json.dumps(coverage_input, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "validate_site_coverage.py", "--input", input_path, "--output", output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("food", payload["by_topic"])
        self.assertIn("missing_required_sites", payload["by_topic"]["food"])
        self.assertIn("xiaohongshu", payload["by_topic"]["food"]["missing_required_sites"])
        self.assertIn("dianping", payload["by_topic"]["food"]["missing_required_sites"])
        self.assertTrue(payload["has_gaps"])

    def test_collect_media_candidates_and_build_image_plan(self):
        media_notes = [
            {
                "platform": "xiaohongshu",
                "title": "寤跺悏涓ゆ棩鍚冨枬璺嚎",
                "author": "鏃呰鑰匒",
                "published_at": "2026-04-09",
                "summary": "閫傚悎绗竴娆″幓寤跺悏鐨勫悆鍠濊矾绾?",
                "comment_highlights": ["鏃╁競寤鸿 7 鐐瑰墠鍒?", "鍖呴キ鍗堥鎺掗槦浼氬彉闀?"],
                "transcript": "绗竴绔欏幓姘翠笂甯傚満锛岀浜岀珯鍘诲寘楗簵銆?",
                "timeline": [
                    {"time": "00:05", "note": "甯傚満鏃╅闀滃ご"},
                    {"time": "00:21", "note": "鍖呴キ涓婃闀滃ご"},
                ],
                "shot_candidates": [
                    {"time": "00:05", "label": "鏃╁競鎽婁綅"},
                    {"time": "00:21", "label": "鍖呴キ鐗瑰啓"},
                ],
                "recommended_usage": "recommended.food",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "media.json"
            candidates = Path(tmp) / "candidates.json"
            image_plan = Path(tmp) / "image-plan.json"
            input_path.write_text(json.dumps(media_notes, ensure_ascii=False, indent=2), encoding="utf-8")
            run_script(SKILL_DIR / "scripts" / "collect_media_candidates.py", "--input", input_path, "--output", candidates)
            run_script(SKILL_DIR / "scripts" / "build_image_plan.py", "--input", candidates, "--output", image_plan)
            media_payload = json.loads(candidates.read_text(encoding="utf-8"))
            image_payload = json.loads(image_plan.read_text(encoding="utf-8"))

        self.assertEqual(media_payload["items"][0]["platform"], "xiaohongshu")
        self.assertIn("timeline", media_payload["items"][0])
        self.assertIn("recommended_usage", media_payload["items"][0])
        self.assertIn("cover", image_payload)
        self.assertTrue(image_payload["section_images"])
        self.assertEqual(image_payload["section_images"][0]["section"], "recommended")


if __name__ == "__main__":
    unittest.main()
