# Use Python 3.8 as the base image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]