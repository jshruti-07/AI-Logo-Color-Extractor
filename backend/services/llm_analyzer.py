import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI, OpenAIError

from utils.color_utils import rgb_to_hsl, hex_to_rgb, color_distance

logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    """Raised when the OpenAI API key is missing or invalid."""
    pass


class LLMAnalysisError(Exception):
    """Raised when LLM analysis fails and cannot be recovered."""
    pass


class LLMAnalyzer:
    """Classifies extracted candidate colors into Primary, Secondary, and Accent brand colors."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "").strip()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.client: Optional[OpenAI] = None

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def is_configured(self) -> bool:
        """Check if OpenAI API key is set."""
        return bool(self.api_key and self.client)

    def select_brand_colors(
        self,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Sends candidates to OpenAI LLM for intelligent brand classification.
        Validates that all selected HEX values belong strictly to candidates.
        """
        if not candidates:
            raise LLMAnalysisError("No candidate colors available for classification.")

        if not self.is_configured():
            raise LLMConfigurationError(
                "OpenAI API key is not configured. Please add OPENAI_API_KEY to backend/.env."
            )

        # Prepare candidate payload for the LLM
        candidate_summary = [
            {
                "hex": c["hex"].upper(),
                "percentage": c.get("percentage", 0.0),
                "importance": c.get("relative_importance", c.get("percentage", 0.0)),
            }
            for c in candidates
        ]

        valid_hex_set = {c["hex"].upper() for c in candidates}

        system_prompt = (
            "You are a professional brand color analyst. "
            "You are given a list of colors extracted directly from a logo image. "
            "Your task is to select exactly three colors:\n"
            "- Primary: The strongest color representing the visual identity of the logo.\n"
            "- Secondary: A supporting color that complements the primary color.\n"
            "- Accent: A visually distinctive color useful for emphasis.\n\n"
            "CRITICAL RULES:\n"
            "1. ONLY select colors from the supplied candidate list.\n"
            "2. NEVER invent or modify a HEX value.\n"
            "3. Return valid JSON only with exact schema:\n"
            "{\n"
            '  "primary": {"hex": "#HEX", "reason": "short explanation"},\n'
            '  "secondary": {"hex": "#HEX", "reason": "short explanation"},\n'
            '  "accent": {"hex": "#HEX", "reason": "short explanation"}\n'
            "}"
        )

        user_content = f"Extracted Candidate Colors:\n{json.dumps(candidate_summary, indent=2)}"

        # Attempt call (with 1 retry on invalid hex response)
        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.2,
                )

                raw_json = response.choices[0].message.content
                parsed = json.loads(raw_json)

                # Validate structure
                if not all(k in parsed for k in ("primary", "secondary", "accent")):
                    raise ValueError("Missing one or more required keys (primary, secondary, accent)")

                primary_hex = parsed["primary"]["hex"].strip().upper()
                secondary_hex = parsed["secondary"]["hex"].strip().upper()
                accent_hex = parsed["accent"]["hex"].strip().upper()

                # Validate hex values exist in candidate list
                if (
                    primary_hex in valid_hex_set and
                    secondary_hex in valid_hex_set and
                    accent_hex in valid_hex_set
                ):
                    return {
                        "primary": {
                            "hex": primary_hex,
                            "reason": parsed["primary"].get("reason", "Dominant brand identity color")
                        },
                        "secondary": {
                            "hex": secondary_hex,
                            "reason": parsed["secondary"].get("reason", "Supporting brand color")
                        },
                        "accent": {
                            "hex": accent_hex,
                            "reason": parsed["accent"].get("reason", "Visual accent color")
                        }
                    }
                else:
                    logger.warning(
                        f"LLM returned HEX not in candidates (attempt {attempt+1}): "
                        f"{primary_hex}, {secondary_hex}, {accent_hex}"
                    )
                    user_content += (
                        "\n\nERROR: One or more returned HEX colors was NOT in the candidate list! "
                        f"You MUST choose exclusively from: {list(valid_hex_set)}"
                    )

            except OpenAIError as oe:
                logger.warning(f"OpenAI API Error ({oe.code if hasattr(oe, 'code') else type(oe)}): {oe}. Falling back to deterministic brand selection.")
                return self.deterministic_brand_selection(candidates)
            except Exception as e:
                logger.error(f"Error parsing LLM response (attempt {attempt+1}): {e}")
                if attempt == 1:
                    break

        # Fallback to deterministic selection if LLM returned non-existent colors
        logger.info("Using deterministic brand color selection fallback.")
        return self.deterministic_brand_selection(candidates)

    @staticmethod
    def deterministic_brand_selection(candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """
        Intelligent deterministic brand color selection based on color theory and frequency
        used if LLM is unavailable or for testing.
        """
        if not candidates:
            raise LLMAnalysisError("No candidate colors available.")

        # If 1 or 2 candidates, handle gracefully
        if len(candidates) == 1:
            h = candidates[0]["hex"].upper()
            return {
                "primary": {"hex": h, "reason": "Dominant logo color"},
                "secondary": {"hex": h, "reason": "Monochromatic secondary"},
                "accent": {"hex": h, "reason": "Monochromatic accent"}
            }
        if len(candidates) == 2:
            h1 = candidates[0]["hex"].upper()
            h2 = candidates[1]["hex"].upper()
            return {
                "primary": {"hex": h1, "reason": "Dominant logo color"},
                "secondary": {"hex": h2, "reason": "Supporting brand color"},
                "accent": {"hex": h1, "reason": "Accent brand color"}
            }

        # Calculate saturation and luminance for each candidate
        enriched = []
        for c in candidates:
            rgb = hex_to_rgb(c["hex"])
            h, s, l = rgb_to_hsl(*rgb)
            enriched.append({
                "hex": c["hex"].upper(),
                "rgb": rgb,
                "percentage": c.get("percentage", 0.0),
                "h": h,
                "s": s,
                "l": l,
                # Chromatic score: saturated colors represent brand identity better than pure neutrals
                "chroma": s * (1.0 - abs(l - 50) / 50.0)
            })

        # Primary: highest frequency, with preference for chromatic identity unless mostly monochrome
        sorted_by_freq = sorted(enriched, key=lambda x: x["percentage"], reverse=True)
        primary = sorted_by_freq[0]

        # If top color is pure white or black and there is a vibrant color with significant percentage (>8%),
        # favor the vibrant color as the primary brand identity
        if (primary["l"] > 90 or primary["l"] < 10) and len(sorted_by_freq) > 1:
            for cand in sorted_by_freq[1:]:
                if cand["chroma"] > 30 and cand["percentage"] >= 8.0:
                    primary = cand
                    break

        # Secondary: color complementing or supporting primary (often neutral or next prominent)
        remaining = [c for c in enriched if c["hex"] != primary["hex"]]
        # Prefer highest remaining frequency that has noticeable distance
        remaining_sorted = sorted(remaining, key=lambda x: x["percentage"], reverse=True)
        secondary = remaining_sorted[0]

        # Accent: color with highest perceptual distance / contrast or most vibrant
        remaining_for_accent = [c for c in remaining if c["hex"] != secondary["hex"]]
        if remaining_for_accent:
            # Score by combination of chroma and distance from primary
            def accent_score(c):
                dist = color_distance(c["rgb"], primary["rgb"])
                return dist + (c["chroma"] * 0.8)

            accent = max(remaining_for_accent, key=accent_score)
        else:
            accent = secondary

        return {
            "primary": {"hex": primary["hex"], "reason": "Primary brand identity color"},
            "secondary": {"hex": secondary["hex"], "reason": "Supporting brand color"},
            "accent": {"hex": accent["hex"], "reason": "High-contrast visual accent"}
        }
