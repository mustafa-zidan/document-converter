"""PDF to text conversion service."""

from pathlib import Path
from typing import BinaryIO, Union

import pypdf
import pytesseract
from loguru import logger
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image


class PDFConversionError(Exception):
    """Exception raised when PDF conversion fails."""

    pass


class PDFService:
    """Service for converting PDF files to text."""

    def __init__(self, ocr_enabled: bool = True):
        """Initialize the PDF service.

        Args:
            ocr_enabled: Whether to use OCR for scanned PDFs.
        """
        self.ocr_enabled: bool = ocr_enabled
        logger.info("Initialized PDF service with OCR enabled: {}", ocr_enabled)

    def extract_text_from_pdf(self, file_input: Union[str, Path, BinaryIO]) -> str:
        """Extract text from a PDF file.

        Args:
            file_input: Path to the PDF file or a file-like object.

        Returns:
            Extracted text from the PDF.

        Raises:
            PDFConversionError: If text extraction fails.
        """
        try:
            # Check if file_input is a file-like object
            if hasattr(file_input, 'read'):
                logger.info("Extracting text from PDF file object")

                # Try standard PDF text extraction first
                text = self._extract_text_standard(file_input)

                # If no text was extracted and OCR is enabled, try OCR
                if not text.strip() and self.ocr_enabled:
                    logger.info("No text found with standard extraction, trying OCR")
                    # Get the file content as bytes
                    file_input.seek(0)
                    file_bytes = file_input.read()
                    text = self._extract_text_ocr_from_bytes(file_bytes)
            else:
                # Handle file path
                file_path = Path(file_input)
                logger.info("Extracting text from PDF: {}", file_path)

                # Try standard PDF text extraction first
                text = self._extract_text_standard(file_path)

                # If no text was extracted and OCR is enabled, try OCR
                if not text.strip() and self.ocr_enabled:
                    logger.info("No text found with standard extraction, trying OCR")
                    text = self._extract_text_ocr(file_path)

            logger.info("Successfully extracted {} characters from PDF", len(text))
            return text
        except Exception as e:
            error_msg = f"Failed to extract text from PDF: {str(e)}"
            logger.error(error_msg)
            raise PDFConversionError(error_msg) from e

    def _extract_text_standard(self, file_input: Union[Path, BinaryIO]) -> str:
        """Extract text from a PDF using standard extraction.

        Args:
            file_input: Path to the PDF file or a file-like object.

        Returns:
            Extracted text from the PDF.
        """
        try:
            # Check if file_input is a file-like object
            if hasattr(file_input, 'read'):
                # Use the file object directly
                file_input.seek(0)
                reader: pypdf.PdfReader = pypdf.PdfReader(file_input)
                text: str = ""
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
                return text
            else:
                # Handle file path
                with open(file_input, "rb") as file:
                    reader: pypdf.PdfReader = pypdf.PdfReader(file)
                    text: str = ""
                    for page in reader.pages:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                    return text
        except FileNotFoundError as e:
            # propagate the error
            logger.error("File not found: {}", file_input)
            raise e
        except Exception as e:
            logger.warning(type(e))
            logger.warning("Standard text extraction failed: {}", str(e))
            return ""

    def _extract_text_ocr(self, file_path: Path) -> str:
        """Extract text from a PDF using OCR.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text from the PDF.

        Note:
            This implementation converts each page of the PDF to an image
            and then uses pytesseract to extract text from each image.
        """
        try:
            logger.info("Starting OCR text extraction for: {}", file_path)

            # Convert PDF to list of PIL Image objects
            images = convert_from_path(file_path)
            logger.info("Converted PDF to {} images", len(images))

            # Extract text from each image using pytesseract
            text = ""
            for i, image in enumerate(images):
                logger.debug("Processing page {} with OCR", i + 1)
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"

            logger.info("OCR extraction complete, extracted {} characters", len(text))
            return text
        except Exception as e:
            logger.warning("OCR text extraction failed: {}", str(e))
            return ""

    def _extract_text_ocr_from_bytes(self, file_bytes: bytes) -> str:
        """Extract text from a PDF using OCR from bytes.

        Args:
            file_bytes: PDF file content as bytes.

        Returns:
            Extracted text from the PDF.

        Note:
            This implementation converts each page of the PDF to an image
            and then uses pytesseract to extract text from each image.
        """
        try:
            logger.info("Starting OCR text extraction from bytes")

            # Convert PDF bytes to list of PIL Image objects
            images = convert_from_bytes(file_bytes)
            logger.info("Converted PDF to {} images", len(images))

            # Extract text from each image using pytesseract
            text = ""
            for i, image in enumerate(images):
                logger.debug("Processing page {} with OCR", i + 1)
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"

            logger.info("OCR extraction complete, extracted {} characters", len(text))
            return text
        except Exception as e:
            logger.warning("OCR text extraction from bytes failed: {}", str(e))
            return ""
