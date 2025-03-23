"""PDF endpoints."""

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger

from app.core.config import settings
from app.models.pdf import ErrorResponse, PDFTextResponse
from app.services.pdf_service import PDFConversionError, PDFService

router = APIRouter()


def get_pdf_service() -> PDFService:
    """Get PDF service instance.

    Returns:
        PDFService instance.
    """
    return PDFService(ocr_enabled=settings.OCR_ENABLED)


@router.post(
    "/convert",
    response_model=PDFTextResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    summary="Convert PDF to text",
    description="Upload a PDF file and convert it to text",
)
async def convert_pdf_to_text(
    file: UploadFile = File(...),
    pdf_service: PDFService = Depends(get_pdf_service),
) -> PDFTextResponse:
    """Convert PDF to text.

    Args:
        file: Uploaded PDF file.
        pdf_service: PDF service instance.

    Returns:
        Extracted text from the PDF.

    Raises:
        HTTPException: If file validation fails or conversion fails.
    """
    # Validate file size
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
        )

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Save uploaded file to temporary file
    temp_file_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_ext}"
        ) as temp_file:
            temp_file_path = temp_file.name
            content: bytes = await file.read()
            temp_file.write(content)

        # Extract text from PDF
        try:
            text = pdf_service.extract_text_from_pdf(temp_file_path)

            # Get page count (simplified implementation)
            page_count: Optional[int] = None
            ocr_used: bool = False  # In a real implementation, this would be determined by the service

            return PDFTextResponse(
                text=text,
                filename=file.filename,
                page_count=page_count,
                ocr_used=ocr_used,
            )
        except PDFConversionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the file",
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
