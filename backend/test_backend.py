"""Unit and integration test suite for AI Logo Color Extractor backend."""

import io
import unittest
import numpy as np
from PIL import Image

from app.utils.color_conversions import (
    rgb_to_hex,
    hex_to_rgb,
    rgb_to_hsl,
    format_rgb,
    format_hsl,
    get_relative_luminance,
    get_contrast_ratio,
)
from app.services.color_namer import color_namer
from app.services.image_processor import validate_and_preprocess_image
from app.services.color_extractor import extract_candidate_colors
from app.services.llm_selector import select_colors_with_heuristics


class TestColorExtractor(unittest.TestCase):
    """Test suite for color extraction and conversion logic."""

    def test_rgb_to_hex(self):
        self.assertEqual(rgb_to_hex(255, 0, 0), "#FF0000")
        self.assertEqual(rgb_to_hex(0, 255, 0), "#00FF00")
        self.assertEqual(rgb_to_hex(0, 0, 255), "#0000FF")
        self.assertEqual(rgb_to_hex(255, 255, 255), "#FFFFFF")
        self.assertEqual(rgb_to_hex(0, 0, 0), "#000000")

    def test_hex_to_rgb(self):
        self.assertEqual(hex_to_rgb("#FF0000"), (255, 0, 0))
        self.assertEqual(hex_to_rgb("#00FF00"), (0, 255, 0))
        self.assertEqual(hex_to_rgb("#1E40AF"), (30, 64, 175))

    def test_rgb_to_hsl(self):
        h, s, l = rgb_to_hsl(255, 0, 0)
        self.assertEqual(h, 0)
        self.assertEqual(s, 100)
        self.assertEqual(l, 50)

        h, s, l = rgb_to_hsl(0, 255, 0)
        self.assertEqual(h, 120)
        self.assertEqual(s, 100)
        self.assertEqual(l, 50)

    def test_color_namer(self):
        self.assertIn("Red", color_namer.get_color_name(255, 0, 0))
        self.assertIn("Blue", color_namer.get_color_name(0, 100, 255))
        self.assertIn("White", color_namer.get_color_name(255, 255, 255))
        self.assertIn("Black", color_namer.get_color_name(0, 0, 0))

    def test_transparent_png_handling(self):
        # Create a synthetic 100x100 RGBA image with 70% transparent and 30% vibrant blue
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0)) # fully transparent
        # Paint a 30x100 rectangle in royal blue (37, 99, 235, 255)
        for x in range(30):
            for y in range(100):
                img.putpixel((x, y), (37, 99, 235, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        pixels, metadata = validate_and_preprocess_image(raw_bytes, "test_logo.png")
        self.assertTrue(metadata.has_alpha)
        self.assertGreater(metadata.filtered_transparent_percentage, 60.0)
        self.assertGreaterEqual(len(pixels), 2000)

        # Extract candidate colors
        candidates = extract_candidate_colors(pixels)
        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["hex"], "#2563EB")

        # Test heuristic selector
        p, s, a, summary = select_colors_with_heuristics(candidates)
        self.assertEqual(p["hex"], "#2563EB")
        self.assertIsNotNone(summary)


if __name__ == "__main__":
    unittest.main()
