# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies and uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSf https://astral.sh/uv/install.sh | bash

# Copy project files
COPY . .

# Install Python dependencies using uv
RUN uv sync -e .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
