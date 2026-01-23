from typing import List, Optional
from database.connection import get_db_connection

DEFAULT_GROUP = ["Default_Employees"]

async def resolve_groups(
    position: str,
) -> List[str]:

    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT ad_groups FROM ad_group_rules
            WHERE is_active = TRUE
              AND (position = $1 OR position IS NULL)
            ORDER BY priority ASC
            LIMIT 1
        """, position)

        if rows:
            return rows[0]["ad_groups"]

        return DEFAULT_GROUP
    finally:
        await conn.close()
