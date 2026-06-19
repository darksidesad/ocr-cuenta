"""FastAPI application — OCR DIAN."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, facturas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    logger.info("Iniciando OCR DIAN...")
    await init_db()
    logger.info("Base de datos inicializada")
    yield
    logger.info("Apagando OCR DIAN...")


app = FastAPI(
    title="OCR DIAN API",
    description="Servicio de extracción de datos de facturas colombianas usando OCR + LLMs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — configurable via env var CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(facturas.router)


@app.get("/health")
async def health() -> dict:
    """Healthcheck endpoint."""
    return {"status": "ok", "service": "ocr-dian", "environment": settings.environment}
