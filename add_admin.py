from services.auth_service import AuthService
from database.connection import get_db_connection
import asyncio


async def create_admin():
    conn = await get_db_connection()
    service = AuthService(conn)
    await service.create_user("admin", "admin123")
    print("admin created")


asyncio.run(create_admin())
