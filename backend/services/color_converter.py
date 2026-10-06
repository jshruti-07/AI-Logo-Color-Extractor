from typing import Dict, Any, Union, Tuple
from utils.color_utils import (
    hex_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    get_color_name,
    get_relative_luminance
)


class ColorConverter:
    """Calculates HEX, RGB, HSL strings, human-readable names, and luminance contrast."""

    @staticmethod
    def convert_color(color_input: Union[str, Tuple[int, int, int]], reason: str = "") -> Dict[str, Any]:
        """
        Takes a HEX string or RGB tuple and returns standardized color representation:
        {
            "name": "Royal Blue",
            "hex": "#2563EB",
            "rgb": "37, 99, 235",
            "hsl": "217°, 91%, 60%",
            "reason": "Dominant brand identity color",
            "luminance": 0.18,
            "text_color": "#FFFFFF"
        }
        """
        if isinstance(color_input, str):
            rgb = hex_to_rgb(color_input)
            hex_val = color_input.upper()
            if not hex_val.startswith("#"):
                hex_val = f"#{hex_val}"
        else:
            rgb = tuple(int(c) for c in color_input[:3])
            hex_val = rgb_to_hex(*rgb)

        r, g, b = rgb
        h, s, l = rgb_to_hsl(r, g, b)
        name = get_color_name(r, g, b)
        lum = get_relative_luminance(r, g, b)
        text_color = "#FFFFFF" if lum < 0.55 else "#0F172A"

        return {
            "name": name,
            "hex": hex_val,
            "rgb": f"{r}, {g}, {b}",
            "hsl": f"{h}°, {s}%, {l}%",
            "reason": reason,
            "luminance": round(lum, 3),
            "text_color": text_color,
        }
