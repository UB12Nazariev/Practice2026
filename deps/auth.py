from fastapi import Depends, HTTPException, Request
from database.connection import get_db_connection, release_connection
from config.config import load_config

config = load_config()


async def get_current_user(request: Request):
    user_id = request.cookies.get(config.auth.cookie_name)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = await get_db_connection()
    try:
        user = await conn.fetchrow(
            "SELECT id, username FROM users WHERE id=$1 AND is_active=true",
            int(user_id),
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid session")

        return dict(user)
    finally:
        await release_connection(conn)
