"""Integration tests for the v2 API endpoints."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

from app.main import app
from app.services.smoldocling_service import (
    SmolDoclingConversionError,
    SmolDoclingService,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_path():
    """Create a sample PDF file for testing."""
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        pdf_path = temp_file.name

    canvas = Canvas(pdf_path, pagesize=LETTER)
    canvas.drawString(1 * inch, 10 * inch, "Hello, this is a test PDF!")
    canvas.save()

    yield pdf_path

    # Clean up
    if os.path.exists(pdf_path):
        os.unlink(pdf_path)


@pytest.fixture(scope="module")
def smoldocling_available():
    """Check if SmolDocling service is available."""
    try:
        # Try to initialize the service
        service = SmolDoclingService()
        # If we get here, the service is available
        return True
    except Exception:
        # If initialization fails, the service is not available
        return False


def test_convert_pdf_endpoint_v2(client, sample_pdf_path, smoldocling_available):
    """Test the v2 PDF conversion endpoint."""
    # Skip if SmolDocling is not available
    if not smoldocling_available:
        pytest.skip("SmolDocling service is not available")

    # Open the sample PDF file
    with open(sample_pdf_path, "rb") as pdf_file:
        # Create a multipart form with the PDF file
        files = {"file": ("test.pdf", pdf_file, "application/pdf")}

        # Make a POST request to the v2 conversion endpoint
        response = client.post("/api/v2/pdf/convert", files=files)

        # Check the response
        assert response.status_code == 200
        assert "text" in response.json()
        assert "filename" in response.json()
        assert response.json()["filename"] == "test.pdf"
        # We can't assert the exact text since it depends on the model
        assert isinstance(response.json()["text"], str)
        assert "ocr_used" in response.json()


def test_convert_pdf_invalid_file_type_v2(client):
    """Test the v2 PDF conversion endpoint with an invalid file type."""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_file.write(b"This is not a PDF file")
        txt_path = temp_file.name

    try:
        # Open the text file
        with open(txt_path, "rb") as txt_file:
            # Create a multipart form with the text file
            files = {"file": ("test.txt", txt_file, "text/plain")}

            # Make a POST request to the v2 conversion endpoint
            response = client.post("/api/v2/pdf/convert", files=files)

            # Check the response
            assert response.status_code == 415
            assert "detail" in response.json()
            assert "Unsupported file type" in response.json()["detail"]
    finally:
        # Clean up
        if os.path.exists(txt_path):
            os.unlink(txt_path)


def test_convert_pdf_file_too_large_v2(client, sample_pdf_path, monkeypatch):
    """Test the v2 PDF conversion endpoint with a file that's too large."""
    # Temporarily set the max upload size to a small value
    from app.core.config import settings

    original_max_size = settings.MAX_UPLOAD_SIZE
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 10)  # 10 bytes

    try:
        # Open the sample PDF file
        with open(sample_pdf_path, "rb") as pdf_file:
            # Create a multipart form with the PDF file
            files = {"file": ("test.pdf", pdf_file, "application/pdf")}

            # Make a POST request to the v2 conversion endpoint
            response = client.post("/api/v2/pdf/convert", files=files)

            # Check the response
            assert response.status_code == 400
            assert "detail" in response.json()
            assert "File size exceeds maximum allowed size" in response.json()["detail"]
    finally:
        # Restore the original max upload size
        monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", original_max_size)


def test_convert_pdf_service_error_v2(
    client, sample_pdf_path, smoldocling_available, monkeypatch
):
    """Test the v2 PDF conversion endpoint when the service raises an error."""
    # Skip if SmolDocling is not available
    if not smoldocling_available:
        pytest.skip("SmolDocling service is not available")

    # Create a corrupted PDF file that will cause an error
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"This is not a valid PDF file")
        corrupted_path = temp_file.name

    try:
        # Open the corrupted PDF file
        with open(corrupted_path, "rb") as pdf_file:
            # Create a multipart form with the PDF file
            files = {"file": ("test.pdf", pdf_file, "application/pdf")}

            # Make a POST request to the v2 conversion endpoint
            response = client.post("/api/v2/pdf/convert", files=files)

            # Check the response
            assert response.status_code == 500
            assert "detail" in response.json()
    finally:
        # Clean up
        if os.path.exists(corrupted_path):
            os.unlink(corrupted_path)
