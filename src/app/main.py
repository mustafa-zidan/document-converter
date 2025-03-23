"""Main application module."""

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1.endpoints import pdf as pdf_v1
from app.api.v2.endpoints import pdf as pdf_v2
from app.core.config import settings
from app.core.version import __version__, get_version

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.info(f"Starting {settings.PROJECT_NAME} v{__version__}")

# Preload the SmolDocling model at application startup
from app.api.v2.endpoints.pdf import get_smoldocling_service
logger.info("Preloading SmolDocling model at application startup")
get_smoldocling_service()  # This will initialize the singleton instance


def create_application() -> FastAPI:
    """Create FastAPI application.

    Returns:
        FastAPI application.
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        description="API for converting PDF files to text",
        version=__version__,
    )

    # Set up CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add exception handlers
    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Global exception handler.

        Args:
            request: Request that caused the exception.
            exc: Exception that was raised.

        Returns:
            JSON response with error details.
        """
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"},
        )

    # Include API routers
    application.include_router(
        pdf_v1.router,
        prefix=f"{settings.API_V1_STR}/pdf",
        tags=["pdf-v1"],
    )

    # Include v2 API routers
    application.include_router(
        pdf_v2.router,
        prefix=f"{settings.API_V2_STR}/pdf",
        tags=["pdf-v2"],
    )

    @application.get("/", include_in_schema=False)
    async def root() -> Dict[str, Any]:
        """Root endpoint.

        Returns:
            Welcome message with version information.
        """
        return {
            "message": "Welcome to the Document Converter API",
            "version": __version__,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    return application


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
