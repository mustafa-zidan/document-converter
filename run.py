#!/usr/bin/env python
"""Entry point script for running the Document Converter API."""
import argparse
import sys

import uvicorn


def parse_args():
    """Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run the Document Converter API")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    return parser.parse_args()


def main():
    """Run the application."""
    args = parse_args()
    
    print(f"Starting Document Converter API on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "src.app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())