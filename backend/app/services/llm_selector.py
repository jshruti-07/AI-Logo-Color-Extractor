"""LLM-based semantic color selection using OpenAI, with intelligent color-theory fallback."""

import json
import logging
from typing import List, Dict, Any, Tuple
from openai import OpenAI, OpenAIError
from ..config import settings
from ..schemas.palette import ColorItem, RGBValues, HSLValues, ColorAccessibility
from ..utils.color_conversions import hex_to_rgb, rgb_to_hsl, format_rgb, format_hsl, get_color_accessibility
from .color_namer import color_namer

logger = logging.getLogger("ai_color_extractor.llm")


def select_colors_with_heuristics(
    candidates: List[Dict[str, Any]],
    reason_prefix: str = "Extracted via color theory clustering"
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], str]:
    """
    Intelligent fallback heuristic based on brand design rules and color theory:
    - Primary: High percentage, high chroma/saturation, dominant brand identity.
    - Secondary: Supporting harmonious color (contrasting lightness or complementary hue with good percentage).
    - Accent: Distinctive, high vibrancy/saturation, standout contrast for call-to-actions.
    """
    if not candidates:
        raise ValueError("Cannot select colors from empty candidate list.")

    if len(candidates) == 1:
        c = candidates[0]
        return c, c, c, "Single color extracted from logo."

    if len(candidates) == 2:
        return candidates[0], candidates[1], candidates[0], "Dual-tone palette extracted from logo."

    # Filter out pure whites/grays for primary if vibrant colored candidates exist
    colored_candidates = [
        c for c in candidates 
        if c.get("hsl_values", {}).get("s", 0) > 15 and 10 < c.get("hsl_values", {}).get("l", 0) < 90
    ]
    pool = colored_candidates if colored_candidates else candidates

    # 1. Primary: The strongest brand color (highest percentage among colored, or top candidate)
    primary = pool[0]

    # 2. Secondary: Supporting color with good contrast or harmony to primary
    remaining = [c for c in candidates if c["hex"] != primary["hex"]]
    if not remaining:
        remaining = candidates

    # Find secondary: prefer color with distinct lightness or hue
    primary_hsl = primary.get("hsl_values", {"h": 0, "s": 0, "l": 50})
    best_secondary = remaining[0]
    best_sec_score = -1.0

    for cand in remaining:
        c_hsl = cand.get("hsl_values", {"h": 0, "s": 0, "l": 50})
        lightness_diff = abs(c_hsl["l"] - primary_hsl["l"])
        hue_diff = min(abs(c_hsl["h"] - primary_hsl["h"]), 360 - abs(c_hsl["h"] - primary_hsl["h"]))
        score = (cand["percentage"] * 1.5) + (lightness_diff * 0.8) + (hue_diff * 0.2)
        if score > best_sec_score:
            best_sec_score = score
            best_secondary = cand

    # 3. Accent: High saturation/vibrancy with highest visual distinctiveness
    accent_pool = [c for c in candidates if c["hex"] not in (primary["hex"], best_secondary["hex"])]
    if not accent_pool:
        accent_pool = [c for c in candidates if c["hex"] != primary["hex"]] or candidates

    best_accent = accent_pool[0]
    best_accent_score = -1.0

    for cand in accent_pool:
        c_hsl = cand.get("hsl_values", {"h": 0, "s": 0, "l": 50})
        sat = c_hsl["s"]
        lum = cand.get("accessibility", {}).get("luminance", 0.5)
        # Accent values high saturation and distinctiveness from primary
        hue_dist = min(abs(c_hsl["h"] - primary_hsl["h"]), 360 - abs(c_hsl["h"] - primary_hsl["h"]))
        score = (sat * 1.8) + (hue_dist * 0.5) + (cand["percentage"] * 0.5)
        if score > best_accent_score:
            best_accent_score = score
            best_accent = cand

    summary = (
        f"Harmonious brand palette identified with {primary['name']} as primary brand identity, "
        f"{best_secondary['name']} as secondary foundation, and {best_accent['name']} as vivid accent."
    )

    return primary, best_secondary, best_accent, summary


def select_colors_with_llm(
    candidates: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], str, str]:
    """
    Calls OpenAI API to assign Primary, Secondary, and Accent roles from the candidate list.
    Falls back to heuristic rules if OpenAI is not configured or errors out.

    Returns:
        Tuple of (primary_dict, secondary_dict, accent_dict, ai_summary, source_str)
    """
    api_key = settings.OPENAI_API_KEY.strip()
    if not api_key:
        logger.info("OpenAI API key not configured. Using color-theory heuristic selector.")
        p, s, a, summary = select_colors_with_heuristics(candidates)
        return p, s, a, summary, "heuristic_fallback"

    # Prepare candidate payload for the LLM
    candidate_summary = []
    candidates_by_hex = {}
    for c in candidates:
        hex_code = c["hex"].upper()
        candidates_by_hex[hex_code] = c
        candidate_summary.append({
            "hex": hex_code,
            "name": c["name"],
            "rgb": c["rgb"],
            "hsl": c["hsl"],
            "percentage": f"{c['percentage']}%",
            "is_dark": c.get("accessibility", {}).get("is_dark", False)
        })

    prompt_content = f"""You are an expert brand designer and art director.
You are given a list of extracted candidate colors from a logo with their percentages and properties:

{json.dumps(candidate_summary, indent=2)}

TASK:
Select exactly THREE colors from the candidate list above:
1. PRIMARY: The strongest, most defining brand color that anchors the logo.
2. SECONDARY: A supporting color that harmonizes or contrasts well with the primary color to build depth.
3. ACCENT: A visually distinctive, vibrant, or eye-catching color ideal for CTAs, highlights, or badges.

CRITICAL RULES:
- You MUST ONLY select hex codes from the candidate list above. Do NOT invent new colors.
- Return valid strict JSON without markdown fences.

Expected JSON schema:
{{
  "primary_hex": "#HEX_CODE",
  "primary_reasoning": "Brief 1-sentence design rationale",
  "secondary_hex": "#HEX_CODE",
  "secondary_reasoning": "Brief 1-sentence design rationale",
  "accent_hex": "#HEX_CODE",
  "accent_reasoning": "Brief 1-sentence design rationale",
  "palette_summary": "1-2 sentence overview of the brand palette harmony and mood"
}}
"""

    try:
        client = OpenAI(api_key=api_key, timeout=12.0)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional brand color specialist. You always respond in strict, valid JSON."
                },
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        result = json.loads(content)

        p_hex = result.get("primary_hex", "").upper()
        s_hex = result.get("secondary_hex", "").upper()
        a_hex = result.get("accent_hex", "").upper()

        # Validate that selected hexes exist in candidates list
        if p_hex in candidates_by_hex and s_hex in candidates_by_hex and a_hex in candidates_by_hex:
            primary = dict(candidates_by_hex[p_hex])
            secondary = dict(candidates_by_hex[s_hex])
            accent = dict(candidates_by_hex[a_hex])

            primary["reasoning"] = result.get("primary_reasoning", "Primary brand identity anchor.")
            secondary["reasoning"] = result.get("secondary_reasoning", "Supporting harmonic brand color.")
            accent["reasoning"] = result.get("accent_reasoning", "Distinctive accent for emphasis.")
            summary = result.get("palette_summary", "Curated brand color palette.")

            return primary, secondary, accent, summary, "openai"
        else:
            logger.warning("OpenAI returned a color not strictly in candidate list. Falling back to heuristic.")
            p, s, a, summary = select_colors_with_heuristics(candidates)
            return p, s, a, summary, "heuristic_fallback"

    except (OpenAIError, json.JSONDecodeError, Exception) as err:
        logger.error(f"OpenAI LLM selection error: {err}. Falling back to color-theory heuristic.")
        p, s, a, summary = select_colors_with_heuristics(candidates)
        return p, s, a, summary, "heuristic_fallback"


def build_color_item(cand: Dict[str, Any], role: str, fallback_reason: str) -> ColorItem:
    """Helper to build a fully typed ColorItem schema from candidate dict."""
    r, g, b = cand["rgb_values"]["r"], cand["rgb_values"]["g"], cand["rgb_values"]["b"]
    h, s, l = cand["hsl_values"]["h"], cand["hsl_values"]["s"], cand["hsl_values"]["l"]
    acc_data = cand["accessibility"]

    return ColorItem(
        name=cand["name"],
        hex=cand["hex"],
        rgb=cand["rgb"],
        hsl=cand["hsl"],
        rgb_values=RGBValues(r=r, g=g, b=b),
        hsl_values=HSLValues(h=h, s=s, l=l),
        percentage=cand.get("percentage", 0.0),
        accessibility=ColorAccessibility(
            luminance=acc_data["luminance"],
            contrast_with_white=acc_data["contrast_with_white"],
            contrast_with_black=acc_data["contrast_with_black"],
            preferred_text_color=acc_data["preferred_text_color"],
            is_dark=acc_data["is_dark"],
        ),
        role=role,
        reasoning=cand.get("reasoning", fallback_reason),
    )
