import aiohttp
import logging
import secrets
import string
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from config.config import Config, load_config
from database.db import add_mail_to_employee, update_employee_mail_status
from database.connection import get_db_connection
from services.token_manager import TokenManager
from core.exception import MailServiceError

logger = logging.getLogger(__name__)
config: Config = load_config()
token_manager = TokenManager()


async def create_mail_account_async(
        last_name: str,
        first_name: str,
        login: str,
        position: str,
        email: str,
        employee_id: Optional[int] = None,
        custom_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Создать почтовый ящик в Mail.ru (асинхронная версия)

    Args:
        last_name: Фамилия
        first_name: Имя
        login: Логин пользователя
        position: Должность
        email: Email адрес
        employee_id: ID сотрудника в БД
        custom_password: Кастомный пароль (если не указан - сгенерируется)

    Returns:
        Словарь с результатом операции
    """
    try:
        logger.info(f"Начато создание почтового ящика для {login} ({email})")

        # Генерация или использование кастомного пароля
        password = custom_password if custom_password else generate_secure_password()
        # print("Сгенерированный пароль: ", password)

        # Подготовка данных для API Mail.ru
        user_data = {
            "username": login,
            "password": password,
            "firstname": first_name,
            "lastname": last_name,
            # "position": position,
            # "email": email
        }

        # Получение токена доступа
        access_token = token_manager.get_access_token()

        # Вызов API Mail.ru (демо-версия)
        mail_response = await call_mail_api(access_token, user_data)

        if mail_response.get("success"):
            # Сохранение информации в базу данных
            if employee_id:
                conn = await get_db_connection()
                try:
                    await add_mail_to_employee(
                        conn=conn,
                        employee_id=employee_id,
                        email=email,
                        mail_password=password,
                        mail_user_id=mail_response.get('response_json').get('id'),
                        status="created"
                    )
                    logger.info(f"✅ Почтовый ящик для {login} успешно создан и сохранен в БД")
                except Exception as db_error:
                    logger.error(f"Ошибка сохранения в БД: {db_error}")
                finally:
                    await conn.close()
            else:
                # Если нет employee_id, создаем запись в логе
                logger.info(f"✅ Почтовый ящик для {login} создан, но нет связи с БД")

            return {
                "success": True,
                "login": login,
                "email": email,
                "mail_user_id": mail_response.get("mail_user_id"),
                "message": "Почтовый ящик создан успешно",
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_msg = mail_response.get("error", "Unknown error")

            # Обновляем статус в БД при ошибке
            if employee_id:
                try:
                    conn = await get_db_connection()
                    await update_employee_mail_status(conn, employee_id, "error", error_msg)
                    await conn.close()
                except Exception:
                    pass

            logger.error(f"❌ Ошибка создания почты для {login}: {error_msg}")
            raise MailServiceError(f"Mail.ru API error: {error_msg}")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при создании почты для {login}: {str(e)}")

        # Обновляем статус в БД при ошибке
        if employee_id:
            try:
                conn = await get_db_connection()
                await update_employee_mail_status(conn, employee_id, "error", str(e))
                await conn.close()
            except Exception:
                pass

        raise MailServiceError(f"Failed to create mail account: {str(e)}")


def generate_secure_password(length: int = 16) -> str:
    """Генерация безопасного пароля"""
    # Используем секретный модуль для криптографически безопасной генерации
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def call_mail_api(access_token: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Вызов API Mail.ru для создания пользователя

    Args:
        access_token: Токен доступа
        user_data: Данные пользователя

    Returns:
        Ответ от API Mail.ru
    """
    try:
        # В реальном приложении здесь будет вызов настоящего API
        # Для демо-режима имитируем API вызов

        logger.info(f"Вызов Mail.ru API для пользователя: {user_data['username']}")

        # Имитация задержки сети
        # await asyncio.sleep(2)

        # Демо-ответ (успешный)
        # В реальном приложении будет что-то вроде:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.mail.api_url}/domains/{config.mail.domain_id}/users",
                params={"access_token": access_token},
                json=user_data,
                ssl=False
            ) as response:
                if response.status == 201:
                    print("Статус код 201")
                    response_json = await response.json()
                    # print("Через метод словаря: ", response_json.get('id'))
                    # print("Через метод массива", response_json['id'])
                    return {"success": True, "response_json": response_json}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": error_text}

        # Для тестирования можно раскомментировать для имитации ошибки:
        # if secrets.randbelow(10) < 2:  # 20% chance of error
        #     return {
        #         "success": False,
        #         "error": "Domain quota exceeded"
        #     }

        # return {
        #     "success": True,
        #     "user_id": f"mail_user_{secrets.token_hex(8)}",
        #     "domain_id": config.mail.domain_id,
        #     "email": user_data['email'],
        #     "mail_user_id": f"MU{secrets.token_hex(10)}"
        # }

    except aiohttp.ClientError as e:
        logger.error(f"Сетевая ошибка при вызове Mail.ru API: {str(e)}")
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Ошибка при вызове Mail.ru API: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Синхронная версия для обратной совместимости
def create_mail_user_sync(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Синхронная версия для создания пользователя
    (например, для использования в скриптах)
    """
    import asyncio

    return asyncio.run(create_mail_account_async(
        user_data.get("lastname", ""),
        user_data.get("firstname", ""),
        user_data.get("username", ""),
        user_data.get("position", ""),
        user_data.get("email", f"{user_data.get('username', '')}@company.ru"),
        user_data.get("employee_id"),
        user_data.get("password")
    ))