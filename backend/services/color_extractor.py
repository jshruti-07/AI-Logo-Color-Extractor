from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import KMeans

from utils.color_utils import rgb_to_hex, filter_near_duplicates


class ColorExtractor:
    """Extracts candidate colors using K-Means clustering and perceptual deduplication."""

    def __init__(self, n_clusters: int = 16, sample_size: int = 15000):
        self.n_clusters = n_clusters
        self.sample_size = sample_size

    def extract_candidate_colors(
        self,
        pixels: np.ndarray,
        distance_threshold: float = 16.0
    ) -> List[Dict[str, Any]]:
        """
        Extract 10-20 candidate colors from visible pixels, compute frequencies,
        and remove near-duplicates.
        """
        if len(pixels) == 0:
            return []

        # Subsample pixels if the array is large to guarantee fast, deterministic clustering
        if len(pixels) > self.sample_size:
            indices = np.random.RandomState(42).choice(
                len(pixels), size=self.sample_size, replace=False
            )
            sampled_pixels = pixels[indices]
        else:
            sampled_pixels = pixels

        # Dynamically adjust cluster count if unique pixels are fewer than n_clusters
        unique_colors_count = len(np.unique(sampled_pixels, axis=0))
        k = min(self.n_clusters, unique_colors_count)
        if k < 1:
            k = 1

        kmeans = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=5,
            max_iter=100
        )
        labels = kmeans.fit_predict(sampled_pixels)
        centers = kmeans.cluster_centers_

        # Calculate frequency for each cluster
        total_samples = len(labels)
        raw_candidates: List[Dict[str, Any]] = []

        for idx in range(k):
            count = np.sum(labels == idx)
            percentage = (count / total_samples) * 100.0

            center_rgb = np.clip(np.round(centers[idx]), 0, 255).astype(int)
            r, g, b = int(center_rgb[0]), int(center_rgb[1]), int(center_rgb[2])
            hex_val = rgb_to_hex(r, g, b)

            raw_candidates.append({
                "hex": hex_val,
                "rgb": [r, g, b],
                "percentage": round(percentage, 1),
            })

        # Remove near-duplicate colors using LAB Delta E perceptual distance
        deduplicated = filter_near_duplicates(raw_candidates, distance_threshold=distance_threshold)

        # If deduplication resulted in fewer than 3 colors but raw had more, relax threshold slightly
        if len(deduplicated) < 3 and len(raw_candidates) >= 3:
            deduplicated = filter_near_duplicates(raw_candidates, distance_threshold=8.0)

        return deduplicated
