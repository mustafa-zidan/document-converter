"""Service for converting PDF files to text using SmolDocling model."""

from pathlib import Path
from typing import Optional, Union

import torch
from loguru import logger
from pdf2image import convert_from_path
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor


class SmolDoclingConversionError(Exception):
    """Exception raised when SmolDocling conversion fails."""

    pass


class SmolDoclingService:
    """Service for converting PDF files to text using SmolDocling model."""

    def __init__(self, model_name: str = "ds4sd/SmolDocling-256M-preview"):
        """Initialize the SmolDocling service.

        Args:
            model_name: Name of the SmolDocling model to use.
        """
        self.model_name = model_name
        logger.info("Initializing SmolDocling service with model: {}", model_name)

        try:
            # Load model and processor
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = AutoModelForVision2Seq.from_pretrained(model_name)

            # Move model to GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)

            logger.info(
                "Successfully loaded SmolDocling model on device: {}", self.device
            )
        except Exception as e:
            error_msg = f"Failed to initialize SmolDocling model: {str(e)}"
            logger.error(error_msg)
            raise SmolDoclingConversionError(error_msg) from e

    def extract_text_from_pdf(self, file_path: Union[str, Path]) -> str:
        """Extract text from a PDF file using SmolDocling model.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text from the PDF.

        Raises:
            SmolDoclingConversionError: If text extraction fails.
        """
        try:
            file_path = Path(file_path)
            logger.info("Extracting text from PDF using SmolDocling: {}", file_path)

            # Convert PDF to images
            images = self._convert_pdf_to_images(file_path)

            # Extract text from each image and combine
            all_text = []
            for i, image in enumerate(images):
                logger.info("Processing page {} of {}", i + 1, len(images))
                page_text = self._extract_text_from_image(image)
                all_text.append(page_text)

            # Combine text from all pages
            combined_text = "\n\n".join(all_text)

            logger.info(
                "Successfully extracted {} characters from PDF using SmolDocling",
                len(combined_text),
            )
            return combined_text
        except Exception as e:
            error_msg = f"Failed to extract text from PDF using SmolDocling: {str(e)}"
            logger.error(error_msg)
            raise SmolDoclingConversionError(error_msg) from e

    def _convert_pdf_to_images(self, file_path: Path) -> list:
        """Convert PDF to a list of images.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of PIL Image objects.
        """
        try:
            logger.info("Converting PDF to images: {}", file_path)
            images = convert_from_path(file_path)
            logger.info("Successfully converted PDF to {} images", len(images))
            return images
        except Exception as e:
            error_msg = f"Failed to convert PDF to images: {str(e)}"
            logger.error(error_msg)
            raise SmolDoclingConversionError(error_msg) from e

    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from an image using SmolDocling model.

        Args:
            image: PIL Image object.

        Returns:
            Extracted text from the image.
        """
        try:
            # Preprocess the image
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs.pixel_values,
                    max_length=1024,
                    num_beams=4,
                )

            # Decode the generated text
            generated_text = self.processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

            return generated_text
        except Exception as e:
            error_msg = f"Failed to extract text from image: {str(e)}"
            logger.error(error_msg)
            raise SmolDoclingConversionError(error_msg) from e
