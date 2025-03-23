"""Tests for the PDF service."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

from app.services.pdf_service import PDFConversionError, PDFService


@pytest.fixture
def pdf_service():
    """Create a PDF service instance for testing."""
    return PDFService(ocr_enabled=True)


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


@pytest.fixture
def corrupted_pdf_path():
    """Create a corrupted PDF file for testing."""
    # Create a temporary file with invalid PDF content
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"This is not a valid PDF file")
        pdf_path = temp_file.name

    yield pdf_path

    # Clean up
    if os.path.exists(pdf_path):
        os.unlink(pdf_path)


@pytest.fixture
def image_only_pdf_path():
    """Create a PDF file that contains only an image (no extractable text)."""
    # Create a temporary image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        img_path = temp_img_file.name

    # Create a blank image with text
    img = Image.new("RGB", (500, 500), color="white")
    img.save(img_path)

    # Create a PDF from the image
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf_file:
        pdf_path = temp_pdf_file.name

    # Use the image to create a PDF (this will be an image-only PDF with no extractable text)
    img = Image.open(img_path)
    img.save(pdf_path, "PDF")

    yield pdf_path

    # Clean up
    if os.path.exists(img_path):
        os.unlink(img_path)
    if os.path.exists(pdf_path):
        os.unlink(pdf_path)


def test_extract_text_standard(pdf_service, sample_pdf_path):
    """Test standard text extraction from a PDF."""
    # Extract text from the sample PDF
    text = pdf_service._extract_text_standard(Path(sample_pdf_path))

    # Check that the text was extracted correctly
    assert "Hello, this is a test PDF!" in text
    assert len(text) > 0


def test_extract_text_from_pdf(pdf_service, sample_pdf_path):
    """Test the main text extraction method."""
    # Extract text from the sample PDF
    text = pdf_service.extract_text_from_pdf(sample_pdf_path)

    # Check that the text was extracted correctly
    assert "Hello, this is a test PDF!" in text
    assert len(text) > 0


def test_extract_text_from_pdf_error():
    """Test error handling in text extraction."""
    pdf_service = PDFService()

    # Test with a non-existent file
    with pytest.raises(PDFConversionError):
        pdf_service.extract_text_from_pdf("non_existent_file.pdf")


def test_extract_text_standard_exception(pdf_service):
    """Test exception handling in standard text extraction."""
    # Test with a non-existent file
    with pytest.raises(FileNotFoundError):
        pdf_service._extract_text_standard(Path("non_existent_file.pdf"))

    # Test with a corrupted PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"This is not a valid PDF file")
        corrupted_path = temp_file.name

    try:
        # Extract text should return empty string if the extraction fails
        text = pdf_service._extract_text_standard(Path(corrupted_path))
        assert text == ""
    finally:
        # Clean up
        if os.path.exists(corrupted_path):
            os.unlink(corrupted_path)


def test_ocr_fallback(pdf_service, image_only_pdf_path):
    """Test OCR fallback when standard extraction returns no text."""
    # Skip test if Tesseract is not installed
    tesseract_installed = shutil.which("tesseract") is not None
    if not tesseract_installed:
        pytest.skip("Tesseract OCR is not installed. Skipping OCR test.")

    # Standard extraction should return empty string for image-only PDF
    standard_text = pdf_service._extract_text_standard(Path(image_only_pdf_path))
    assert standard_text.strip() == ""

    # Extract text should fall back to OCR
    text = pdf_service.extract_text_from_pdf(image_only_pdf_path)

    # The text might not be perfect due to OCR, but it should not be empty
    assert len(text) > 0


def test_extract_text_ocr(pdf_service, sample_pdf_path):
    """Test OCR text extraction from a PDF using actual pytesseract.

    This test uses the real OCR functionality to extract text from a PDF.
    If Tesseract is not installed, the test will be skipped.
    """
    # Check if Tesseract is installed
    tesseract_installed = shutil.which("tesseract") is not None

    if not tesseract_installed:
        pytest.skip("Tesseract OCR is not installed. Skipping OCR test.")

    # Extract text using OCR
    text = pdf_service._extract_text_ocr(Path(sample_pdf_path))

    # Verify the results
    assert "Hello, this is a test PDF!" in text
    assert len(text) > 0
