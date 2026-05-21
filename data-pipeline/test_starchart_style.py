import importlib.util
import pathlib
import sys
import types
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("starchart_server.py")


def load_module():
    flask_stub = types.ModuleType("flask")

    class Flask:
        def __init__(self, *_args, **_kwargs):
            pass

        def route(self, *_args, **_kwargs):
            return lambda func: func

        def run(self, *_args, **_kwargs):
            pass

    flask_stub.Flask = Flask
    flask_stub.request = types.SimpleNamespace(method="GET", args={}, get_json=lambda **_kwargs: {})
    flask_stub.jsonify = lambda *args, **kwargs: (args, kwargs)
    flask_stub.send_file = lambda *args, **kwargs: types.SimpleNamespace(headers={})
    sys.modules.setdefault("flask", flask_stub)

    spec = importlib.util.spec_from_file_location("starchart_server", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StarChartStyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chart = load_module()

    def test_magnitude_to_marker_makes_bright_stars_dominant_without_bloating_faint_stars(self):
        sizes = [
            self.chart.magnitude_to_marker(-1.0),
            self.chart.magnitude_to_marker(2.0),
            self.chart.magnitude_to_marker(6.5),
        ]

        self.assertGreater(sizes[0], sizes[1])
        self.assertGreater(sizes[1], sizes[2])
        self.assertGreaterEqual(sizes[0], 42.0)
        self.assertLessEqual(sizes[2], 7.0)

    def test_format_ra_and_dec_labels_use_real_chart_units(self):
        self.assertEqual(self.chart.format_ra_label(83.82), "05h35m")
        self.assertEqual(self.chart.format_ra_label(359.9), "00h00m")
        self.assertEqual(self.chart.format_dec_label(-5.39), "-05°23'")
        self.assertEqual(self.chart.format_dec_label(12.0), "+12°00'")

    def test_choose_label_stars_limits_density_and_prefers_named_bright_stars(self):
        stars = {
            1: {"ra": 83.0, "dec": -5.0, "mag": 5.2, "proper": ""},
            2: {"ra": 84.0, "dec": -5.2, "mag": 1.2, "proper": "Rigel"},
            3: {"ra": 85.2, "dec": -6.4, "mag": 2.7, "proper": ""},
            4: {"ra": 120.0, "dec": 40.0, "mag": 0.5, "proper": "Far"},
        }

        labels = self.chart.choose_label_stars(stars, 83.8, -5.3, 15.0, max_labels=2)

        self.assertEqual([label["name"] for label in labels], ["Rigel", "HIP3"])

    def test_parse_catalog_coordinates_for_deep_sky_overlays(self):
        self.assertAlmostEqual(self.chart.parse_hms_to_degrees("05:35:17.3"), 83.822083, places=5)
        self.assertAlmostEqual(self.chart.parse_dms_to_degrees("-05:23:28"), -5.391111, places=5)
        self.assertAlmostEqual(self.chart.parse_dms_to_degrees("+41:16:09"), 41.269167, places=5)

    def test_hyg_ra_hours_are_converted_to_degrees(self):
        self.assertAlmostEqual(self.chart.hyg_ra_to_degrees("5.588"), 83.82, places=2)
        self.assertAlmostEqual(self.chart.hyg_ra_to_degrees("23.9"), 358.5, places=2)

    def test_gnomonic_chart_scale_uses_tangent_of_half_field(self):
        self.assertAlmostEqual(self.chart.chart_scale(35.0), 0.3153, places=3)

    def test_mobile_style_uses_immersive_sky_layers(self):
        style = self.chart.resolve_chart_style("mobile")

        self.assertEqual(style["background_top"], "#2b3d58")
        self.assertGreater(style["constellation_fill_alpha"], 0.18)
        self.assertGreater(style["bright_star_glow"], 5.0)
        self.assertTrue(style["show_mobile_chrome"])

    def test_convex_hull_builds_constellation_art_surface(self):
        points = [(0, 0), (2, 0), (1, 1), (0.5, 0.3), (0, 2)]

        hull = self.chart.convex_hull(points)

        self.assertEqual(hull, [(0, 0), (2, 0), (0, 2)])

    def test_visible_planet_markers_are_filtered_by_field_of_view(self):
        planets = self.chart.visible_planet_markers(310.0, -17.0, 35.0)

        names = [planet["name"] for planet in planets]
        self.assertIn("Mars", names)
        self.assertIn("Pluto", names)
        self.assertNotIn("Jupiter", names)


if __name__ == "__main__":
    unittest.main()
