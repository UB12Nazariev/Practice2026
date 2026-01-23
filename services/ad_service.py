import logging
import asyncio
from typing import Dict, Any, Optional

from ldap3 import (
    Server, Connection, ALL,
    MODIFY_REPLACE, MODIFY_ADD
)

from config.config import load_config
from core.ad_utils import build_dc
from database.connection import get_db_connection
from database.db import (
    add_ad_account_to_employee,
    update_ad_account_status
)
from services.ad_group_resolver import resolve_groups

logger = logging.getLogger(__name__)
config = load_config()

def delete_ad_user(conn: Connection, user_dn: str):
    if conn.delete(user_dn):
        logger.warning(f"♻️ Rollback: пользователь {user_dn} удалён")
    else:
        logger.error(f"❌ Rollback не удался: {conn.result}")

logger = logging.getLogger(__name__)

async def create_ad_account(
    last_name: str,
    first_name: str,
    login: str,
    position: str,
    employee_id: int
):
    ad_conn = None
    db_conn = None
    user_dn = None

    try:
        admin_dn = f"{config.ad.admin_user}@{config.ad.domain}"

        ad_conn = Connection(
            config.ad.server,
            user=admin_dn,
            password=config.ad.admin_password,
            auto_bind=True
        )

        dc = build_dc(config.ad.domain)
        user_dn = f"CN={last_name} {first_name},OU=Employees,{dc}"

        ad_conn.add(
            user_dn,
            attributes={
                "objectClass": ["top", "person", "organizationalPerson", "user"],
                "cn": f"{last_name} {first_name}",
                "sn": last_name,
                "givenName": first_name,
                "sAMAccountName": login,
                "userPrincipalName": f"{login}@{config.ad.domain}",
                "displayName": f"{last_name} {first_name}",
                "title": position,
            }
        )

        if ad_conn.result["description"] != "success":
            raise Exception(ad_conn.result)

        logger.info(f"✅ AD пользователь создан: {user_dn}")

        groups = await resolve_groups(position)
        for group_dn in groups:
            ad_conn.modify(group_dn, {
                "member": [(MODIFY_ADD, [user_dn])]
            })

        db_conn = await get_db_connection()
        await add_ad_account_to_employee(
            db_conn,
            employee_id,
            login,
            user_dn,
            "created"
        )

    except Exception as e:
        logger.error(f"❌ AD error: {e}")

        if ad_conn and user_dn:
            ad_conn.delete(user_dn)

        if employee_id:
            db_conn = await get_db_connection()
            await update_ad_account_status(db_conn, employee_id, "error")

        raise

    finally:
        if db_conn:
            await db_conn.close()
        if ad_conn:
            ad_conn.unbind()