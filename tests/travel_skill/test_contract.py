import unittest

from tests.travel_skill.helpers import ROOT, SKILL_DIR


class TravelSkillContractTest(unittest.TestCase):
    def test_skill_metadata_and_references_exist(self):
        required = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "references" / "source-priority.md",
            SKILL_DIR / "references" / "research-checklists.md",
            SKILL_DIR / "references" / "content-schema.md",
            SKILL_DIR / "references" / "sharing-modes.md",
            SKILL_DIR / "references" / "sample-gap-checklist.md",
            SKILL_DIR / "references" / "site-matrix.md",
            SKILL_DIR / "references" / "web-access-research-contract.md",
            SKILL_DIR / "scripts" / "build_web_research_runs.py",
            SKILL_DIR / "scripts" / "validate_site_coverage.py",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [], f"Missing travel skill files: {missing}")

    def test_skill_markdown_mentions_required_flow(self):
        skill_path = SKILL_DIR / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        for needle in [
            "review-gate",
            "single-file HTML",
            "web-access",
            "frontend-design",
            "ui-ux-pro-max",
            "playwright-skill",
            "verification-before-completion",
            "xiaohongshu",
            "douyin",
            "bilibili",
            "meituan",
            "dianping",
        ]:
            self.assertIn(needle, content)

    def test_openai_contract_mentions_web_access_research_run(self):
        path = SKILL_DIR / "agents" / "openai.yaml"
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        for needle in [
            "Travel Skill",
            "web-access",
            "build_research_tasks.py",
            "build_web_research_runs.py",
            "validate_site_coverage.py",
            "xiaohongshu",
            "douyin",
            "bilibili",
            "meituan",
            "dianping",
            "raw JSON",
            "comment_highlights",
            "timeline",
        ]:
            self.assertIn(needle, content)

    def test_reference_documents_include_required_keywords(self):
        checks = {
            "source-priority.md": ["# Source Priority", "official", "platform", "social", "checked_at"],
            "research-checklists.md": [
                "# Research Checklists",
                "## Transport",
                "## Weather",
                "## Food",
                "packing",
                "seasonality",
                "xiaohongshu",
                "meituan",
                "dianping",
            ],
            "content-schema.md": [
                "# Content Schema",
                "trip_request",
                "research_task",
                "fact_item",
                "`site`",
                "`site_query`",
                "`collection_method`",
                "`must_capture_fields`",
                "`evidence_level`",
                "daily-overview",
                "comprehensive",
            ],
            "sharing-modes.md": ["# Sharing Modes", "`single-html`", "`zip-bundle`", "`static-url`"],
            "sample-gap-checklist.md": ["# Sample Gap Checklist", "sample.html"],
            "site-matrix.md": ["# Site Matrix", "xiaohongshu", "douyin", "bilibili", "meituan", "dianping"],
            "web-access-research-contract.md": [
                "# Web Access Research Contract",
                "web-access",
                "site_query",
                "collection_method",
                "comment_highlights",
                "timeline",
            ],
        }
        for filename, needles in checks.items():
            path = SKILL_DIR / "references" / filename
            content = path.read_text(encoding="utf-8") if path.exists() else ""
            for needle in needles:
                self.assertIn(needle, content, f"{filename} missing keyword: {needle}")


if __name__ == "__main__":
    unittest.main()
