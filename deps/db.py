from database.connection import get_db_connection, release_connection


async def get_db():
    conn = await get_db_connection()
    try:
        yield conn
    finally:
        await release_connection(conn)
