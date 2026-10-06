"""Image validation, preprocessing, and transparency handling."""

import io
from typing import Tuple, Dict, Any
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException, status
from ..config import settings
from ..schemas.palette import ImageMetadata


def validate_and_preprocess_image(
    image_bytes: bytes,
    filename: str
) -> Tuple[np.ndarray, ImageMetadata]:
    """
    Validates uploaded image and extracts non-transparent foreground RGB pixels.

    Args:
        image_bytes: Raw bytes from uploaded file.
        filename: Original file name.

    Returns:
        Tuple of:
          - np.ndarray: Shape (N, 3) of RGB pixels from valid foreground.
          - ImageMetadata: Extracted metadata including transparency info.

    Raises:
        HTTPException: For invalid files, unsupported formats, or empty images.
    """
    # 1. Check size limit
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the {settings.MAX_FILE_SIZE_MB}MB maximum limit."
        )

    # 2. Check extension
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Supported formats: {', '.join(settings.allowed_extensions_list).upper()}."
        )

    # 3. Load with Pillow & verify integrity
    try:
        img_buffer = io.BytesIO(image_bytes)
        img = Image.open(img_buffer)
        img.verify()  # Verify integrity of header and structure
        
        # Re-open after verify() because verify() can corrupt internal state
        img_buffer.seek(0)
        img = Image.open(img_buffer)
        
        # Apply EXIF rotation if present (especially for smartphone photos)
        img = ImageOps.exif_transpose(img)
    except (UnidentifiedImageError, OSError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The uploaded file is not a valid or readable image. Error: {str(exc)}"
        )

    orig_width, orig_height = img.size
    img_format = (img.format or ext).upper()
    has_alpha = img.mode in ("RGBA", "LA", "PA") or ("transparency" in img.info)

    # 4. Downsample if image is very large for optimal performance
    max_dim = settings.IMAGE_RESIZE_MAX_DIM
    if orig_width > max_dim or orig_height > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # 5. Extract pixels and handle alpha transparency correctly
    if has_alpha:
        img_rgba = img.convert("RGBA")
        np_img = np.array(img_rgba)
        
        # Shape: (H, W, 4)
        rgb_channels = np_img[:, :, :3]
        alpha_channel = np_img[:, :, 3]
        
        total_pixels = alpha_channel.size
        # Filter mask: keep pixels where alpha >= threshold
        mask = alpha_channel >= settings.ALPHA_TRANSPARENCY_THRESHOLD
        transparent_pixels = total_pixels - np.count_nonzero(mask)
        filtered_percentage = round((transparent_pixels / total_pixels) * 100, 2)
        
        valid_pixels = rgb_channels[mask]
    else:
        img_rgb = img.convert("RGB")
        np_img = np.array(img_rgb)
        # Flatten (H, W, 3) to (N, 3)
        valid_pixels = np_img.reshape(-1, 3)
        total_pixels = len(valid_pixels)
        filtered_percentage = 0.0

    if len(valid_pixels) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No sufficient foreground pixels detected. The image might be completely transparent or empty."
        )

    metadata = ImageMetadata(
        filename=filename,
        format=img_format,
        width=orig_width,
        height=orig_height,
        has_alpha=has_alpha,
        filtered_transparent_percentage=filtered_percentage,
        total_pixels_analyzed=len(valid_pixels),
    )

    return valid_pixels, metadata
