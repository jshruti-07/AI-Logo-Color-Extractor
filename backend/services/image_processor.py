import io
import os
from typing import Tuple
import numpy as np
from PIL import Image, UnidentifiedImageError

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/x-png",
    "application/octet-stream",  # Sometimes sent by clients for binary blobs
}
MAX_PROCESSING_DIMENSION = 300


class ImageValidationError(Exception):
    """Raised when an uploaded file fails validation checks."""
    def __init__(self, message: str, code: str = "INVALID_IMAGE"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ImageProcessor:
    """Handles image validation, decoding, transparency handling, and pixel extraction."""

    @staticmethod
    def validate_file_metadata(filename: str, content_type: str, file_size: int) -> None:
        """Validate file size, extension, and MIME type."""
        if file_size > MAX_FILE_SIZE:
            raise ImageValidationError(
                f"File size exceeds 5MB limit. Uploaded size: {file_size / (1024 * 1024):.1f}MB.",
                code="FILE_TOO_LARGE"
            )

        if not filename:
            raise ImageValidationError("Please upload a valid JPG or PNG logo.", code="INVALID_FILENAME")

        _, ext = os.path.splitext(filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            raise ImageValidationError(
                "Please upload a valid JPG or PNG logo.",
                code="INVALID_EXTENSION"
            )

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ImageValidationError(
                "Please upload a valid JPG or PNG logo.",
                code="INVALID_MIME_TYPE"
            )

    @staticmethod
    def load_and_preprocess(file_bytes: bytes, filename: str = "", content_type: str = "") -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Validate, open, resize, and extract visible RGB pixels from image bytes.
        Returns:
            pixels: np.ndarray of shape (N, 3) in uint8 RGB format
            original_dimensions: (width, height) tuple
        """
        if not file_bytes:
            raise ImageValidationError("Please upload a valid JPG or PNG logo.", code="EMPTY_FILE")

        ImageProcessor.validate_file_metadata(filename, content_type, len(file_bytes))

        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Verify the image format
            if image.format not in ("JPEG", "PNG"):
                raise ImageValidationError(
                    "Please upload a valid JPG or PNG logo.",
                    code="UNSUPPORTED_FORMAT"
                )
            # Fully load image data to catch truncation or corruption
            image.load()
        except UnidentifiedImageError:
            raise ImageValidationError(
                "Unable to process this image. Please upload another logo.",
                code="CORRUPT_IMAGE"
            )
        except Exception as e:
            if isinstance(e, ImageValidationError):
                raise
            raise ImageValidationError(
                "Unable to process this image. Please upload another logo.",
                code="IMAGE_READ_ERROR"
            )

        orig_dimensions = (image.width, image.height)

        # Resize to reasonable processing size while preserving aspect ratio
        processed_image = image.copy()
        if max(processed_image.width, processed_image.height) > MAX_PROCESSING_DIMENSION:
            processed_image.thumbnail(
                (MAX_PROCESSING_DIMENSION, MAX_PROCESSING_DIMENSION),
                Image.Resampling.LANCZOS
            )

        # Handle transparency (RGBA, LA, or Palette images with transparency)
        if processed_image.mode in ("RGBA", "LA") or (
            processed_image.mode == "P" and "transparency" in processed_image.info
        ):
            rgba_image = processed_image.convert("RGBA")
            rgba_array = np.array(rgba_image)

            # Separate RGB and Alpha channels
            rgb_part = rgba_array[:, :, :3]
            alpha_part = rgba_array[:, :, 3]

            # Filter out transparent pixels (alpha < 32 out of 255)
            # This ensures transparent backgrounds are NOT counted as white or brand color
            visible_mask = alpha_part > 32
            visible_pixels = rgb_part[visible_mask]

        else:
            # JPG or opaque PNG
            rgb_image = processed_image.convert("RGB")
            rgb_array = np.array(rgb_image)
            visible_pixels = rgb_array.reshape(-1, 3)

        if len(visible_pixels) < 10:
            raise ImageValidationError(
                "No visible pixels found. Please upload a logo with visible graphic elements.",
                code="NO_VISIBLE_PIXELS"
            )

        return visible_pixels, orig_dimensions
