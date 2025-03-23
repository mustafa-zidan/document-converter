"""Tests for the SmolDocling service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

from app.services.smoldocling_service import SmolDoclingConversionError, SmolDoclingService


@pytest.fixture
def mock_processor():
    """Mock the AutoProcessor."""
    with patch("app.services.smoldocling_service.AutoProcessor") as mock:
        processor = MagicMock()
        mock.from_pretrained.return_value = processor

        # Mock the batch_decode method
        processor.batch_decode.return_value = ["Extracted text from image"]

        yield processor


@pytest.fixture
def mock_model():
    """Mock the AutoModelForVision2Seq."""
    with patch("app.services.smoldocling_service.AutoModelForVision2Seq") as mock:
        model = MagicMock()
        mock.from_pretrained.return_value = model

        # Mock the generate method
        model.generate.return_value = "generated_ids"

        # Mock the to method (for device placement)
        model.to.return_value = model

        yield model


@pytest.fixture
def mock_torch_cuda():
    """Mock torch.cuda to simulate GPU availability."""
    with patch("app.services.smoldocling_service.torch.cuda") as mock_cuda:
        # Default to GPU not available
        mock_cuda.is_available.return_value = False
        yield mock_cuda


@pytest.fixture
def smoldocling_service(mock_processor, mock_model, mock_torch_cuda):
    """Create a SmolDocling service instance for testing with mocked dependencies."""
    with patch("app.services.smoldocling_service.torch.backends.mps.is_available", return_value=False):
        service = SmolDoclingService()
        return service


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


def test_init_with_gpu(mock_processor, mock_model):
    """Test initialization with GPU available."""
    with patch("app.services.smoldocling_service.torch.cuda.is_available", return_value=True):
        service = SmolDoclingService()
        assert service.device == "cuda"
        assert service.model_name == "ds4sd/SmolDocling-256M-preview"


def test_init_with_mps(mock_processor, mock_model):
    """Test initialization with Apple Silicon GPU available."""
    with patch("app.services.smoldocling_service.torch.cuda.is_available", return_value=False):
        with patch("app.services.smoldocling_service.platform.system", return_value="Darwin"):
            with patch("app.services.smoldocling_service.torch.backends.mps.is_available", return_value=True):
                service = SmolDoclingService()
                assert service.device == "mps"


def test_init_with_cpu(mock_processor, mock_model):
    """Test initialization with no GPU available."""
    with patch("app.services.smoldocling_service.torch.cuda.is_available", return_value=False):
        with patch("app.services.smoldocling_service.platform.system", return_value="Linux"):
            service = SmolDoclingService()
            assert service.device == "cpu"


def test_init_error():
    """Test error handling during initialization."""
    with patch("app.services.smoldocling_service.AutoProcessor.from_pretrained", side_effect=Exception("Test exception")):
        with pytest.raises(SmolDoclingConversionError):
            SmolDoclingService()


def test_extract_text_from_pdf(smoldocling_service, sample_pdf_path):
    """Test the main text extraction method."""
    # Mock the helper methods
    smoldocling_service._convert_pdf_to_images = MagicMock(return_value=[Image.new('RGB', (100, 100))])
    smoldocling_service._extract_text_from_image = MagicMock(return_value="Extracted text from page")

    # Extract text from the sample PDF
    text = smoldocling_service.extract_text_from_pdf(sample_pdf_path)

    # Check that the text was extracted correctly
    assert text == "Extracted text from page"
    smoldocling_service._convert_pdf_to_images.assert_called_once()
    smoldocling_service._extract_text_from_image.assert_called_once()


def test_extract_text_from_pdf_multiple_pages(smoldocling_service, sample_pdf_path):
    """Test text extraction from a multi-page PDF."""
    # Mock the helper methods to simulate multiple pages
    smoldocling_service._convert_pdf_to_images = MagicMock(return_value=[
        Image.new('RGB', (100, 100)),
        Image.new('RGB', (100, 100)),
        Image.new('RGB', (100, 100))
    ])
    smoldocling_service._extract_text_from_image = MagicMock(return_value="Extracted text from page")

    # Extract text from the sample PDF
    text = smoldocling_service.extract_text_from_pdf(sample_pdf_path)

    # Check that the text was extracted correctly
    assert text == "Extracted text from page\n\nExtracted text from page\n\nExtracted text from page"
    assert smoldocling_service._convert_pdf_to_images.call_count == 1
    assert smoldocling_service._extract_text_from_image.call_count == 3


def test_extract_text_from_pdf_error(smoldocling_service):
    """Test error handling in text extraction."""
    # Test with a non-existent file
    with pytest.raises(SmolDoclingConversionError):
        smoldocling_service.extract_text_from_pdf("non_existent_file.pdf")


@patch("app.services.smoldocling_service.convert_from_path")
def test_convert_pdf_to_images(mock_convert, smoldocling_service, sample_pdf_path):
    """Test PDF to image conversion."""
    # Mock the convert_from_path function
    mock_images = [Image.new('RGB', (100, 100)), Image.new('RGB', (100, 100))]
    mock_convert.return_value = mock_images

    # Convert the PDF to images
    images = smoldocling_service._convert_pdf_to_images(Path(sample_pdf_path))

    # Check that the conversion was done correctly
    assert images == mock_images
    mock_convert.assert_called_once_with(Path(sample_pdf_path))


@patch("app.services.smoldocling_service.convert_from_path")
def test_convert_pdf_to_images_error(mock_convert, smoldocling_service, sample_pdf_path):
    """Test error handling in PDF to image conversion."""
    # Mock convert_from_path to raise an exception
    mock_convert.side_effect = Exception("Test exception")

    # Converting the PDF should raise a SmolDoclingConversionError
    with pytest.raises(SmolDoclingConversionError):
        smoldocling_service._convert_pdf_to_images(Path(sample_pdf_path))


def test_extract_text_from_image(smoldocling_service):
    """Test text extraction from an image."""
    # Create a test image
    image = Image.new('RGB', (100, 100))

    # Mock the processor and model behavior
    inputs = MagicMock()
    inputs.pixel_values = MagicMock()
    inputs.pixel_values.shape = [1, 3, 100, 100]  # Non-empty shape
    smoldocling_service.processor.return_value = inputs

    # Extract text from the image
    text = smoldocling_service._extract_text_from_image(image)

    # Check that the text was extracted correctly
    assert text == "Extracted text from image"
    smoldocling_service.processor.assert_called_once()
    smoldocling_service.model.generate.assert_called_once()
    smoldocling_service.processor.batch_decode.assert_called_once()


def test_extract_text_from_image_empty(smoldocling_service):
    """Test text extraction from an empty image."""
    # Create a test image
    image = Image.new('RGB', (100, 100))

    # Create a patch for the _extract_text_from_image method to test the empty image case
    with patch.object(smoldocling_service, 'processor') as mock_processor:
        # Set up the mock to return an object with the properties we need
        mock_inputs = MagicMock()
        mock_inputs.pixel_values = MagicMock()
        mock_inputs.pixel_values.shape = [0, 3, 100, 100]  # Empty shape
        mock_inputs.to = MagicMock(return_value=mock_inputs)

        # Make the processor return our mock inputs
        mock_processor.return_value = mock_inputs

        # Extract text from the image
        text = smoldocling_service._extract_text_from_image(image)

        # Check that an empty string is returned
        assert text == ""

        # Verify the processor was called
        mock_processor.assert_called_once()

        # Model.generate should not be called for empty images
        smoldocling_service.model.generate.assert_not_called()


def test_extract_text_from_image_error(smoldocling_service):
    """Test error handling in image text extraction."""
    # Create a test image
    image = Image.new('RGB', (100, 100))

    # Mock the processor to raise an exception
    smoldocling_service.processor.side_effect = Exception("Test exception")

    # Extracting text should raise a SmolDoclingConversionError
    with pytest.raises(SmolDoclingConversionError):
        smoldocling_service._extract_text_from_image(image)
