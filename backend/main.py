import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Load environment variables from .env
load_dotenv()

from database import init_db, get_db, check_db_status
from services.image_processor import ImageProcessor, ImageValidationError
from services.color_extractor import ColorExtractor
from services.color_converter import ColorConverter
from services.llm_analyzer import LLMAnalyzer, LLMConfigurationError, LLMAnalysisError
from services.palette_repository import PaletteRepository

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_logo_color_extractor")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    logger.info("Starting AI Logo Color Extractor backend...")
    init_db()
    yield
    logger.info("Shutting down AI Logo Color Extractor backend...")


app = FastAPI(
    title="AI Logo Color Extractor API",
    version="1.0.0",
    description="Extracts candidate colors and uses OpenAI to classify Primary, Secondary, and Accent brand colors with MySQL persistence.",
    lifespan=lifespan
)

# CORS setup for Angular development server
CORS_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service instances
image_processor = ImageProcessor()
color_extractor = ColorExtractor(n_clusters=16)
llm_analyzer = LLMAnalyzer()


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint, OpenAI LLM configuration status, and MySQL database connection status."""
    load_dotenv(override=True)
    current_llm = LLMAnalyzer()
    db_status = check_db_status()
    return {
        "status": "healthy",
        "llm_configured": current_llm.is_configured(),
        "model": current_llm.model if current_llm.is_configured() else None,
        "database": db_status,
    }


@app.post("/api/analyze-logo")
async def analyze_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    Analyze uploaded logo image (JPG/PNG):
    1. Validate and preprocess image (including transparency filtering).
    2. Extract candidate colors using K-Means clustering.
    3. Filter near-duplicate colors via perceptual LAB Delta E.
    4. Send candidates to OpenAI LLM to classify Primary, Secondary, Accent.
    5. Convert and return HEX, RGB, HSL, Color Name, and contrast styling.
    6. Persist extraction and classification results into MySQL database.
    """
    load_dotenv(override=True)
    try:
        # Read file contents into memory
        file_bytes = await file.read()
        filename = file.filename or "unknown.png"
        content_type = file.content_type or ""

        # Step 1: Preprocess and extract visible pixels
        logger.info(f"Processing uploaded file: {filename} ({len(file_bytes)} bytes)")
        pixels, dimensions = image_processor.load_and_preprocess(
            file_bytes, filename=filename, content_type=content_type
        )

        # Step 2 & 3: Color Extraction and deduplication
        logger.info(f"Extracting colors from {len(pixels)} visible pixels...")
        candidates = color_extractor.extract_candidate_colors(pixels)
        if not candidates:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "code": "COLOR_EXTRACTION_FAILED",
                        "message": "Unable to extract meaningful colors from this logo."
                    }
                }
            )

        logger.info(f"Extracted {len(candidates)} distinct candidate colors.")

        # Step 4: AI Classification via OpenAI LLM
        # Ensure fresh LLMAnalyzer instance in case .env was updated
        current_llm = LLMAnalyzer()
        if not current_llm.is_configured():
            logger.warning("OpenAI API key is missing.")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "code": "OPENAI_KEY_MISSING",
                        "message": "OpenAI API key is not configured. Please add OPENAI_API_KEY to backend/.env to enable AI color classification."
                    }
                }
            )

        selected_roles = current_llm.select_brand_colors(candidates)

        # Step 5: Convert selected colors to complete palette specification
        primary_data = ColorConverter.convert_color(
            selected_roles["primary"]["hex"],
            reason=selected_roles["primary"]["reason"]
        )
        secondary_data = ColorConverter.convert_color(
            selected_roles["secondary"]["hex"],
            reason=selected_roles["secondary"]["reason"]
        )
        accent_data = ColorConverter.convert_color(
            selected_roles["accent"]["hex"],
            reason=selected_roles["accent"]["reason"]
        )

        candidate_preview = [
            {"hex": c["hex"], "percentage": c["percentage"]}
            for c in candidates[:8]
        ]

        # Step 6: Persist analysis into MySQL database
        saved_record = PaletteRepository.save_palette(
            db=db,
            filename=filename,
            dimensions=dimensions,
            candidate_count=len(candidates),
            colors={
                "primary": primary_data,
                "secondary": secondary_data,
                "accent": accent_data,
            },
            candidates=candidate_preview,
        )
        record_id = saved_record.id if saved_record else None

        response_payload = {
            "success": True,
            "id": record_id,
            "colors": {
                "primary": primary_data,
                "secondary": secondary_data,
                "accent": accent_data
            },
            "meta": {
                "dimensions": {"width": dimensions[0], "height": dimensions[1]},
                "candidate_count": len(candidates),
                "candidates": candidate_preview
            }
        }
        return JSONResponse(status_code=200, content=response_payload)

    except ImageValidationError as ive:
        logger.warning(f"Image validation error: {ive.message}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": ive.code,
                    "message": ive.message
                }
            }
        )
    except LLMConfigurationError as lce:
        logger.warning(f"LLM configuration error: {lce}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "OPENAI_KEY_MISSING",
                    "message": str(lce)
                }
            }
        )
    except LLMAnalysisError as lae:
        logger.error(f"LLM analysis error: {lae}")
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": {
                    "code": "LLM_ANALYSIS_FAILED",
                    "message": f"AI brand analysis failed: {str(lae)}"
                }
            }
        )
    except Exception as e:
        logger.exception(f"Unexpected server error during logo analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while processing the logo. Please try again."
                }
            }
        )


@app.get("/api/history")
def get_palette_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Retrieve list of saved color extraction records from MySQL."""
    items = PaletteRepository.list_palettes(db=db, limit=limit, offset=offset)
    return JSONResponse(status_code=200, content={"success": True, "history": items})


@app.get("/api/history/{palette_id}")
def get_palette_by_id(
    palette_id: int,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Retrieve full details of a previously analyzed logo palette."""
    palette = PaletteRepository.get_palette_by_id(db=db, palette_id=palette_id)
    if not palette:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Palette with ID {palette_id} not found."}
            }
        )
    return JSONResponse(status_code=200, content={"success": True, **palette})


@app.delete("/api/history/{palette_id}")
def delete_palette_by_id(
    palette_id: int,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Delete a saved palette from MySQL history."""
    deleted = PaletteRepository.delete_palette_by_id(db=db, palette_id=palette_id)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Palette with ID {palette_id} not found or could not be deleted."}
            }
        )
    return JSONResponse(status_code=200, content={"success": True, "message": f"Palette {palette_id} deleted."})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
