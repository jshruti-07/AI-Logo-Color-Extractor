"""FastAPI application for AI Logo Color Extractor."""

import logging
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .schemas.palette import (
    ExtractedPaletteResponse,
    CandidateColor,
    HealthResponse,
    ErrorResponse,
)
from .services.image_processor import validate_and_preprocess_image
from .services.color_extractor import extract_candidate_colors
from .services.llm_selector import select_colors_with_llm, build_color_item

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_color_extractor.api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Full-stack AI Logo Color Extractor API with Pillow/K-Means and OpenAI semantic color selection.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local Angular dev server and custom origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint to verify backend status and OpenAI key configuration."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        openai_configured=bool(settings.OPENAI_API_KEY.strip()),
        max_file_size_mb=settings.MAX_FILE_SIZE_MB,
    )


@app.post(
    "/api/analyze-logo",
    response_model=ExtractedPaletteResponse,
    status_code=status.HTTP_200_OK,
    tags=["Color Extraction"],
    summary="Extracts dominant brand colors and selects Primary, Secondary, and Accent roles via AI."
)
async def analyze_logo(file: UploadFile = File(..., description="Uploaded JPG, PNG, or WEBP logo image")):
    """
    Main Logo Analysis Workflow:
    1. Validate image format, integrity, and file size.
    2. Handle transparent PNG backgrounds (filter out alpha < threshold).
    3. Preprocess and downsample image for color clustering.
    4. Extract 10-20 distinct candidate colors via MiniBatchKMeans.
    5. Pass candidate colors to OpenAI LLM (or intelligent heuristic fallback) to select:
       - Primary: Strongest brand identity anchor.
       - Secondary: Supporting color that works harmoniously with Primary.
       - Accent: Visually distinctive color for emphasis and CTAs.
    6. Return structured JSON with Primary, Secondary, Accent, Candidate Spectrum, and Accessibility data.
    """
    filename = file.filename or "unknown.png"
    logger.info(f"Received logo upload: '{filename}' (content_type={file.content_type})")

    # Read uploaded file bytes
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file stream."
        )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # 1. Validate & preprocess image
    pixels, metadata = validate_and_preprocess_image(contents, filename)
    logger.info(f"Preprocessed '{filename}': {len(pixels)} valid foreground pixels extracted (transparency filtered: {metadata.filtered_transparent_percentage}%).")

    # 2. Extract 10-20 candidate colors via clustering
    raw_candidates = extract_candidate_colors(pixels)
    if not raw_candidates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No distinct colors could be extracted from the provided logo."
        )

    logger.info(f"Extracted {len(raw_candidates)} candidate color clusters from '{filename}'.")

    # 3. LLM semantic color role selection (Primary, Secondary, Accent)
    primary_cand, secondary_cand, accent_cand, ai_summary, source = select_colors_with_llm(raw_candidates)

    # 4. Mark candidate colors with their selected roles
    structured_candidates: List[CandidateColor] = []
    for c in raw_candidates:
        role = None
        if c["hex"] == primary_cand["hex"]:
            role = "primary"
        elif c["hex"] == secondary_cand["hex"]:
            role = "secondary"
        elif c["hex"] == accent_cand["hex"]:
            role = "accent"

        structured_candidates.append(CandidateColor(
            id=c["id"],
            hex=c["hex"],
            name=c["name"],
            rgb=c["rgb"],
            hsl=c["hsl"],
            percentage=c["percentage"],
            is_selected_role=role,
        ))

    # 5. Build final typed response
    primary_item = build_color_item(primary_cand, "primary", "Anchor brand identity color.")
    secondary_item = build_color_item(secondary_cand, "secondary", "Supporting harmonic brand color.")
    accent_item = build_color_item(accent_cand, "accent", "Eye-catching accent color.")

    response = ExtractedPaletteResponse(
        primary=primary_item,
        secondary=secondary_item,
        accent=accent_item,
        candidates=structured_candidates,
        total_candidates=len(structured_candidates),
        ai_selection_source=source,
        ai_summary=ai_summary,
        image_metadata=metadata,
    )

    logger.info(f"Completed analysis for '{filename}'. Primary={primary_item.hex}, Secondary={secondary_item.hex}, Accent={accent_item.hex} (Source={source}).")
    return response


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc: HTTPException):
    """Custom JSON error handler for standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "RequestError",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Catch-all error handler for unexpected server errors."""
    logger.exception(f"Unhandled server exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the logo. Please try again or check backend logs.",
            "status_code": 500
        }
    )
