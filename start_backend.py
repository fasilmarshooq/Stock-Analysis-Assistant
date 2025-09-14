#!/usr/bin/env python3
"""
Start script for Stock Analysis Assistant Backend
"""

import uvicorn
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

if __name__ == "__main__":
    # Change to backend directory to run the app
    os.chdir(backend_path)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 