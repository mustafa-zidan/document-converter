#!/usr/bin/env python
"""Example client for the Document Converter API."""
import argparse
import sys
from pathlib import Path

import requests


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Document Converter API Client Example")
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file to convert",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="API host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API port (default: 8000)",
    )
    parser.add_argument(
        "--api-version",
        type=str,
        default="v1",
        help="API version (default: v1)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default="pdf/convert",
        help="API endpoint path (default: pdf/convert)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save the extracted text (default: print to stdout)",
    )
    return parser.parse_args()


def main():
    """Run the client example."""
    args = parse_args()

    # Check if the PDF file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    print(f"Converting PDF file: {pdf_path}")

    # Construct the API URL from components
    api_url = f"http://{args.host}:{args.port}/api/{args.api_version}/{args.path}"
    print(f"API URL: {api_url}")

    try:
        # Open the PDF file
        with open(pdf_path, "rb") as pdf_file:
            # Create a multipart form with the PDF file
            files = {"file": (pdf_path.name, pdf_file, "application/pdf")}

            # Make a POST request to the conversion endpoint
            print("Sending request to API...")
            response = requests.post(api_url, files=files)

            # Check if the request was successful
            response.raise_for_status()

            # Parse the response
            result = response.json()
            text = result["text"]

            # Print or save the extracted text
            if args.output:
                output_path = Path(args.output)
                print(f"Saving extracted text to: {output_path}")
                with open(output_path, "w", encoding="utf-8") as output_file:
                    output_file.write(text)
            else:
                print("\nExtracted Text:")
                print("-" * 40)
                print(text)
                print("-" * 40)

            print(f"\nSuccess! Extracted {len(text)} characters from {pdf_path.name}")
            if result.get("ocr_used"):
                print("Note: OCR was used for text extraction")

            return 0
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "Unknown error")
                print(f"API error: {error_detail}")
            except ValueError:
                print(f"API returned status code {e.response.status_code}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
