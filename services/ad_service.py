import logging
import asyncio
from typing import Dict, Any, Optional

from ldap3 import (
    Server, Connection, ALL,
    MODIFY_REPLACE, MODIFY_ADD
)

from config.config import load_config
from database.connection import get_db_connection
from database.db import (
    add_ad_account_to_employee,
    update_ad_account_status
)
from services.ad_group_resolver import resolve_groups

logger = logging.getLogger(__name__)
config = load_config()


def build_dc(domain: str) -> str:
    return "DC=" + ",DC=".join(domain.split("."))


def delete_ad_user(conn: Connection, user_dn: str):
    if conn.delete(user_dn):
        logger.warning(f"♻️ Rollback: пользователь {user_dn} удалён")
    else:
        logger.error(f"❌ Rollback не удался: {conn.result}")


def create_ad_account(
    last_name: str,
    first_name: str,
    login: str,
    position: str,
    employee_id: Optional[int] = None
) -> Dict[str, Any]:

    server = Server(config.ad.server, get_info=ALL)
    admin_dn = f"{config.ad.admin_user}@{config.ad.domain}"

    conn = Connection(
        server,
        user=admin_dn,
        password=config.ad.admin_password,
        auto_bind=True
    )

    dc = build_dc(config.ad.domain)
    user_ou = f"OU=Employees,{dc}"
    user_dn = f"CN={last_name} {first_name},{user_ou}"

    try:
        # 1️⃣ Создание пользователя
        if not conn.add(user_dn, attributes={
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "sAMAccountName": login,
            "userPrincipalName": f"{login}@{config.ad.domain}",
            "givenName": first_name,
            "sn": last_name,
            "displayName": f"{last_name} {first_name}",
            "title": position
        }):
            raise Exception(conn.result)

        # 2️⃣ Пароль + enable
        pwd = '"TemporaryPassword123!"'.encode("utf-16-le")
        conn.modify(user_dn, {"unicodePwd": [(MODIFY_REPLACE, [pwd])]})
        conn.modify(user_dn, {"userAccountControl": [(MODIFY_REPLACE, [512])]})

        # 3️⃣ Группы (position)
        groups = asyncio.run(resolve_groups(position))

        for group in groups:
            conn.search(dc, f"(cn={group})", attributes=["distinguishedName"])
            if not conn.entries:
                raise Exception(f"Группа {group} не найдена")

            conn.modify(
                conn.entries[0].entry_dn,
                {"member": [(MODIFY_ADD, [user_dn])]}
            )

        # 4️⃣ DB
        async def sync_db():
            db = await get_db_connection()
            try:
                await add_ad_account_to_employee(
                    db, employee_id, login, user_ou, "created"
                )
            finally:
                await db.close()

        asyncio.run(sync_db())

        return {"success": True, "groups": groups}

    except Exception as e:
        logger.error(f"❌ AD error: {e}")
        delete_ad_user(conn, user_dn)

        async def mark_error():
            db = await get_db_connection()
            try:
                await update_ad_account_status(db, employee_id, "error")
            finally:
                await db.close()

        asyncio.run(mark_error())
        return {"success": False, "error": str(e)}

    finally:
        conn.unbind()
