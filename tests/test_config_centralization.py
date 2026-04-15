import importlib
from pathlib import Path
import sys
import tempfile
import unittest

from tests.helpers import SKILL_DIR


def load_module(module_name: str):
    scripts_dir = str(SKILL_DIR / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return importlib.import_module(module_name)


class TravelConfigCentralizationTest(unittest.TestCase):
    def test_site_coverage_matrix_comes_from_shared_config(self):
        config = load_module("travel_config")
        research_runs = load_module("build_web_research_runs")
        validator = load_module("validate_site_coverage")
        review_packet = load_module("generate_review_packet")

        self.assertIs(research_runs.SITE_COVERAGE_TARGETS, config.SITE_COVERAGE_TARGETS)
        self.assertIs(validator.REQUIRED_SITE_MATRIX, config.SITE_COVERAGE_TARGETS)
        self.assertIs(review_packet.REQUIRED_SITE_MATRIX, config.SITE_COVERAGE_TARGETS)

    def test_template_catalog_comes_from_shared_config(self):
        config = load_module("travel_config")
        renderer = load_module("render_trip_site")
        portal = load_module("build_portal")
        packager = load_module("package_trip")
        verifier = load_module("verify_trip")

        self.assertIs(renderer.RENDER_TEMPLATES, config.TEMPLATE_IDS)
        self.assertIs(portal.TEMPLATES, config.SORTED_TEMPLATE_IDS)
        self.assertIs(packager.TEMPLATES, config.SORTED_TEMPLATE_IDS)
        self.assertIs(verifier.EXPECTED_TEMPLATES, config.SORTED_TEMPLATE_IDS)
        self.assertIs(renderer.TEMPLATE_LABELS, config.TEMPLATE_LABELS)
        self.assertIs(renderer.TEMPLATE_SECTIONS, config.TEMPLATE_SECTIONS)

    def test_transport_threshold_comes_from_shared_config(self):
        config = load_module("travel_config")
        guide_model = load_module("build_guide_model")

        self.assertEqual(config.FLIGHT_HYBRID_THRESHOLD_KM, 1000)
        self.assertEqual(
            guide_model._transport_rule(config.FLIGHT_HYBRID_THRESHOLD_KM - 1),
            {"long_distance": "within-1000km"},
        )
        self.assertEqual(
            guide_model._transport_rule(config.FLIGHT_HYBRID_THRESHOLD_KM + 1),
            {"long_distance": "over-1000km"},
        )

    def test_output_layers_and_publish_artifacts_come_from_shared_config(self):
        config = load_module("travel_config")
        guide_model = load_module("build_guide_model")
        filler = load_module("fill_missing_sections")
        portal = load_module("build_portal")
        packager = load_module("package_trip")

        self.assertIs(guide_model.OUTPUT_KEYS, config.GUIDE_OUTPUT_KEYS)
        self.assertIs(filler.OUTPUT_KEYS, config.GUIDE_OUTPUT_KEYS)
        self.assertEqual(config.PUBLISH_ARTIFACTS["portal"], "portal.html")
        self.assertEqual(config.PUBLISH_ARTIFACTS["recommended"], "recommended.html")
        self.assertEqual(config.PUBLISH_ARTIFACTS["share"], "share.html")
        self.assertEqual(config.PUBLISH_ARTIFACTS["summary"], "trip-summary.txt")
        self.assertEqual(config.PUBLISH_ARTIFACTS["sources_markdown"], "notes/sources.md")
        self.assertEqual(config.PUBLISH_ARTIFACTS["sources_html"], "notes/sources.html")
        self.assertIs(portal.PUBLISH_ARTIFACTS, config.PUBLISH_ARTIFACTS)
        self.assertIs(packager.PUBLISH_ARTIFACTS, config.PUBLISH_ARTIFACTS)

    def test_sharing_modes_reference_uses_guides_root(self):
        sharing_modes = (SKILL_DIR / "references" / "sharing-modes.md").read_text(encoding="utf-8")

        self.assertIn("guides/<slug>/desktop/editorial/index.html", sharing_modes)
        self.assertIn("guides/<slug>/mobile/editorial/index.html", sharing_modes)
        self.assertNotIn("trips/<slug>/desktop", sharing_modes)
        self.assertNotIn("trips/<slug>/mobile", sharing_modes)

    def test_sharing_modes_reference_lists_publish_artifacts_from_config(self):
        config = load_module("travel_config")
        sharing_modes = (SKILL_DIR / "references" / "sharing-modes.md").read_text(encoding="utf-8")

        self.assertIn(config.PUBLISH_ARTIFACTS["portal"], sharing_modes)
        self.assertIn(config.PUBLISH_ARTIFACTS["recommended"], sharing_modes)
        self.assertIn(config.PUBLISH_ARTIFACTS["share"], sharing_modes)
        self.assertIn("package.zip", sharing_modes)

    def test_package_summary_text_uses_publish_artifact_config(self):
        packager = load_module("package_trip")

        original = dict(packager.PUBLISH_ARTIFACTS)
        try:
            packager.PUBLISH_ARTIFACTS["summary"] = "bundle-summary.txt"
            packager.PUBLISH_ARTIFACTS["sources_markdown"] = "notes/references.md"
            packager.PUBLISH_ARTIFACTS["sources_html"] = "notes/references.html"
            packager.PUBLISH_ARTIFACTS["share"] = "share-bundle.html"
            packager.PUBLISH_ARTIFACTS["recommended"] = "route-bundle.html"
            with tempfile.TemporaryDirectory() as tmp:
                guide_root = Path(tmp) / "demo-trip"
                (guide_root / "desktop" / "route-first").mkdir(parents=True)
                summary = packager.build_summary(
                    guide_root,
                    Path(tmp) / "portal-custom.html",
                    Path(tmp) / "route-bundle.html",
                    Path(tmp) / "share-bundle.html",
                )
        finally:
            packager.PUBLISH_ARTIFACTS.clear()
            packager.PUBLISH_ARTIFACTS.update(original)

        self.assertIn("notes/references.md", summary)
        self.assertIn("notes/references.html", summary)
        self.assertIn("share-bundle.html", summary)
        self.assertIn("route-bundle.html", summary)
        self.assertIn("bundle-summary.txt", summary)


if __name__ == "__main__":
    unittest.main()
