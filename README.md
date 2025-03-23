# Document Converter API

A FastAPI service that converts PDF files to text.

## Features

- Convert PDF files to text
- Support for both standard PDFs and scanned PDFs (via OCR)
- Advanced document understanding with SmolDocling model (v2 API)
- RESTful API with OpenAPI documentation
- Proper error handling and validation
- Configurable via environment variables
- Versioned API for better compatibility tracking

## Requirements

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for dependency management (recommended)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (optional, for OCR support)
- PyTorch and Transformers (for v2 API with SmolDocling model)
- pdf2image (for v2 API to convert PDFs to images)

## Installation

### Using the setup script (recommended)

The easiest way to set up the development environment is to use the provided setup script:

```bash
# Clone the repository
git clone https://github.com/yourusername/document-converter.git
cd document-converter

# Run the setup script
./setup.sh
```

The setup script will:
- Check if uv is installed and use it if available
- Create a virtual environment
- Install all dependencies (including development and example dependencies)
- Create a .env file from the template if it doesn't exist
- Create data directories for uploads and logs

### Manual installation

#### Using uv

```bash
# Install uv if you don't have it
curl -sSf https://astral.sh/uv/install.sh | bash

# Clone the repository
git clone https://github.com/yourusername/document-converter.git
cd document-converter

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Configuration

The application can be configured using environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `False` |
| `MAX_UPLOAD_SIZE` | Maximum upload size in bytes | `10485760` (10MB) |
| `ALLOWED_EXTENSIONS` | Comma-separated list of allowed file extensions | `pdf` |
| `OCR_ENABLED` | Enable OCR for scanned PDFs | `True` |
| `BACKEND_CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `[]` |

### Setting up environment variables

You can create a `.env` file in the project root directory to set environment variables. A template is provided in `.env.example`:

```bash
# Copy the example file
cp .env.example .env

# Edit the file with your preferred settings
nano .env  # or use any text editor
```

Example `.env` file:

```
DEBUG=True
MAX_UPLOAD_SIZE=20971520
ALLOWED_EXTENSIONS=pdf
OCR_ENABLED=True
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Usage

### Running the server

#### Using the run script

```bash
# Using the run script (recommended)
./run.py

# With custom options
./run.py --host 127.0.0.1 --port 8080 --reload --workers 4

# Development mode (alternative)
cd src
python -m app.main

# Production mode (using uvicorn directly)
uvicorn src.app.main:app --host 0.0.0.0 --port 8000
```

#### Using Docker

```bash
# Build and run the Docker image
docker build -t document-converter .
docker run -p 8000:8000 document-converter
```

#### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

The API will be available at http://localhost:8000.

### Docker Configuration

You can configure the Docker container by modifying the environment variables in the `docker-compose.yml` file:

```yaml
environment:
  - DEBUG=False
  - MAX_UPLOAD_SIZE=10485760
  - ALLOWED_EXTENSIONS=pdf
  - OCR_ENABLED=True
  - BACKEND_CORS_ORIGINS=
```

A data volume is also mounted to persist data between container restarts:

```yaml
volumes:
  - ./data:/app/data
```

### API Documentation

The API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

#### Root Endpoint

```
GET /
```

Response:
```json
{
  "message": "Welcome to the Document Converter API",
  "version": "0.1.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

This endpoint provides basic information about the API, including the current version.

#### Convert PDF to Text (v1 API)

```
POST /api/v1/pdf/convert
```

Request:
- `file`: PDF file to convert (multipart/form-data)

Response:
```json
{
  "text": "Extracted text from the PDF...",
  "filename": "example.pdf",
  "page_count": 5,
  "ocr_used": false
}
```

#### Convert PDF to Text with SmolDocling (v2 API)

```
POST /api/v1/v2/pdf/convert
```

This endpoint uses the SmolDocling-256M-preview model from Hugging Face for advanced document understanding. It's particularly effective for complex document layouts and can handle a wide variety of document formats.

Request:
- `file`: PDF file to convert (multipart/form-data)

Response:
```json
{
  "text": "Extracted text from the PDF using SmolDocling...",
  "filename": "example.pdf",
  "page_count": 5,
  "ocr_used": false
}
```

> **Note**: The v2 API requires additional dependencies (PyTorch, Transformers, pdf2image) and may have higher computational requirements due to the machine learning model used.

### Example Client

An example client script is provided in the `examples` directory to demonstrate how to use the API programmatically:

```bash
# Basic usage
./examples/client_example.py path/to/your/document.pdf

# Save output to a file
./examples/client_example.py path/to/your/document.pdf --output extracted_text.txt

# Use a different API endpoint
./examples/client_example.py path/to/your/document.pdf --api-url http://api.example.com/api/v1/pdf/convert
```

The example client requires the `requests` library, which you can install using uv:

```bash
# Install requests directly
uv pip install requests

# Or install as an optional dependency group
uv pip install -e ".[examples]"
```

## Versioning

The Document Converter API uses semantic versioning (SemVer) for version management. The version format is `MAJOR.MINOR.PATCH`:

- `MAJOR` version changes indicate incompatible API changes
- `MINOR` version changes add functionality in a backward-compatible manner
- `PATCH` version changes make backward-compatible bug fixes

### Checking the Version

You can check the current version of the API in several ways:

1. **API Root Endpoint**: Send a GET request to the root endpoint (`/`) to see the version in the response.
2. **OpenAPI Documentation**: The version is displayed in the Swagger UI and ReDoc pages.
3. **Startup Logs**: The version is logged when the application starts.

### Version Management

The version is centrally managed in the codebase:

1. The canonical version is defined in `pyproject.toml`
2. The version is exposed through the `app.core.version` module
3. All parts of the application reference this central version

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint code
ruff src tests
```

## License

MIT
