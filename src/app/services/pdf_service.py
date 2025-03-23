"""PDF to text conversion service."""

from pathlib import Path
from typing import Union

import pypdf
from loguru import logger


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
        self.ocr_enabled = ocr_enabled
        logger.info("Initialized PDF service with OCR enabled: {}", ocr_enabled)

    def extract_text_from_pdf(self, file_path: Union[str, Path]) -> str:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text from the PDF.

        Raises:
            PDFConversionError: If text extraction fails.
        """
        try:
            file_path = Path(file_path)
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

    def _extract_text_standard(self, file_path: Path) -> str:
        """Extract text from a PDF using standard extraction.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text from the PDF.
        """
        try:
            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
                return text
        except FileNotFoundError as e:
            # propagate the error
            logger.error("File not found: {}", file_path)
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
            This is a simplified implementation. In a production environment,
            you would want to convert each page to an image and process them
            individually.
        """
        try:
            logger.warning(
                "OCR extraction is a placeholder. Implement full conversion for production use."
            )
            return "OCR text extraction not fully implemented. This is a placeholder."
        except Exception as e:
            logger.warning("OCR text extraction failed: {}", str(e))
            return ""
