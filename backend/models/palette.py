import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from database import Base


class PaletteRecord(Base):
    """
    MySQL database model storing extracted brand color palettes and logo metadata.
    """
    __tablename__ = "palettes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False, index=True)
    dimensions_width = Column(Integer, nullable=True)
    dimensions_height = Column(Integer, nullable=True)
    candidate_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Primary brand color
    primary_name = Column(String(100), nullable=False)
    primary_hex = Column(String(10), nullable=False)
    primary_rgb = Column(String(50), nullable=False)
    primary_hsl = Column(String(50), nullable=False)
    primary_reason = Column(Text, nullable=True)
    primary_luminance = Column(Float, nullable=True)
    primary_text_color = Column(String(10), nullable=True)

    # Secondary brand color
    secondary_name = Column(String(100), nullable=False)
    secondary_hex = Column(String(10), nullable=False)
    secondary_rgb = Column(String(50), nullable=False)
    secondary_hsl = Column(String(50), nullable=False)
    secondary_reason = Column(Text, nullable=True)
    secondary_luminance = Column(Float, nullable=True)
    secondary_text_color = Column(String(10), nullable=True)

    # Accent brand color
    accent_name = Column(String(100), nullable=False)
    accent_hex = Column(String(10), nullable=False)
    accent_rgb = Column(String(50), nullable=False)
    accent_hsl = Column(String(50), nullable=False)
    accent_reason = Column(Text, nullable=True)
    accent_luminance = Column(Float, nullable=True)
    accent_text_color = Column(String(10), nullable=True)

    # Serialized candidate list and extra metadata
    candidates_json = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record into the standard API response structure."""
        candidates = []
        if self.candidates_json:
            try:
                candidates = json.loads(self.candidates_json)
            except Exception:
                candidates = []

        return {
            "id": self.id,
            "filename": self.filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "colors": {
                "primary": {
                    "name": self.primary_name,
                    "hex": self.primary_hex,
                    "rgb": self.primary_rgb,
                    "hsl": self.primary_hsl,
                    "reason": self.primary_reason,
                    "luminance": self.primary_luminance,
                    "text_color": self.primary_text_color,
                },
                "secondary": {
                    "name": self.secondary_name,
                    "hex": self.secondary_hex,
                    "rgb": self.secondary_rgb,
                    "hsl": self.secondary_hsl,
                    "reason": self.secondary_reason,
                    "luminance": self.secondary_luminance,
                    "text_color": self.secondary_text_color,
                },
                "accent": {
                    "name": self.accent_name,
                    "hex": self.accent_hex,
                    "rgb": self.accent_rgb,
                    "hsl": self.accent_hsl,
                    "reason": self.accent_reason,
                    "luminance": self.accent_luminance,
                    "text_color": self.accent_text_color,
                },
            },
            "meta": {
                "dimensions": {
                    "width": self.dimensions_width or 0,
                    "height": self.dimensions_height or 0,
                },
                "candidate_count": self.candidate_count or 0,
                "candidates": candidates,
            },
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns a lightweight summary for history listings."""
        return {
            "id": self.id,
            "filename": self.filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "primary": {"name": self.primary_name, "hex": self.primary_hex},
            "secondary": {"name": self.secondary_name, "hex": self.secondary_hex},
            "accent": {"name": self.accent_name, "hex": self.accent_hex},
        }
