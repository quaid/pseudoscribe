#!/usr/bin/env python3
"""
Entry point script for the PseudoScribe API container.
This script starts the FastAPI application in a production-style configuration.
"""

import uvicorn

if __name__ == "__main__":
    # Start the FastAPI application without the reloader for stability.
    uvicorn.run(
        "pseudoscribe.api.app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
