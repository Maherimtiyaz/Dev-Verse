"""
DevVerse AI - Main Application Entry Point

FastAPI application with middleware, routers, and lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.logging_config import setup_logging, get_logger, correlation_id_middleware
from api.v1.router import api_router


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting DevVerse AI...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.APP_VERSION}")
    
    # Setup logging
    setup_logging()
    
    # Initialize database (optional, use migrations in production)
    # await init_db()
    
    logger.info("DevVerse AI started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DevVerse AI...")
    
    # Cleanup resources
    from db.session import close_db
    await close_db()
    
    logger.info("DevVerse AI shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## DevVerse AI - Your AI Developer Platform

DevVerse AI combines cutting-edge AI with developer tools to help you:

### 🧬 AI GitHub Twin
Get a comprehensive developer profile analyzing your GitHub activity, coding patterns, and engineering style.

### 🔥 AI Code Roast
Receive brutal but helpful code reviews in professional mode or Gen-Z roast mode.

### 🤝 Open Source Matchmaker
Discover open source projects that match your skills and career goals.

### 👥 Hackathon Partner Finder
Find the perfect teammates for your next hackathon based on compatibility scoring.

---

**Built with:** FastAPI, PostgreSQL, Redis, Qdrant, LangGraph, Next.js
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.middleware("http")(correlation_id_middleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={"path": request.url.path},
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint",
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# Health check at root level too
@app.get("/health", tags=["Health"])
async def health():
    """Quick health check."""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
