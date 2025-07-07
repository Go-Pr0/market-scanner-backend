from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.routers import health, market, trendspider, auth

# Import AI router
from app.routers import ai as ai_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application instance
app = FastAPI(title=settings.app_name, version=settings.version)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log all requests, especially OPTIONS
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Request: {request.method} {request.url.path} from {client_host}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method == "OPTIONS":
        logger.info(f"OPTIONS request to {request.url.path}")
        logger.info(f"Origin header: {request.headers.get('origin', 'Not set')}")
        logger.info(f"Access-Control-Request-Method: {request.headers.get('access-control-request-method', 'Not set')}")
        logger.info(f"Access-Control-Request-Headers: {request.headers.get('access-control-request-headers', 'Not set')}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include application routers
app.include_router(health.router)
app.include_router(market.router)
app.include_router(trendspider.router)
app.include_router(auth.router)
# AI endpoints
app.include_router(ai_router.router)


# ---------------------------------------------------------------------------
# Background tasks: refresh caches and run Bybit monitor
# ---------------------------------------------------------------------------

from app.services.fully_diluted_service import update_fully_diluted_cache
from app.services.market_analysis_service import update_market_analysis_cache
from app.services.bybit_monitor_service import bybit_monitor_service
from app.trendspider import trendspider_setup


async def _fully_diluted_cache_refresher() -> None:
    """Periodically refresh the fully-diluted coins cache."""
    # Populate cache once before entering the loop so that initial requests
    # have data available as soon as possible.
    await run_in_threadpool(update_fully_diluted_cache)

    while True:
        await asyncio.sleep(settings.fully_diluted_update_interval)
        await run_in_threadpool(update_fully_diluted_cache)


async def _market_analysis_cache_refresher() -> None:
    """Periodically refresh the market analysis cache."""
    # Wait a bit for Bybit data to be available before first refresh
    await asyncio.sleep(60)  # Wait 1 minute after startup
    
    # Populate cache once before entering the loop
    await update_market_analysis_cache()

    while True:
        await asyncio.sleep(settings.market_analysis_update_interval)
        await update_market_analysis_cache()


# Register startup event to launch background tasks
@app.on_event("startup")
async def start_background_tasks() -> None:
    # Initialize User database
    from app.services.user_db import user_db
    # Database is initialized automatically when imported
    
    # Initialize AI Assistant database
    from app.services.ai_assistant_db import ai_assistant_db
    # Database is initialized automatically when imported
    
    # Initialize TrendSpider module
    trendspider_setup()
    
    # Start the Bybit monitor service
    await bybit_monitor_service.start()
    
    # Start cache refresh tasks
    asyncio.create_task(_fully_diluted_cache_refresher())
    asyncio.create_task(_market_analysis_cache_refresher())


# Register shutdown event to clean up background tasks
@app.on_event("shutdown")
async def shutdown_background_tasks() -> None:
    # Stop the Bybit monitor service
    await bybit_monitor_service.stop()


# Application entry point when executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 