import math
from typing import List, Tuple, Dict, Any

# Standard reference colors for deterministic perceptual naming
COLOR_NAMES_DB = [
    ("Pure Black", (0, 0, 0)),
    ("Obsidian", (15, 23, 42)),
    ("Charcoal", (30, 41, 59)),
    ("Jet Black", (18, 18, 18)),
    ("Graphite", (51, 65, 85)),
    ("Slate Gray", (100, 116, 139)),
    ("Steel Gray", (148, 163, 184)),
    ("Silver", (203, 213, 225)),
    ("Cloud Gray", (226, 232, 240)),
    ("Off-White", (248, 250, 252)),
    ("Pure White", (255, 255, 255)),
    ("Crimson Red", (220, 38, 38)),
    ("Scarlet Red", (239, 68, 68)),
    ("Ruby Red", (185, 28, 28)),
    ("Cherry Red", (225, 29, 72)),
    ("Coral Red", (244, 63, 94)),
    ("Burgundy", (136, 19, 55)),
    ("Wine Red", (159, 18, 57)),
    ("Tangerine", (249, 115, 22)),
    ("Deep Orange", (234, 88, 12)),
    ("Burnt Orange", (194, 65, 12)),
    ("Amber", (245, 158, 11)),
    ("Golden Amber", (217, 119, 6)),
    ("Mustard", (180, 83, 9)),
    ("Sunflower Yellow", (234, 179, 8)),
    ("Gold", (202, 138, 4)),
    ("Lemon Yellow", (250, 204, 21)),
    ("Lime Green", (132, 204, 22)),
    ("Spring Green", (101, 163, 13)),
    ("Emerald Green", (16, 185, 129)),
    ("Mint Green", (52, 211, 153)),
    ("Forest Green", (5, 150, 105)),
    ("Deep Green", (4, 120, 87)),
    ("Olive Green", (77, 124, 15)),
    ("Teal", (13, 148, 136)),
    ("Dark Teal", (15, 118, 110)),
    ("Cyan", (6, 182, 212)),
    ("Aqua", (34, 211, 238)),
    ("Deep Sky Blue", (14, 165, 233)),
    ("Sky Blue", (56, 189, 248)),
    ("Royal Blue", (37, 99, 235)),
    ("Cobalt Blue", (29, 78, 216)),
    ("Navy Blue", (30, 58, 138)),
    ("Indigo", (79, 70, 229)),
    ("Deep Indigo", (67, 56, 202)),
    ("Midnight Blue", (49, 46, 129)),
    ("Violet", (124, 58, 237)),
    ("Deep Purple", (109, 40, 217)),
    ("Purple", (147, 51, 234)),
    ("Fuchsia", (192, 38, 211)),
    ("Magenta", (217, 70, 239)),
    ("Hot Pink", (236, 72, 153)),
    ("Rose Pink", (244, 114, 182)),
    ("Blush Pink", (251, 113, 133)),
    ("Bronze", (146, 64, 14)),
    ("Chocolate Brown", (120, 53, 15)),
    ("Warm Taupe", (168, 162, 158)),
    ("Espresso", (68, 64, 60)),
]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB integers (0-255) to a formatted HEX string (#RRGGBB)."""
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Parse HEX string (#RRGGBB or RRGGBB) into RGB tuple."""
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        raise ValueError(f"Invalid HEX color: {hex_str}")
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """
    Convert RGB (0-255) to HSL:
    h: 0-360 degrees
    s: 0-100 percentage
    l: 0-100 percentage
    """
    rf = r / 255.0
    gf = g / 255.0
    bf = b / 255.0

    max_c = max(rf, gf, bf)
    min_c = min(rf, gf, bf)
    diff = max_c - min_c

    l = (max_c + min_c) / 2.0

    if diff == 0:
        h = 0.0
        s = 0.0
    else:
        s = diff / (2.0 - max_c - min_c) if l > 0.5 else diff / (max_c + min_c)
        if max_c == rf:
            h = (gf - bf) / diff + (6.0 if gf < bf else 0.0)
        elif max_c == gf:
            h = (bf - rf) / diff + 2.0
        else:
            h = (rf - gf) / diff + 4.0
        h *= 60.0

    return (round(h) % 360, round(s * 100), round(l * 100))


def rgb_to_xyz(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert sRGB to CIE XYZ color space (D65 standard observer)."""
    def pivot(v: float) -> float:
        v = v / 255.0
        return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92

    rl = pivot(r) * 100.0
    gl = pivot(g) * 100.0
    bl = pivot(b) * 100.0

    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041
    return x, y, z


def xyz_to_lab(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert CIE XYZ to CIE L*a*b* color space."""
    # Reference white point D65
    ref_x = 95.047
    ref_y = 100.000
    ref_z = 108.883

    def pivot(v: float) -> float:
        return v ** (1.0 / 3.0) if v > 0.008856 else (7.787 * v) + (16.0 / 116.0)

    px = pivot(x / ref_x)
    py = pivot(y / ref_y)
    pz = pivot(z / ref_z)

    l_val = (116.0 * py) - 16.0
    a_val = 500.0 * (px - py)
    b_val = 200.0 * (py - pz)
    return l_val, a_val, b_val


def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB to CIE L*a*b*."""
    x, y, z = rgb_to_xyz(r, g, b)
    return xyz_to_lab(x, y, z)


def delta_e_cielab(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """Calculate Euclidean distance Delta E in CIE L*a*b* space."""
    return math.sqrt(
        (lab1[0] - lab2[0]) ** 2 +
        (lab1[1] - lab2[1]) ** 2 +
        (lab1[2] - lab2[2]) ** 2
    )


def color_distance(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    """Calculate perceptual color distance between two RGB colors using Delta E."""
    lab1 = rgb_to_lab(*rgb1)
    lab2 = rgb_to_lab(*rgb2)
    return delta_e_cielab(lab1, lab2)


def get_color_name(r: int, g: int, b: int) -> str:
    """Find the best matching human-readable name using Delta E perceptual distance."""
    target_lab = rgb_to_lab(r, g, b)
    closest_name = "Custom Color"
    min_dist = float("inf")

    for name, ref_rgb in COLOR_NAMES_DB:
        ref_lab = rgb_to_lab(*ref_rgb)
        dist = delta_e_cielab(target_lab, ref_lab)
        if dist < min_dist:
            min_dist = dist
            closest_name = name

    return closest_name


def get_relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance according to W3C WCAG 2.1 specifications."""
    def pivot(v: float) -> float:
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    rl = pivot(r)
    gl = pivot(g)
    bl = pivot(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def filter_near_duplicates(
    candidates: List[Dict[str, Any]],
    distance_threshold: float = 16.0
) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate candidate colors based on Delta E perceptual distance.
    Merges percentages of near duplicates into the representative candidate.
    """
    if not candidates:
        return []

    # Sort descending by percentage
    sorted_candidates = sorted(candidates, key=lambda c: c.get("percentage", 0.0), reverse=True)
    filtered: List[Dict[str, Any]] = []

    for cand in sorted_candidates:
        rgb = tuple(cand["rgb"])
        cand_lab = rgb_to_lab(*rgb)

        matched_idx = -1
        for i, kept in enumerate(filtered):
            kept_lab = rgb_to_lab(*kept["rgb"])
            dist = delta_e_cielab(cand_lab, kept_lab)
            if dist < distance_threshold:
                matched_idx = i
                break

        if matched_idx == -1:
            # New distinct color candidate
            filtered.append({
                "hex": cand["hex"].upper(),
                "rgb": cand["rgb"],
                "percentage": round(float(cand["percentage"]), 1),
            })
        else:
            # Merge percentage into the representative color
            filtered[matched_idx]["percentage"] = round(
                filtered[matched_idx]["percentage"] + float(cand["percentage"]), 1
            )

    # Recalculate relative importance (normalize to percentage scale or keep tracked weight)
    total_pct = sum(c["percentage"] for c in filtered)
    if total_pct > 0:
        for c in filtered:
            c["relative_importance"] = round((c["percentage"] / total_pct) * 100.0, 1)

    return filtered
