"""Color conversion and accessibility utilities."""

import math
from typing import Tuple, Dict, Any


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values (0-255) to a standard uppercase HEX string (#RRGGBB)."""
    r = max(0, min(255, int(round(r))))
    g = max(0, min(255, int(round(g))))
    b = max(0, min(255, int(round(b))))
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert HEX string (#RRGGBB or RRGGBB) to (r, g, b) integers."""
    clean_hex = hex_str.strip().lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join(c * 2 for c in clean_hex)
    if len(clean_hex) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    r = int(clean_hex[0:2], 16)
    g = int(clean_hex[2:4], 16)
    b = int(clean_hex[4:6], 16)
    return (r, g, b)


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """
    Convert RGB (0-255) to HSL:
    H: 0-360 degrees
    S: 0-100 percentage
    L: 0-100 percentage
    """
    r_norm = max(0, min(255, r)) / 255.0
    g_norm = max(0, min(255, g)) / 255.0
    b_norm = max(0, min(255, b)) / 255.0

    c_max = max(r_norm, g_norm, b_norm)
    c_min = min(r_norm, g_norm, b_norm)
    delta = c_max - c_min

    # Calculate Lightness
    l = (c_max + c_min) / 2.0

    # Calculate Saturation
    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        s = delta / (1.0 - abs(2.0 * l - 1.0)) if (1.0 - abs(2.0 * l - 1.0)) != 0 else 0.0

        # Calculate Hue
        if c_max == r_norm:
            h = 60.0 * (((g_norm - b_norm) / delta) % 6)
        elif c_max == g_norm:
            h = 60.0 * (((b_norm - r_norm) / delta) + 2)
        else:
            h = 60.0 * (((r_norm - g_norm) / delta) + 4)

    h_deg = int(round(h)) % 360
    s_pct = int(round(s * 100))
    l_pct = int(round(l * 100))

    return (h_deg, s_pct, l_pct)


def format_rgb(r: int, g: int, b: int) -> str:
    """Format RGB as 'rgb(R, G, B)'."""
    return f"rgb({int(r)}, {int(g)}, {int(b)})"


def format_hsl(h: int, s: int, l: int) -> str:
    """Format HSL as 'hsl(H, S%, L%)'."""
    return f"hsl({int(h)}, {int(s)}%, {int(l)}%)"


def get_relative_luminance(r: int, g: int, b: int) -> float:
    """
    Calculate WCAG 2.1 relative luminance (0.0 - 1.0).
    Formula: 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
    """
    def channel_linear(val: int) -> float:
        v = val / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r_lin = channel_linear(r)
    g_lin = channel_linear(g)
    b_lin = channel_linear(b)

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def get_contrast_ratio(lum1: float, lum2: float) -> float:
    """
    Calculate contrast ratio between two luminance values according to WCAG 2.1.
    Formula: (L1 + 0.05) / (L2 + 0.05) where L1 is the lighter of the two.
    """
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def get_color_accessibility(r: int, g: int, b: int) -> Dict[str, Any]:
    """Calculate accessibility metrics: text contrast against white and black."""
    lum = get_relative_luminance(r, g, b)
    contrast_white = get_contrast_ratio(lum, 1.0)
    contrast_black = get_contrast_ratio(lum, 0.0)

    preferred_text_color = "#FFFFFF" if contrast_white >= contrast_black else "#000000"

    return {
        "luminance": round(lum, 4),
        "contrast_with_white": contrast_white,
        "contrast_with_black": contrast_black,
        "preferred_text_color": preferred_text_color,
        "is_dark": lum < 0.45
    }


def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert sRGB (0-255) to CIE L*a*b* color space for perceptual distance calculations.
    Uses D65 standard illuminant.
    """
    # 1. Linearize sRGB to RGB
    def gamma_inv(v: float) -> float:
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r_lin = gamma_inv(r / 255.0)
    g_lin = gamma_inv(g / 255.0)
    b_lin = gamma_inv(b / 255.0)

    # 2. Convert to XYZ (D65)
    x = (r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375) / 0.95047
    y = (r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750) / 1.00000
    z = (r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041) / 1.08883

    # 3. Convert XYZ to Lab
    def f(t: float) -> float:
        delta = 6.0 / 29.0
        return t ** (1.0 / 3.0) if t > delta ** 3 else (t / (3.0 * delta ** 2)) + (4.0 / 29.0)

    fx = f(x)
    fy = f(y)
    fz = f(z)

    l_star = 116.0 * fy - 16.0
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)

    return (round(l_star, 3), round(a_star, 3), round(b_star, 3))


def delta_e_lab(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """Calculate Euclidean distance in CIELAB space (CIE76 Delta-E)."""
    dl = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dl * dl + da * da + db * db)
