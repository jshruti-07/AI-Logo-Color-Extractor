"""Pydantic schemas for the AI Logo Color Extractor API."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RGBValues(BaseModel):
    r: int = Field(..., ge=0, le=255, description="Red component (0-255)")
    g: int = Field(..., ge=0, le=255, description="Green component (0-255)")
    b: int = Field(..., ge=0, le=255, description="Blue component (0-255)")


class HSLValues(BaseModel):
    h: int = Field(..., ge=0, le=360, description="Hue in degrees (0-360)")
    s: int = Field(..., ge=0, le=100, description="Saturation percentage (0-100)")
    l: int = Field(..., ge=0, le=100, description="Lightness percentage (0-100)")


class ColorAccessibility(BaseModel):
    luminance: float = Field(..., description="WCAG 2.1 relative luminance")
    contrast_with_white: float = Field(..., description="Contrast ratio against pure white")
    contrast_with_black: float = Field(..., description="Contrast ratio against pure black")
    preferred_text_color: str = Field(..., description="#FFFFFF or #000000 for accessible readability")
    is_dark: bool = Field(..., description="True if color is dark (light text recommended)")


class ColorItem(BaseModel):
    """Represents a finalized extracted color role (Primary, Secondary, or Accent)."""
    name: str = Field(..., description="Human-readable color name, e.g. 'Electric Indigo'")
    hex: str = Field(..., description="Uppercase HEX color code with hash, e.g. '#2563EB'")
    rgb: str = Field(..., description="Formatted RGB string, e.g. 'rgb(37, 99, 235)'")
    hsl: str = Field(..., description="Formatted HSL string, e.g. 'hsl(221, 83%, 53%)'")
    rgb_values: Optional[RGBValues] = None
    hsl_values: Optional[HSLValues] = None
    percentage: float = Field(default=0.0, description="Percentage share in logo colors")
    accessibility: Optional[ColorAccessibility] = None
    role: Optional[str] = Field(default=None, description="Role: 'primary', 'secondary', or 'accent'")
    reasoning: Optional[str] = Field(default=None, description="Explanation for why this color was assigned this role")


class CandidateColor(BaseModel):
    """Represents one of the 10-20 raw clustered candidate colors."""
    id: int = Field(..., description="Cluster identifier index")
    hex: str = Field(..., description="Uppercase HEX code")
    name: str = Field(..., description="Human-readable color name")
    rgb: str = Field(..., description="Formatted RGB string")
    hsl: str = Field(..., description="Formatted HSL string")
    percentage: float = Field(..., description="Percentage of valid logo pixels represented by this cluster")
    is_selected_role: Optional[str] = Field(default=None, description="'primary', 'secondary', 'accent' or None")


class ImageMetadata(BaseModel):
    """Metadata about the processed logo image."""
    filename: str
    format: str
    width: int
    height: int
    has_alpha: bool
    filtered_transparent_percentage: float
    total_pixels_analyzed: int


class ExtractedPaletteResponse(BaseModel):
    """Main response structure conforming to prompt specifications."""
    primary: ColorItem
    secondary: ColorItem
    accent: ColorItem
    candidates: List[CandidateColor] = Field(default_factory=list)
    total_candidates: int = Field(default=0)
    ai_selection_source: str = Field(default="openai", description="'openai' or 'heuristic_fallback'")
    ai_summary: Optional[str] = Field(default=None, description="Semantic description of the brand color palette")
    image_metadata: Optional[ImageMetadata] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    openai_configured: bool
    max_file_size_mb: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None
