"""Service for converting PDF files to Markdown using SmolDocling model."""

import platform
import time
from pathlib import Path
from typing import BinaryIO, Union

import torch
from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import DocTagsDocument
from loguru import logger
from pdf2image import convert_from_bytes, convert_from_path
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor


class SmolDoclingConversionError(Exception):
    """Exception raised when SmolDocling conversion fails."""

    pass


class SmolDoclingService:
    """Service for converting PDF files to Markdown using the SmolDocling model."""

    def __init__(self, model_name: str = "ds4sd/SmolDocling-256M-preview"):
        logger.info("🚀 Initializing SmolDocling service with model: {}", model_name)

        try:
            # Select device
            if torch.backends.mps.is_available():
                self.device = "mps"
                torch_dtype = torch.float16
                logger.info("💻 Apple Silicon GPU (MPS) detected")
            elif torch.cuda.is_available():
                self.device = "cuda"
                torch_dtype = torch.bfloat16
                logger.info("🖥️ CUDA GPU detected")
            else:
                self.device = "cpu"
                torch_dtype = torch.float32
                logger.warning("⚠️ No GPU detected. Running on CPU.")

            # Load model
            self.model = AutoModelForVision2Seq.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                _attn_implementation="eager",  # flash_attention not supported on MPS
            ).to(self.device)

            # Load processor
            self.processor = AutoProcessor.from_pretrained(model_name)

            logger.success("✅ SmolDocling model loaded on device: {}", self.device)

        except Exception as e:
            msg = f"Failed to initialize SmolDocling model: {e}"
            logger.exception(msg)
            raise SmolDoclingConversionError(msg) from e

    def extract_text_from_pdf(self, file_input: Union[str, Path, BinaryIO]) -> str:
        start_time = time.time()

        try:
            if hasattr(file_input, "read"):  # file-like object
                logger.info("📄 Extracting from file-like PDF input")
                file_input.seek(0)
                file_bytes = file_input.read()
                images = self._convert_pdf_bytes_to_images(file_bytes)
            else:  # path
                file_path = Path(file_input)
                logger.info("📄 Extracting from PDF file: {}", file_path)
                images = self._convert_pdf_to_images(file_path)

            all_markdown = []
            for i, image in enumerate(images):
                logger.info("🖼️  Processing page {}/{}", i + 1, len(images))
                page_md = self._extract_text_from_image(image)
                all_markdown.append(page_md)

            combined = "\n\n---\n\n".join(all_markdown)
            logger.success(
                "✅ Extracted {} pages in {:.2f}s",
                len(images),
                time.time() - start_time,
            )
            return combined

        except Exception as e:
            msg = f"Failed to extract text from PDF: {e}"
            logger.exception(msg)
            raise SmolDoclingConversionError(msg) from e

    def _convert_pdf_to_images(self, file_path: Path) -> list[Image.Image]:
        try:
            images = convert_from_path(file_path)
            logger.info("🖼️ Converted PDF to {} image(s)", len(images))
            return images
        except Exception as e:
            msg = f"Failed to convert PDF to images: {e}"
            logger.error(msg)
            raise SmolDoclingConversionError(msg) from e

    def _convert_pdf_bytes_to_images(self, file_bytes: bytes) -> list[Image.Image]:
        try:
            images = convert_from_bytes(file_bytes)
            logger.info("🖼️ Converted PDF bytes to {} image(s)", len(images))
            return images
        except Exception as e:
            msg = f"Failed to convert PDF bytes to images: {e}"
            logger.error(msg)
            raise SmolDoclingConversionError(msg) from e

    def _extract_text_from_image(self, image: Image.Image) -> str:
        try:
            # Create chat prompt
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": "Convert this page to docling."},
                    ],
                }
            ]
            prompt = self.processor.apply_chat_template(
                messages, add_generation_prompt=True
            )

            inputs = self.processor(
                text=prompt, images=[image], return_tensors="pt", truncation=True
            ).to(self.device)

            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=8192,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.95,
                )

            prompt_len = inputs["input_ids"].shape[1]
            trimmed_ids = generated_ids[:, prompt_len:]

            doctags = self.processor.batch_decode(
                trimmed_ids, skip_special_tokens=False
            )[0].lstrip()

            # Convert to Markdown
            doctags_doc = DocTagsDocument.from_doctags_and_image_pairs(
                [doctags], [image]
            )
            doc = DoclingDocument(name="ConvertedDocument")
            doc.load_from_doctags(doctags_doc)

            return doc.export_to_markdown()

        except Exception as e:
            msg = f"Failed to extract text from image: {e}"
            logger.exception(msg)
            raise SmolDoclingConversionError(msg) from e
