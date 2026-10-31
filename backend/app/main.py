"""
WorkforceIQ FastAPI Main Application Entry Point.
Configures FastAPI app factory, CORS, lifespans, exception handlers, and routing.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.config import get_settings
from app.database import init_db_engine, close_db_engine

# Configure enterprise structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("workforce_iq.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Initializes database connectivity on boot and cleanly closes resources on termination.
    """
    settings = get_settings()
    logger.info(f"Booting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]...")
    
    try:
        engine, dialect = await init_db_engine()
        logger.info(f"Database initialized successfully with dialect '{dialect}'.")
    except Exception as exc:
        logger.error(f"Failed to initialize database during startup: {exc}")
        if not settings.DB_FALLBACK_SQLITE:
            raise exc

    yield  # Application serves requests

    logger.info("Initiating graceful shutdown...")
    await close_db_engine()
    logger.info("Shutdown complete.")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        description="AI-Powered Workforce Demand Forecasting & Skill Gap Intelligence Platform API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    origins = settings.BACKEND_CORS_ORIGINS
    if isinstance(origins, str):
        origins = [origins]

    logger.info(f"Configuring CORS with origins: {origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Mount master API router under /api/v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    async def root():
        """Root API metadata and documentation link."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "online",
            "documentation": "/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    return app


app = create_application()

