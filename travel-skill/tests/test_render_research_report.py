import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_TMP_ROOT = REPO_ROOT / ".tmp-tests"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from render_trip_site import render_trip_site  # noqa: E402


class RenderResearchReportTest(unittest.TestCase):
    def test_render_trip_site_outputs_media_evidence_cards(self):
        payload = {
            "trip_slug": "hangzhou-spring-trip",
            "research_report": {
                "coverage_overview": [{"site": "xiaohongshu", "coverage_status": "complete"}],
                "quick_findings": ["West Lake is quieter on weekday mornings."],
                "theme_blocks": [
                    {
                        "title": "Seasonal feeling",
                        "recent": ["Willows are already green."],
                        "historical": ["Flower timing was stable in the same period last year."],
                    }
                ],
                "evidence_cards": [
                    {
                        "title": "Xiaohongshu post A",
                        "platform": "xiaohongshu",
                        "time_layer": "recent",
                        "summary": "Queue conditions are acceptable before 8am.",
                        "coverage_status": "complete",
                    }
                ],
                "selected_frames": [
                    {
                        "title": "West Lake crowd check",
                        "platform": "douyin",
                        "time_layer": "recent",
                        "coverage_status": "partial",
                        "image_url": "https://cdn.example.com/frame-001.jpg",
                        "image_hint": "Crowd density near the causeway",
                        "evidence_score": 0.92,
                    }
                ],
                "gaps": [{"site": "douyin", "reason": "insufficient_sample_size"}],
            },
        }
        guide_root = TEST_TMP_ROOT / "render-research-report"
        if guide_root.exists():
            import shutil

            shutil.rmtree(guide_root)
        guide_root.mkdir(parents=True, exist_ok=True)

        render_trip_site(payload, guide_root)
        html_text = (guide_root / "research-report.html").read_text(encoding="utf-8")
        self.assertIn('data-page="research-report"', html_text)
        self.assertIn("selected-frame", html_text)
        self.assertIn("coverage_status", html_text)


if __name__ == "__main__":
    unittest.main()
