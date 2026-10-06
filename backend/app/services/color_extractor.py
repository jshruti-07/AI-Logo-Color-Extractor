"""Color extraction and clustering using K-Means."""

from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.cluster import MiniBatchKMeans, KMeans
from ..config import settings
from ..schemas.palette import CandidateColor, RGBValues, HSLValues, ColorAccessibility
from ..utils.color_conversions import (
    rgb_to_hex,
    rgb_to_hsl,
    format_rgb,
    format_hsl,
    get_color_accessibility,
    rgb_to_lab,
    delta_e_lab,
)
from .color_namer import color_namer


def extract_candidate_colors(pixels: np.ndarray) -> List[Dict[str, Any]]:
    """
    Extracts 10-18 distinct candidate colors from pixel array using KMeans.

    Args:
        pixels: Array of shape (N, 3) containing RGB values (0-255).

    Returns:
        List of candidate color dictionaries sorted by dominance percentage.
    """
    total_pixels = len(pixels)
    if total_pixels == 0:
        return []

    # Determine optimal number of clusters (between min and max clusters)
    # Check number of unique colors in sample
    unique_colors_count = len(np.unique(pixels, axis=0))
    n_clusters = min(settings.MAX_CLUSTERS, max(settings.MIN_CLUSTERS, unique_colors_count))
    if n_clusters < 1:
        n_clusters = 1

    # Use MiniBatchKMeans for rapid convergence and crisp clustering
    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        random_state=42,
        batch_size=1024,
        max_iter=100,
        n_init=3,
    )
    kmeans.fit(pixels)

    centers = kmeans.cluster_centers_  # Shape: (n_clusters, 3)
    labels = kmeans.labels_            # Shape: (N,)

    # Count occurrences of each cluster label
    counts = np.bincount(labels, minlength=n_clusters)

    # Filter out empty clusters and merge clusters that are perceptually identical (Delta-E < 4.0)
    candidates_raw = []
    for idx in range(n_clusters):
        count = counts[idx]
        if count == 0:
            continue
        center_rgb = centers[idx]
        r = int(np.clip(round(center_rgb[0]), 0, 255))
        g = int(np.clip(round(center_rgb[1]), 0, 255))
        b = int(np.clip(round(center_rgb[2]), 0, 255))
        pct = (count / total_pixels) * 100.0
        lab = rgb_to_lab(r, g, b)
        candidates_raw.append({
            "r": r,
            "g": g,
            "b": b,
            "count": count,
            "percentage": pct,
            "lab": lab
        })

    # Deduplicate / merge clusters with very close perceptual distance (Delta-E < 5.0)
    merged_candidates: List[Dict[str, Any]] = []
    for cand in candidates_raw:
        merged = False
        for target in merged_candidates:
            dist = delta_e_lab(cand["lab"], target["lab"])
            if dist < 5.0:
                # Merge into existing target
                total_count = target["count"] + cand["count"]
                # Weighted average RGB
                target["r"] = int(round((target["r"] * target["count"] + cand["r"] * cand["count"]) / total_count))
                target["g"] = int(round((target["g"] * target["count"] + cand["g"] * cand["count"]) / total_count))
                target["b"] = int(round((target["b"] * target["count"] + cand["b"] * cand["count"]) / total_count))
                target["count"] = total_count
                target["percentage"] = (total_count / total_pixels) * 100.0
                target["lab"] = rgb_to_lab(target["r"], target["g"], target["b"])
                merged = True
                break
        if not merged:
            merged_candidates.append(cand.copy())

    # Sort by percentage share descending
    merged_candidates.sort(key=lambda x: x["percentage"], reverse=True)

    # Format structured candidate list
    final_candidates: List[Dict[str, Any]] = []
    for idx, item in enumerate(merged_candidates, start=1):
        r, g, b = item["r"], item["g"], item["b"]
        hex_code = rgb_to_hex(r, g, b)
        h, s, l = rgb_to_hsl(r, g, b)
        name = color_namer.get_color_name(r, g, b)
        acc = get_color_accessibility(r, g, b)
        
        final_candidates.append({
            "id": idx,
            "hex": hex_code,
            "name": name,
            "rgb": format_rgb(r, g, b),
            "hsl": format_hsl(h, s, l),
            "rgb_values": {"r": r, "g": g, "b": b},
            "hsl_values": {"h": h, "s": s, "l": l},
            "percentage": round(item["percentage"], 2),
            "accessibility": acc,
            "is_selected_role": None,
        })

    return final_candidates
