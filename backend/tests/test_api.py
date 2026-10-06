import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from main import app
from services.llm_analyzer import LLMAnalyzer, LLMConfigurationError

client = TestClient(app)


def create_sample_png_bytes():
    img = Image.new("RGB", (64, 64), color=(37, 99, 235))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_configured" in data


def test_api_invalid_file_type():
    files = {"file": ("test.txt", b"plain text content", "text/plain")}
    response = client.post("/api/analyze-logo", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "INVALID_EXTENSION"
    assert "Please upload a valid JPG or PNG logo" in data["error"]["message"]


def test_api_corrupt_file():
    files = {"file": ("corrupt.png", b"corrupted png bytes here", "image/png")}
    response = client.post("/api/analyze-logo", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] in ("CORRUPT_IMAGE", "IMAGE_READ_ERROR")


def test_llm_analyzer_unconfigured_raises_clear_error():
    analyzer = LLMAnalyzer(api_key="")
    candidates = [{"hex": "#2563EB", "percentage": 80.0}, {"hex": "#FFFFFF", "percentage": 20.0}]
    with pytest.raises(LLMConfigurationError) as exc_info:
        analyzer.select_brand_colors(candidates)
    assert "OpenAI API key is not configured" in str(exc_info.value)


def test_deterministic_brand_selection_roles():
    candidates = [
        {"hex": "#2563EB", "percentage": 60.0},
        {"hex": "#FFFFFF", "percentage": 25.0},
        {"hex": "#F59E0B", "percentage": 15.0},
    ]
    roles = LLMAnalyzer.deterministic_brand_selection(candidates)
    assert "primary" in roles
    assert "secondary" in roles
    assert "accent" in roles

    # Roles must only use candidate hex values
    valid_hexes = {"#2563EB", "#FFFFFF", "#F59E0B"}
    assert roles["primary"]["hex"] in valid_hexes
    assert roles["secondary"]["hex"] in valid_hexes
    assert roles["accent"]["hex"] in valid_hexes
