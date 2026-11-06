"""
GeM BidWatch — Production Server Entry Point
Runs Uvicorn with auto-restart and scheduler
"""
import uvicorn
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings import settings

if __name__ == "__main__":
    print(f"Starting GeM BidWatch on {settings.APP_HOST}:{settings.APP_PORT}...")
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
