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
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [], f"Missing travel skill files: {missing}")

    def test_skill_markdown_mentions_required_flow(self):
        skill_path = SKILL_DIR / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        for needle in ["review-gate", "single-file HTML", "web-access", "frontend-design", "playwright-skill"]:
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
            ],
            "content-schema.md": [
                "# Content Schema",
                "trip_request",
                "research_task",
                "fact_item",
                "daily-overview",
                "comprehensive",
            ],
            "sharing-modes.md": ["# Sharing Modes", "`single-html`", "`zip-bundle`", "`static-url`"],
            "sample-gap-checklist.md": ["# Sample Gap Checklist", "订票顺序", "价格区间", "每日执行表", "风险与避坑提示"],
        }
        for filename, needles in checks.items():
            path = SKILL_DIR / "references" / filename
            content = path.read_text(encoding="utf-8") if path.exists() else ""
            for needle in needles:
                self.assertIn(needle, content, f"{filename} missing keyword: {needle}")


if __name__ == "__main__":
    unittest.main()
