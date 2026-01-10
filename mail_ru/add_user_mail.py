from get_tokens.token_manager import TokenManager
import requests
import logging
from infrastructure.database.db import add_employee_mail
from infrastructure.database.connection import get_pg_connection
from config.config import Config, load_config
from psycopg import AsyncConnection
import asyncio

config: Config = load_config()

logging.basicConfig(
    level=logging.getLevelName(level=config.log.level),
    format=config.log.format,
)

logger = logging.getLogger(__name__)

token_manager = TokenManager()
access_token = token_manager.get_access_token()

user_data = {
    "username": "scovoroda",
    "password": "georgy19054y37478346374",
    "firstname": "Алексей",
    "lastname": "Пупкин"
}


async def add_mail_user(token, data):
    response = requests.post(
        "https://biz.mail.ru/api/v1/domains/8025776/users",
        params={"access_token": token},
        data=data,
        verify=False,
    )
    if response.status_code == 201:
        # Создаем соединение
        conn: AsyncConnection = await get_pg_connection(
            db_name=config.db.name,
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
        )
        try:
            await add_employee_mail(conn, user_data['username'], user_data['password'],
                                    user_data['firstname'], user_data['lastname'])
            logger.info('Пользователь успешно добавлен')
        finally:
            # Закрываем соединение в любом случае
            await conn.close()
    else:
        logger.error(f'Произошла ошибка: {response.text}')
    return response.json()


asyncio.run(add_mail_user(access_token, user_data))
