import numpy as np
from services.color_extractor import ColorExtractor
from utils.color_utils import filter_near_duplicates


def test_candidate_color_extraction():
    # Synthetic array with 3 distinct color regions
    red_pixels = np.full((100, 3), [220, 38, 38], dtype=np.uint8)
    blue_pixels = np.full((100, 3), [37, 99, 235], dtype=np.uint8)
    yellow_pixels = np.full((100, 3), [245, 158, 11], dtype=np.uint8)
    all_pixels = np.vstack([red_pixels, blue_pixels, yellow_pixels])

    extractor = ColorExtractor(n_clusters=8)
    candidates = extractor.extract_candidate_colors(all_pixels)

    assert len(candidates) >= 3
    hex_values = [c["hex"] for c in candidates]
    # Check that colors close to the inputs are found
    assert any(c.startswith("#DC") or c.startswith("#DD") or c.startswith("#DB") for c in hex_values)
    assert any(c.startswith("#25") or c.startswith("#24") or c.startswith("#26") for c in hex_values)


def test_similar_color_filtering():
    # Provide candidate colors that are nearly identical (e.g. #2563EB, #2564EC, #2562EA)
    candidates = [
        {"hex": "#2563EB", "rgb": [37, 99, 235], "percentage": 45.0},
        {"hex": "#2564EC", "rgb": [37, 100, 236], "percentage": 5.0},
        {"hex": "#2562EA", "rgb": [37, 98, 234], "percentage": 4.0},
        {"hex": "#F59E0B", "rgb": [245, 158, 11], "percentage": 30.0},
        {"hex": "#FFFFFF", "rgb": [255, 255, 255], "percentage": 16.0},
    ]

    filtered = filter_near_duplicates(candidates, distance_threshold=15.0)

    # Near duplicates of #2563EB should be merged into one representative
    assert len(filtered) == 3
    blue_candidate = next(c for c in filtered if c["hex"] == "#2563EB")
    # Percentage should have merged (45 + 5 + 4 = 54)
    assert blue_candidate["percentage"] >= 53.0
