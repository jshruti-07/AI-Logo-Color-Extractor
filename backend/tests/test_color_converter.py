from services.color_converter import ColorConverter
from utils.color_utils import rgb_to_hsl, hex_to_rgb, rgb_to_hex


def test_color_conversion_values():
    # Royal Blue #2563EB -> RGB (37, 99, 235)
    res = ColorConverter.convert_color("#2563EB", reason="Brand primary")
    assert res["hex"] == "#2563EB"
    assert res["rgb"] == "37, 99, 235"
    assert res["hsl"] == "221°, 83%, 53%"
    assert "Blue" in res["name"]
    assert res["text_color"] == "#FFFFFF"  # White text on royal blue background


def test_white_and_black_luminance_contrast():
    white_res = ColorConverter.convert_color("#FFFFFF")
    assert white_res["name"] == "Pure White"
    assert white_res["text_color"] == "#0F172A"  # Dark text on white background

    black_res = ColorConverter.convert_color("#000000")
    assert black_res["name"] == "Pure Black"
    assert black_res["text_color"] == "#FFFFFF"  # White text on black background


def test_hsl_algorithm():
    # Pure red
    h, s, l = rgb_to_hsl(255, 0, 0)
    assert h == 0
    assert s == 100
    assert l == 50

    # Pure green
    h, s, l = rgb_to_hsl(0, 255, 0)
    assert h == 120
    assert s == 100
    assert l == 50
