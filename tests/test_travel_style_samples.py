from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample" / "travel-style-samples"


class TravelStyleSamplesTest(unittest.TestCase):
    def test_sample_pages_and_assets_exist(self):
        required = [
            SAMPLE_ROOT / "index.html",
            SAMPLE_ROOT / "style-a-editorial.html",
            SAMPLE_ROOT / "style-b-destination.html",
            SAMPLE_ROOT / "style-c-hotel.html",
            SAMPLE_ROOT / "style-d-bento.html",
            SAMPLE_ROOT / "assets" / "shared.css",
            SAMPLE_ROOT / "assets" / "sample-data.js",
            SAMPLE_ROOT / "assets" / "sample-render.js",
            SAMPLE_ROOT / "assets" / "style-a.css",
            SAMPLE_ROOT / "assets" / "style-b.css",
            SAMPLE_ROOT / "assets" / "style-c.css",
            SAMPLE_ROOT / "assets" / "style-d.css",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        self.assertEqual(missing, [], f"Missing sample files: {missing}")

    def test_index_links_to_all_style_pages(self):
        index_path = SAMPLE_ROOT / "index.html"
        content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
        for filename in [
            "style-a-editorial.html",
            "style-b-destination.html",
            "style-c-hotel.html",
            "style-d-bento.html",
        ]:
            self.assertIn(filename, content)

    def test_each_style_page_includes_desktop_and_mobile_previews(self):
        pages = [
            SAMPLE_ROOT / "style-a-editorial.html",
            SAMPLE_ROOT / "style-b-destination.html",
            SAMPLE_ROOT / "style-c-hotel.html",
            SAMPLE_ROOT / "style-d-bento.html",
        ]
        for path in pages:
            content = path.read_text(encoding="utf-8") if path.exists() else ""
            self.assertIn("data-preview=\"desktop\"", content, f"{path.name} missing desktop preview")
            self.assertIn("data-preview=\"mobile\"", content, f"{path.name} missing mobile preview")
            self.assertIn("sample-render.js", content, f"{path.name} missing shared renderer")


if __name__ == "__main__":
    unittest.main()
