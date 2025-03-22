"""Integration tests for the API endpoints."""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app


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

    # Create a simple PDF with text
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    page.insert_text("Hello, this is a test PDF!", x=50, y=100)

    with open(pdf_path, "wb") as output_file:
        writer.write(output_file)

    yield pdf_path

    # Clean up
    if os.path.exists(pdf_path):
        os.unlink(pdf_path)


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Welcome to the Document Converter API" in response.json()["message"]
    assert "version" in response.json()
    assert response.json()["version"] is not None


def test_convert_pdf_endpoint(client, sample_pdf_path):
    """Test the PDF conversion endpoint."""
    # Open the sample PDF file
    with open(sample_pdf_path, "rb") as pdf_file:
        # Create a multipart form with the PDF file
        files = {"file": ("test.pdf", pdf_file, "application/pdf")}

        # Make a POST request to the conversion endpoint
        response = client.post("/api/v1/pdf/convert", files=files)

        # Check the response
        assert response.status_code == 200
        assert "text" in response.json()
        assert "Hello, this is a test PDF!" in response.json()["text"]
        assert response.json()["filename"] == "test.pdf"


def test_convert_pdf_invalid_file_type(client):
    """Test the PDF conversion endpoint with an invalid file type."""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_file.write(b"This is not a PDF file")
        txt_path = temp_file.name

    try:
        # Open the text file
        with open(txt_path, "rb") as txt_file:
            # Create a multipart form with the text file
            files = {"file": ("test.txt", txt_file, "text/plain")}

            # Make a POST request to the conversion endpoint
            response = client.post("/api/v1/pdf/convert", files=files)

            # Check the response
            assert response.status_code == 415
            assert "detail" in response.json()
            assert "Unsupported file type" in response.json()["detail"]
    finally:
        # Clean up
        if os.path.exists(txt_path):
            os.unlink(txt_path)


def test_convert_pdf_file_too_large(client, sample_pdf_path, monkeypatch):
    """Test the PDF conversion endpoint with a file that's too large."""
    # Temporarily set the max upload size to a small value
    from app.core.config import settings
    original_max_size = settings.MAX_UPLOAD_SIZE
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 10)  # 10 bytes

    try:
        # Open the sample PDF file
        with open(sample_pdf_path, "rb") as pdf_file:
            # Create a multipart form with the PDF file
            files = {"file": ("test.pdf", pdf_file, "application/pdf")}

            # Make a POST request to the conversion endpoint
            response = client.post("/api/v1/pdf/convert", files=files)

            # Check the response
            assert response.status_code == 400
            assert "detail" in response.json()
            assert "File size exceeds maximum allowed size" in response.json()["detail"]
    finally:
        # Restore the original max upload size
        monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", original_max_size)
