"""PDF models."""

from typing import Optional

from pydantic import BaseModel, Field


class PDFTextResponse(BaseModel):
    """Response model for PDF text extraction."""

    text: str = Field(..., description="Extracted text from the PDF")
    filename: str = Field(..., description="Original filename")
    page_count: Optional[int] = Field(None, description="Number of pages in the PDF")
    ocr_used: bool = Field(False, description="Whether OCR was used for extraction")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "text": "This is the extracted text from the PDF...",
                "filename": "example.pdf",
                "page_count": 5,
                "ocr_used": False,
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error detail")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"example": {"detail": "Failed to process PDF file"}}
