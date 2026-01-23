import logging
from database.connection import get_db_connection

logger = logging.getLogger(__name__)


async def resolve_groups(position: str) -> list[str]:
    conn = None
    try:
        conn = await get_db_connection()
        rows = await conn.fetch("""
            SELECT ad_groups
            FROM ad_group_rules
            WHERE is_active = TRUE
              AND position = $1
            ORDER BY priority
            LIMIT 1
        """, position)

        if not rows:
            logger.warning(f"⚠️ Нет AD-групп для должности: {position}")
            return []

        return rows[0]["ad_groups"]

    except Exception as e:
        logger.error(f"❌ Ошибка resolve_groups: {e}")
        return []

    finally:
        if conn:
            await conn.close()
