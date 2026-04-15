import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(r"C:\Users\Lenovo\.codex\skills\travel-skill\scripts")
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from render_trip_site import render_trip_site  # noqa: E402


class RenderResearchReportTest(unittest.TestCase):
    def test_render_trip_site_outputs_research_report_sections(self):
        payload = {
            "trip_slug": "hangzhou-spring-trip",
            "research_report": {
                "coverage_overview": [{"site": "xiaohongshu", "coverage_status": "complete"}],
                "quick_findings": ["西湖工作日早晨更适合拍照"],
                "theme_blocks": [{"title": "景观与季节性", "recent": ["柳树已绿"], "historical": ["去年同期花期稳定"]}],
                "evidence_cards": [{"title": "小红书帖子 A", "platform": "xiaohongshu", "time_layer": "recent"}],
                "gaps": [{"site": "douyin", "reason": "insufficient_sample_size"}],
            },
        }
        guide_root = Path(r"d:\vscode\video\travel-skill-render-test")
        render_trip_site(payload, guide_root)
        html_text = (guide_root / "research-report.html").read_text(encoding="utf-8")
        self.assertIn("覆盖总览", html_text)
        self.assertIn("最新现状", html_text)
        self.assertIn("去年同期经验", html_text)
        self.assertIn("缺口与失败", html_text)


if __name__ == "__main__":
    unittest.main()
