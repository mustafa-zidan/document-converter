"""Tests for the PDF service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

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


@patch("app.services.pdf_service.pypdf.PdfReader")
def test_extract_text_standard_exception(mock_pdf_reader, pdf_service, sample_pdf_path):
    """Test exception handling in standard text extraction."""
    # Mock PdfReader to raise an exception
    mock_pdf_reader.side_effect = Exception("Test exception")

    with pytest.raises(FileNotFoundError):
        pdf_service._extract_text_standard(Path("non_existent_file.pdf"))

    # Extract text should raise a PDFConversionError if file does not exist or
    # empty text if the extraction fails
    text = pdf_service._extract_text_standard(sample_pdf_path)
    assert text == ""


@patch("app.services.pdf_service.PDFService._extract_text_standard")
def test_ocr_fallback(mock_extract_standard, pdf_service, sample_pdf_path):
    """Test OCR fallback when standard extraction returns no text."""
    # Mock standard extraction to return empty string
    mock_extract_standard.return_value = ""

    # Mock OCR extraction
    pdf_service._extract_text_ocr = MagicMock(return_value="OCR extracted text")

    # Extract text should fall back to OCR
    text = pdf_service.extract_text_from_pdf(sample_pdf_path)
    assert text == "OCR extracted text"
    pdf_service._extract_text_ocr.assert_called_once()


def test_extract_text_ocr(pdf_service, sample_pdf_path):
    """Test OCR text extraction from a PDF using actual pytesseract.

    This test uses the real OCR functionality to extract text from a PDF.
    If Tesseract is not installed, the test will be skipped.
    """
    # Check if Tesseract is installed
    import shutil
    tesseract_installed = shutil.which("tesseract") is not None

    if not tesseract_installed:
        pytest.skip("Tesseract OCR is not installed. Skipping OCR test.")

    # Extract text using OCR
    text = pdf_service._extract_text_ocr(Path(sample_pdf_path))

    # Verify the results
    assert "Hello, this is a test PDF!" in text
    assert len(text) > 0
