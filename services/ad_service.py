import logging
from typing import Dict, Any, Optional
from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, MODIFY_ADD, SUBTREE
from config.config import load_config
from database.connection import get_db_connection
from database.db import add_ad_account_to_employee, update_ad_account_status

logger = logging.getLogger(__name__)
config = load_config()

# Карта соответствия должностей и групп AD
# Ключ: должность из API, Значение: Имя группы в AD
POSITION_GROUPS = {
    "DevOps Engineer": "IT_DevOps_Group",
    "Backend Developer": "IT_Developers_Group",
    "Frontend Developer": "IT_Developers_Group",
    "System Administrator": "IT_Admins_Group",
    "HR Manager": "HR_Department_Group",
    # Добавьте остальные должности по аналогии
}


def create_ad_account(
        last_name: str,
        first_name: str,
        login: str,
        position: str,
        employee_id: Optional[int] = None
) -> Dict[str, Any]:
    """Создать учетную запись в AD и добавить в группы по должности"""
    server = Server(config.ad.server, get_info=ALL)
    admin_dn = f"{config.ad.admin_user}@{config.ad.domain}"

    conn = Connection(
        server,
        user=admin_dn,
        password=config.ad.admin_password,
        auto_bind=True
    )

    try:
        # 1. Создание пользователя
        ou = f"OU=Users,DC={config.ad.domain.replace('.', ',DC=')}"
        user_dn = f"CN={last_name} {first_name},{ou}"

        attributes = {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'sAMAccountName': login,
            'userPrincipalName': f"{login}@{config.ad.domain}",
            'givenName': first_name,
            'sn': last_name,
            'displayName': f"{last_name} {first_name}",
            'title': position,
        }

        if not conn.add(user_dn, attributes=attributes):
            raise Exception(f"LDAP Create Error: {conn.result['description']}")

        # 2. Установка пароля и активация (требуется LDAPS)
        temp_password = "TemporaryPassword123!"
        unicode_pass = f'"{temp_password}"'.encode('utf-16-le')
        conn.modify(user_dn, {'unicodePwd': [(MODIFY_REPLACE, [unicode_pass])]})
        conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [512])]})

        # 3. ДОБАВЛЕНИЕ В ГРУППУ ПО ДОЛЖНОСТИ
        target_group_name = POSITION_GROUPS.get(position)
        if target_group_name:
            # Поиск DN группы по имени
            search_base = f"DC={config.ad.domain.replace('.', ',DC=')}"
            conn.search(search_base, f'(&(objectClass=group)(cn={target_group_name}))',
                        attributes=['distinguishedName'])

            if conn.entries:
                group_dn = conn.entries[0].entry_dn
                # Добавление пользователя в группу
                conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]})
                logger.info(f"✅ Пользователь {login} добавлен в группу {target_group_name}")
            else:
                logger.warning(f"⚠️ Группа {target_group_name} не найдена в AD")
        else:
            logger.info(f"ℹ️ Для должности {position} не настроены группы AD")

        # 4. Обновление БД (код остается прежним)
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
        logger.error(f"❌ Ошибка AD для {login}: {str(e)}")
        # ... (логика обработки ошибок в БД)
        return {"success": False, "error": str(e)}
    finally:
        conn.unbind()