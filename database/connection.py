import asyncpg
import logging
from typing import Optional
from config.config import Config, load_config

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None
_config: Optional[Config] = None


def get_config() -> Config:
    """Получить конфигурацию"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


async def init_db():
    global _pool
    try:
        config = load_config()
        _pool = await asyncpg.create_pool(
            user=config.db.user,
            password=config.db.password,
            database=config.db.name,
            host=config.db.host,
            port=config.db.port,
            min_size=5,
            max_size=20
        )
        logger.info("✅ Пул соединений БД создан")

        # ДОБАВЬТЕ ЭТИ СТРОКИ:
        from database.db import create_tables
        async with _pool.acquire() as conn:
            await create_tables()
            logger.info("✅ Таблицы базы данных успешно созданы/проверены")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации пула БД: {e}")
        raise


async def get_db_connection():
    """Получить соединение с БД из пула"""
    global _pool

    if _pool is None:
        await init_db()

    if _pool is None:
        raise RuntimeError("Database pool not initialized")

    try:
        return await _pool.acquire()
    except Exception as e:
        logger.error(f"Ошибка получения соединения с БД: {str(e)}")
        raise


async def release_connection(conn):
    """Вернуть соединение в пул"""
    if _pool and not _pool._closed:
        await _pool.release(conn)


async def close_db():
    """Закрыть пул соединений"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Пул соединений с БД закрыт")