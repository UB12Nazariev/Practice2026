import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from contextlib import asynccontextmanager

import datetime
from config.config import load_config, Config
from api.endpoints import router as api_router
from database.connection import init_db, close_db
import collections
if not hasattr(collections, 'MutableMapping'):
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
from api.health import router as health_router
from api.bitwarden import router as bitwarden_router
# from api.onboarding import router as onboarding_router
from fastapi import APIRouter, Depends, HTTPException
from api.auth import router as auth_router

from services.bitwarden_vault_client import (
    BitwardenVaultLocked,
    BitwardenVaultError,
)


router = APIRouter(
    prefix="/onboarding",
    tags=["onboarding"],
)


# Загрузка конфигурации
config: Config = load_config()

# Настройка логирования
logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при запуске
    logger.info("🚀 Starting StaffFlow application...")

    # Инициализация БД
    await init_db()
    logger.info("✅ Database initialized")

    yield

    # Очистка при завершении
    logger.info("🛑 Shutting down StaffFlow application...")
    await close_db()


# Создание приложения FastAPI
app = FastAPI(
    title="StaffFlow API",
    description="Система автоматического онбординга сотрудников",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Подключение маршрутов API
app.include_router(api_router, prefix="/api")
app.include_router(health_router)
app.include_router(bitwarden_router)
app.include_router(auth_router)


# Настройка статических файлов
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"✅ Static files mounted from: {static_dir}")
else:
    logger.warning(f"⚠️ Static directory not found: {static_dir}")


# Корневой маршрут для фронтенда
@app.get("/")
async def serve_frontend():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found. Please check static files."}


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "StaffFlow",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload
    )