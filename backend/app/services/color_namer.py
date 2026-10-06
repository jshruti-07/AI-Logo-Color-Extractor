"""Color naming service using nearest-neighbor search in CIELAB color space."""

import math
from typing import List, Tuple, Dict, Any
from ..utils.color_conversions import rgb_to_lab, delta_e_lab, hex_to_rgb


# Curated dictionary of named colors across shades, tints, vibrant tones, and neutrals
NAMED_COLORS_DB: List[Dict[str, Any]] = [
    # Neutrals, Whites, Grays, Blacks
    {"name": "Pure Black", "hex": "#000000"},
    {"name": "Night Shadow", "hex": "#111827"},
    {"name": "Obsidian", "hex": "#1E1E1E"},
    {"name": "Dark Charcoal", "hex": "#262626"},
    {"name": "Charcoal Gray", "hex": "#374151"},
    {"name": "Gunmetal", "hex": "#4B5563"},
    {"name": "Slate Gray", "hex": "#64748B"},
    {"name": "Cool Gray", "hex": "#6B7280"},
    {"name": "Medium Gray", "hex": "#9CA3AF"},
    {"name": "Silver Mist", "hex": "#CBD5E1"},
    {"name": "Light Gray", "hex": "#D1D5DB"},
    {"name": "Platinum", "hex": "#E2E8F0"},
    {"name": "Cloud White", "hex": "#F3F4F6"},
    {"name": "Alabaster", "hex": "#F8FAFC"},
    {"name": "Ivory White", "hex": "#FFFFF0"},
    {"name": "Pure White", "hex": "#FFFFFF"},

    # Reds & Maroons
    {"name": "Deep Maroon", "hex": "#450A0A"},
    {"name": "Wine Red", "hex": "#7F1D1D"},
    {"name": "Burgundy", "hex": "#881337"},
    {"name": "Crimson", "hex": "#991B1B"},
    {"name": "Ruby Red", "hex": "#DC2626"},
    {"name": "Vibrant Red", "hex": "#EF4444"},
    {"name": "Scarlet", "hex": "#FF2400"},
    {"name": "Fire Engine Red", "hex": "#CE2029"},
    {"name": "Coral Red", "hex": "#F87171"},
    {"name": "Salmon Pink", "hex": "#FA8072"},
    {"name": "Pastel Red", "hex": "#FCA5A5"},
    {"name": "Rose Quartz", "hex": "#FECDD3"},

    # Oranges & Warm Tones
    {"name": "Burnt Umber", "hex": "#7C2D12"},
    {"name": "Rust Orange", "hex": "#9A3412"},
    {"name": "Tangerine Dark", "hex": "#C2410C"},
    {"name": "Bright Orange", "hex": "#EA580C"},
    {"name": "Vibrant Orange", "hex": "#F97316"},
    {"name": "Safety Orange", "hex": "#FF6700"},
    {"name": "Sunset Coral", "hex": "#FB923C"},
    {"name": "Peach", "hex": "#FDBA74"},
    {"name": "Warm Apricot", "hex": "#FFD8B1"},
    {"name": "Soft Peach", "hex": "#FED7AA"},

    # Ambers & Yellows
    {"name": "Dark Amber", "hex": "#78350F"},
    {"name": "Golden Bronze", "hex": "#92400E"},
    {"name": "Deep Amber", "hex": "#B45309"},
    {"name": "Warm Amber", "hex": "#D97706"},
    {"name": "Golden Yellow", "hex": "#F59E0B"},
    {"name": "Sunflower Yellow", "hex": "#FBBF24"},
    {"name": "Lemon Yellow", "hex": "#FDE047"},
    {"name": "Electric Yellow", "hex": "#FEF08A"},
    {"name": "Canary Yellow", "hex": "#FFEF00"},
    {"name": "Champagne Gold", "hex": "#F5D77F"},
    {"name": "Pale Gold", "hex": "#FEF9C3"},

    # Limes & Chartreuses
    {"name": "Dark Olive Lime", "hex": "#365314"},
    {"name": "Olive Drab", "hex": "#4D7C0F"},
    {"name": "Moss Lime", "hex": "#65A30D"},
    {"name": "Bright Lime", "hex": "#84CC16"},
    {"name": "Vibrant Lime", "hex": "#A3E635"},
    {"name": "Chartreuse", "hex": "#7FFF00"},
    {"name": "Electric Lime", "hex": "#BEF264"},
    {"name": "Pastel Lime", "hex": "#D9F99D"},

    # Greens & Emeralds
    {"name": "Forest Green Dark", "hex": "#052E16"},
    {"name": "Deep Pine Green", "hex": "#14532D"},
    {"name": "Hunter Green", "hex": "#166534"},
    {"name": "Forest Green", "hex": "#15803D"},
    {"name": "Emerald Green", "hex": "#16A34A"},
    {"name": "Vibrant Green", "hex": "#22C55E"},
    {"name": "Jungle Green", "hex": "#2E8B57"},
    {"name": "Mint Green", "hex": "#4ADE80"},
    {"name": "Pastel Green", "hex": "#86EFAC"},
    {"name": "Seafoam Green", "hex": "#93C5FD"},
    {"name": "Soft Sage", "hex": "#BBF7D0"},

    # Teals & Aquas
    {"name": "Deep Cyan", "hex": "#083344"},
    {"name": "Dark Teal", "hex": "#134E4A"},
    {"name": "Ocean Teal", "hex": "#115E59"},
    {"name": "Deep Jade", "hex": "#0F766E"},
    {"name": "Teal", "hex": "#0D9488"},
    {"name": "Sea Green", "hex": "#14B8A6"},
    {"name": "Bright Teal", "hex": "#2DD4BF"},
    {"name": "Aquamarine", "hex": "#5EEAD4"},
    {"name": "Soft Aqua", "hex": "#99F6E4"},

    # Cyans & Light Blues
    {"name": "Midnight Cyan", "hex": "#164E63"},
    {"name": "Dark Cyan", "hex": "#155E75"},
    {"name": "Ocean Blue", "hex": "#0E7490"},
    {"name": "Cyan", "hex": "#06B6D4"},
    {"name": "Electric Cyan", "hex": "#00FFFF"},
    {"name": "Bright Sky Blue", "hex": "#22D3EE"},
    {"name": "Turquoise", "hex": "#40E0D0"},
    {"name": "Ice Blue", "hex": "#67E8F9"},
    {"name": "Pastel Cyan", "hex": "#A5F3FC"},

    # Blues & Azures
    {"name": "Deep Midnight Navy", "hex": "#030712"},
    {"name": "Navy Blue", "hex": "#0F172A"},
    {"name": "Midnight Blue", "hex": "#1E3A8A"},
    {"name": "Sapphire Blue", "hex": "#1D4ED8"},
    {"name": "Cobalt Blue", "hex": "#0047AB"},
    {"name": "Royal Blue", "hex": "#2563EB"},
    {"name": "Electric Blue", "hex": "#3B82F6"},
    {"name": "Dodger Blue", "hex": "#1E90FF"},
    {"name": "Sky Blue", "hex": "#60A5FA"},
    {"name": "Cornflower Blue", "hex": "#6495ED"},
    {"name": "Soft Azure", "hex": "#93C5FD"},
    {"name": "Baby Blue", "hex": "#BFDBFE"},

    # Indigos & Purples
    {"name": "Deep Indigo Dark", "hex": "#1E1B4B"},
    {"name": "Night Indigo", "hex": "#312E81"},
    {"name": "Deep Indigo", "hex": "#3730A3"},
    {"name": "Indigo", "hex": "#4338CA"},
    {"name": "Electric Indigo", "hex": "#4F46E5"},
    {"name": "Bright Indigo", "hex": "#6366F1"},
    {"name": "Iris Blue", "hex": "#818CF8"},
    {"name": "Periwinkle", "hex": "#A5B4FC"},
    {"name": "Lavender Mist", "hex": "#C7D2FE"},

    # Violets & Amethysts
    {"name": "Deep Violet", "hex": "#2E1065"},
    {"name": "Dark Violet", "hex": "#4C1D95"},
    {"name": "Royal Purple", "hex": "#5B21B6"},
    {"name": "Deep Purple", "hex": "#6D28D9"},
    {"name": "Purple", "hex": "#7C3AED"},
    {"name": "Electric Violet", "hex": "#8B5CF6"},
    {"name": "Amethyst", "hex": "#9966CC"},
    {"name": "Bright Violet", "hex": "#A78BFA"},
    {"name": "Lilac", "hex": "#C4B5FD"},
    {"name": "Pastel Lavender", "hex": "#DDD6FE"},

    # Fuchsias, Magentas & Pinks
    {"name": "Deep Plum", "hex": "#4A044E"},
    {"name": "Dark Magenta", "hex": "#701A75"},
    {"name": "Plum", "hex": "#86198F"},
    {"name": "Deep Fuchsia", "hex": "#A21CAF"},
    {"name": "Fuchsia Magenta", "hex": "#C026D3"},
    {"name": "Electric Fuchsia", "hex": "#D946EF"},
    {"name": "Magenta", "hex": "#FF00FF"},
    {"name": "Orchid", "hex": "#E879F9"},
    {"name": "Hot Pink", "hex": "#FF69B4"},
    {"name": "Neon Pink", "hex": "#FF1493"},
    {"name": "Deep Rose", "hex": "#BE185D"},
    {"name": "Vibrant Rose", "hex": "#E11D48"},
    {"name": "Rose Pink", "hex": "#F43F5E"},
    {"name": "Carnation Pink", "hex": "#FB7185"},
    {"name": "Blush Pink", "hex": "#FDA4AF"},
    {"name": "Baby Pink", "hex": "#FCE7F3"},

    # Browns & Warm Earth
    {"name": "Espresso Brown", "hex": "#271711"},
    {"name": "Dark Chocolate", "hex": "#3E2723"},
    {"name": "Saddle Brown", "hex": "#5D4037"},
    {"name": "Coffee Brown", "hex": "#6F4E37"},
    {"name": "Chestnut Brown", "hex": "#8D6E63"},
    {"name": "Terracotta", "hex": "#A0522D"},
    {"name": "Warm Sand", "hex": "#D7CCC8"},
    {"name": "Desert Beige", "hex": "#EFEBE9"},
]


class ColorNamer:
    """Precomputes CIELAB coordinates for fast, accurate color naming."""

    def __init__(self):
        self._cache: List[Tuple[str, str, Tuple[float, float, float]]] = []
        for item in NAMED_COLORS_DB:
            r, g, b = hex_to_rgb(item["hex"])
            lab = rgb_to_lab(r, g, b)
            self._cache.append((item["name"], item["hex"], lab))

    def get_color_name(self, r: int, g: int, b: int) -> str:
        """Find the closest human-readable color name using CIELAB Delta-E."""
        target_lab = rgb_to_lab(r, g, b)
        best_name = "Custom Color"
        best_dist = float("inf")

        for name, _hex_val, ref_lab in self._cache:
            dist = delta_e_lab(target_lab, ref_lab)
            if dist < best_dist:
                best_dist = dist
                best_name = name

        return best_name

    def get_color_name_from_hex(self, hex_str: str) -> str:
        """Find the closest human-readable color name from a HEX string."""
        r, g, b = hex_to_rgb(hex_str)
        return self.get_color_name(r, g, b)


# Singleton instance
color_namer = ColorNamer()
