import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.palette import PaletteRecord

logger = logging.getLogger(__name__)


class PaletteRepository:
    """Repository handling MySQL database operations for color palettes."""

    @staticmethod
    def save_palette(
        db: Session,
        filename: str,
        dimensions: Tuple[int, int],
        candidate_count: int,
        colors: Dict[str, Dict[str, Any]],
        candidates: List[Dict[str, Any]],
    ) -> Optional[PaletteRecord]:
        """
        Saves an extracted color palette analysis into the MySQL database.
        """
        try:
            record = PaletteRecord(
                filename=filename,
                dimensions_width=dimensions[0],
                dimensions_height=dimensions[1],
                candidate_count=candidate_count,
                # Primary color
                primary_name=colors["primary"]["name"],
                primary_hex=colors["primary"]["hex"],
                primary_rgb=colors["primary"]["rgb"],
                primary_hsl=colors["primary"]["hsl"],
                primary_reason=colors["primary"].get("reason"),
                primary_luminance=colors["primary"].get("luminance"),
                primary_text_color=colors["primary"].get("text_color"),
                # Secondary color
                secondary_name=colors["secondary"]["name"],
                secondary_hex=colors["secondary"]["hex"],
                secondary_rgb=colors["secondary"]["rgb"],
                secondary_hsl=colors["secondary"]["hsl"],
                secondary_reason=colors["secondary"].get("reason"),
                secondary_luminance=colors["secondary"].get("luminance"),
                secondary_text_color=colors["secondary"].get("text_color"),
                # Accent color
                accent_name=colors["accent"]["name"],
                accent_hex=colors["accent"]["hex"],
                accent_rgb=colors["accent"]["rgb"],
                accent_hsl=colors["accent"]["hsl"],
                accent_reason=colors["accent"].get("reason"),
                accent_luminance=colors["accent"].get("luminance"),
                accent_text_color=colors["accent"].get("text_color"),
                # Serialized candidate colors
                candidates_json=json.dumps(candidates),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info(f"Saved palette analysis to database with ID={record.id}")
            return record
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save palette to database: {e}")
            return None

    @staticmethod
    def list_palettes(
        db: Session,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a list of recent palette analyses ordered by creation date descending.
        """
        try:
            records = (
                db.query(PaletteRecord)
                .order_by(desc(PaletteRecord.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [record.to_summary_dict() for record in records]
        except Exception as e:
            logger.error(f"Failed to list palettes from database: {e}")
            return []

    @staticmethod
    def get_palette_by_id(
        db: Session,
        palette_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves full palette details by primary key ID.
        """
        try:
            record = db.query(PaletteRecord).filter(PaletteRecord.id == palette_id).first()
            if record:
                return record.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch palette ID={palette_id} from database: {e}")
            return None

    @staticmethod
    def delete_palette_by_id(
        db: Session,
        palette_id: int
    ) -> bool:
        """
        Deletes a palette record by ID.
        """
        try:
            record = db.query(PaletteRecord).filter(PaletteRecord.id == palette_id).first()
            if not record:
                return False
            db.delete(record)
            db.commit()
            logger.info(f"Deleted palette ID={palette_id} from database.")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete palette ID={palette_id} from database: {e}")
            return False
