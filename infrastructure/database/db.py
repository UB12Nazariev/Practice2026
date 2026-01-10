import logging
from psycopg import AsyncConnection
logger = logging.getLogger(__name__)


# Функция добавления сотрудника
async def add_employee_mail(
        conn: AsyncConnection,
        username: str,
        password: str,
        firstname: str,
        lastname: str,
) -> None:
    async with conn.cursor() as cursor:
        await cursor.execute(
            query="""
                INSERT INTO Employees_Mail(username, password, firstname, lastname)
                VALUES(%s, %s, %s, %s) 
                ON CONFLICT DO NOTHING;
            """,
            params=(username, password, firstname, lastname)
        )
    await conn.commit()
    logger.info("Employee added")
