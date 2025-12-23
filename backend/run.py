#!/usr/bin/env python3
"""
Case Whisperer Backend Server
"""
import asyncio
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.core.database import create_tables
from app.services.scheduler import scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    """Lifespan event handler for FastAPI"""
    # Startup
    logger.info("Starting Case Whisperer Backend...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # Start scheduler
    await scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Case Whisperer Backend...")
    
    # Stop scheduler
    await scheduler.stop()
    logger.info("Scheduler stopped")

# Set the lifespan for the app
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        lifespan="on"
    )