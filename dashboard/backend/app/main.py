"""
AI Operations Dashboard Backend

FastAPI application that provides:
- Health check aggregation for all monitored services
- Trace lookup and search via Jaeger API
- Unified API for the frontend dashboard widget
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import health_router, traces_router, aiai_router, supervision_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Jaeger URL: {settings.jaeger_base_url}")
    logger.info(f"MLI URL: {settings.mli_base_url}")
    yield
    logger.info("Shutting down dashboard backend")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend service for the AI Operations Dashboard. "
            "Provides unified API for health checks and trace lookup."
        ),
        lifespan=lifespan,
    )

    # Configure CORS
    if settings.cors_origins == "*":
        # Allow all origins (development mode)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Specific origins (production mode)
        origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(traces_router)
    app.include_router(aiai_router)
    app.include_router(supervision_router)

    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/health/",
            "traces": "/api/traces/",
            "supervision": "/api/supervision/",
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
