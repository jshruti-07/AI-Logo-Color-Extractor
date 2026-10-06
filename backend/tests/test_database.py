import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.palette import PaletteRecord
from services.palette_repository import PaletteRepository


@pytest.fixture
def db_session():
    """Provides a fresh SQLite in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_save_and_retrieve_palette(db_session):
    colors = {
        "primary": {
            "name": "Royal Blue",
            "hex": "#2563EB",
            "rgb": "37, 99, 235",
            "hsl": "221°, 83%, 53%",
            "reason": "Dominant brand color",
            "luminance": 0.18,
            "text_color": "#FFFFFF",
        },
        "secondary": {
            "name": "Pure White",
            "hex": "#FFFFFF",
            "rgb": "255, 255, 255",
            "hsl": "0°, 0%, 100%",
            "reason": "Clean background accent",
            "luminance": 1.0,
            "text_color": "#0F172A",
        },
        "accent": {
            "name": "Amber",
            "hex": "#F59E0B",
            "rgb": "245, 158, 11",
            "hsl": "38°, 92%, 50%",
            "reason": "Highlight color",
            "luminance": 0.44,
            "text_color": "#FFFFFF",
        },
    }
    candidates = [{"hex": "#2563EB", "percentage": 70.0}, {"hex": "#FFFFFF", "percentage": 30.0}]

    # Save
    record = PaletteRepository.save_palette(
        db=db_session,
        filename="test_logo.png",
        dimensions=(512, 512),
        candidate_count=2,
        colors=colors,
        candidates=candidates,
    )
    assert record is not None
    assert record.id is not None
    assert record.filename == "test_logo.png"

    # List
    history = PaletteRepository.list_palettes(db=db_session)
    assert len(history) == 1
    assert history[0]["id"] == record.id
    assert history[0]["filename"] == "test_logo.png"
    assert history[0]["primary"]["hex"] == "#2563EB"

    # Get by ID
    retrieved = PaletteRepository.get_palette_by_id(db=db_session, palette_id=record.id)
    assert retrieved is not None
    assert retrieved["colors"]["primary"]["name"] == "Royal Blue"
    assert retrieved["meta"]["dimensions"]["width"] == 512

    # Delete
    deleted = PaletteRepository.delete_palette_by_id(db=db_session, palette_id=record.id)
    assert deleted is True

    # Confirm deletion
    assert PaletteRepository.get_palette_by_id(db=db_session, palette_id=record.id) is None
    assert len(PaletteRepository.list_palettes(db=db_session)) == 0
