import io
import pytest
from PIL import Image
from services.image_processor import ImageProcessor, ImageValidationError


def create_test_image(format="PNG", mode="RGB", size=(100, 100), color=(255, 0, 0), transparent=False) -> bytes:
    """Helper to generate in-memory image bytes."""
    if transparent and mode == "RGBA":
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        # Draw a colored square in the center
        for x in range(30, 70):
            for y in range(30, 70):
                img.putpixel((x, y), (color[0], color[1], color[2], 255))
    else:
        img = Image.new(mode, size, color)

    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_valid_png_upload():
    png_bytes = create_test_image("PNG", "RGB", color=(37, 99, 235))
    pixels, dims = ImageProcessor.load_and_preprocess(png_bytes, "logo.png", "image/png")
    assert len(pixels) > 0
    assert dims == (100, 100)


def test_valid_jpg_upload():
    jpg_bytes = create_test_image("JPEG", "RGB", color=(245, 158, 11))
    pixels, dims = ImageProcessor.load_and_preprocess(jpg_bytes, "logo.jpg", "image/jpeg")
    assert len(pixels) > 0
    assert dims == (100, 100)


def test_invalid_file_type():
    with pytest.raises(ImageValidationError) as exc_info:
        ImageProcessor.load_and_preprocess(b"some content", "file.pdf", "application/pdf")
    assert exc_info.value.code == "INVALID_EXTENSION"


def test_corrupted_image():
    corrupted_bytes = b"\x89PNG\r\n\x1a\nCorruptedImageDataThatFailsParsing"
    with pytest.raises(ImageValidationError) as exc_info:
        ImageProcessor.load_and_preprocess(corrupted_bytes, "corrupt.png", "image/png")
    assert exc_info.value.code in ("CORRUPT_IMAGE", "IMAGE_READ_ERROR")


def test_transparent_png_filters_empty_pixels():
    # RGBA image with 40x40 visible pixels on a 100x100 transparent canvas
    rgba_bytes = create_test_image("PNG", "RGBA", size=(100, 100), color=(16, 185, 129), transparent=True)
    pixels, dims = ImageProcessor.load_and_preprocess(rgba_bytes, "transparent_logo.png", "image/png")
    # Only non-transparent pixels should be returned
    assert len(pixels) == 1600  # 40 x 40 = 1600 pixels
    # Verify pixels are emerald green (16, 185, 129), not black or white
    assert abs(pixels[0][0] - 16) <= 5
    assert abs(pixels[0][1] - 185) <= 5
    assert abs(pixels[0][2] - 129) <= 5


def test_transparent_png_all_transparent_fails():
    img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with pytest.raises(ImageValidationError) as exc_info:
        ImageProcessor.load_and_preprocess(buf.getvalue(), "empty.png", "image/png")
    assert exc_info.value.code == "NO_VISIBLE_PIXELS"


def test_file_too_large():
    fake_large_data = b"X" * (6 * 1024 * 1024)  # 6 MB
    with pytest.raises(ImageValidationError) as exc_info:
        ImageProcessor.load_and_preprocess(fake_large_data, "large.png", "image/png")
    assert exc_info.value.code == "FILE_TOO_LARGE"
