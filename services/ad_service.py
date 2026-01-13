import logging
from typing import Dict, Any, Optional
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, SUBTREE
from config.config import load_config
from database.connection import get_db_connection
from database.db import add_ad_account_to_employee, update_ad_account_status

logger = logging.getLogger(__name__)
config = load_config()


def create_ad_account(
        last_name: str,
        first_name: str,
        login: str,
        position: str,
        employee_id: Optional[int] = None
) -> Dict[str, Any]:
    """Создать учетную запись в Active Directory и обновить БД"""

    server = Server(config.ad.server, get_info=ALL)
    # Формируем DN администратора (может потребоваться корректировка под ваш формат)
    admin_dn = f"{config.ad.admin_user}@{config.ad.domain}"

    conn = Connection(
        server,
        user=admin_dn,
        password=config.ad.admin_password,
        auto_bind=True
    )

    try:
        # Определяем контейнер (OU). Если OU не существует, создание может не пройти.
        # В идеале здесь должна быть проверка/создание OU.
        ou = f"OU=Users,DC={config.ad.domain.replace('.', ',DC=')}"
        user_dn = f"CN={last_name} {first_name},{ou}"

        # Атрибуты пользователя
        attributes = {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'distinguishedName': user_dn,
            'sAMAccountName': login,
            'userPrincipalName': f"{login}@{config.ad.domain}",
            'givenName': first_name,
            'sn': last_name,
            'displayName': f"{last_name} {first_name}",
            'title': position,
        }

        logger.info(f"Попытка создания пользователя в AD: {user_dn}")

        if not conn.add(user_dn, attributes=attributes):
            raise Exception(f"LDAP Error: {conn.result['description']}")

        # 1. Установка пароля (требует защищенного соединения LDAPS/StartTLS)
        # Генерируем временный пароль или используем стандартный
        temp_password = "TemporaryPassword123!"
        unicode_pass = f'"{temp_password}"'.encode('utf-16-le')
        conn.modify(user_dn, {'unicodePwd': [(MODIFY_REPLACE, [unicode_pass])]})

        # 2. Активация аккаунта (снимаем флаг 'Account Disabled')
        # 512 - Normal Account, 544 - Enabled + Password Not Required (не рекомендуется)
        conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [512])]})

        logger.info(f"✅ AD аккаунт для {login} успешно создан и активирован")

        # Обновляем данные в нашей БД асинхронно через обертку или напрямую
        # Так как create_ad_account вызывается в background_tasks, мы можем сделать это здесь
        import asyncio
        async def sync_db():
            db_conn = await get_db_connection()
            try:
                if employee_id:
                    await add_ad_account_to_employee(db_conn, employee_id, login, ou)
            finally:
                await db_conn.close()

        asyncio.run(sync_db())

        return {"success": True, "dn": user_dn}

    except Exception as e:
        logger.error(f"❌ Ошибка при создании AD аккаунта {login}: {str(e)}")
        if employee_id:
            async def log_error():
                db_conn = await get_db_connection()
                try:
                    await update_ad_account_status(db_conn, employee_id, 'error')
                finally:
                    await db_conn.close()

            asyncio.run(log_error())
        return {"success": False, "error": str(e)}
    finally:
        conn.unbind()