import logging
import ssl
from ldap3 import Server, Connection, MODIFY_REPLACE, MODIFY_ADD, Tls

from config.config import load_config
from core.ad_utils import build_dc
from database.connection import get_db_connection
from database.db import add_ad_account_to_employee, update_ad_account_status
from services.ad_group_resolver import resolve_groups

logger = logging.getLogger(__name__)
config = load_config()


async def create_ad_account(
    last_name: str,
    first_name: str,
    login: str,
    position: str,
    employee_id: int,
    password: str
):
    ad_conn = None
    db_conn = None
    user_dn = None

    try:
        admin_dn = f"{config.ad.admin_user}@{config.ad.domain}"
        dc = build_dc(config.ad.domain)

        server = Server(
            config.ad.server,   # ТОЛЬКО FQDN
            port=636,
            use_ssl=True,
            tls=Tls(
                validate=ssl.CERT_NONE,
                version=ssl.PROTOCOL_TLSv1_2
            )
        )

        ad_conn = Connection(
            server,
            user=admin_dn,
            password=config.ad.admin_password,
            auto_bind=True
        )

        user_dn = f"CN={last_name} {first_name},OU=Employees,{dc}"

        # 1️⃣ Создаём пользователя (disabled)
        ad_conn.add(
            user_dn,
            attributes={
                "objectClass": ["top", "person", "organizationalPerson", "user"],
                "cn": f"{last_name} {first_name}",
                "sn": last_name,
                "givenName": first_name,
                "displayName": f"{last_name} {first_name}",
                "sAMAccountName": login,
                "userPrincipalName": f"{login}@{config.ad.domain}",
                "title": position,
                "userAccountControl": 514,
            }
        )

        if ad_conn.result["description"] != "success":
            raise Exception(ad_conn.result)

        # 2️⃣ Пароль (LDAPS)
        ad_conn.extend.microsoft.modify_password(user_dn, password)

        if ad_conn.result["description"] != "success":
            raise Exception(ad_conn.result)

        # 3️⃣ Активируем
        ad_conn.modify(
            user_dn,
            {"userAccountControl": [(MODIFY_REPLACE, [512])]}
        )

        if ad_conn.result["description"] != "success":
            raise Exception(ad_conn.result)

        # 4️⃣ Группы
        groups = await resolve_groups(position)
        for group_dn in groups:
            ad_conn.modify(group_dn, {
                "member": [(MODIFY_ADD, [user_dn])]
            })

        # 5️⃣ DB
        db_conn = await get_db_connection()
        await add_ad_account_to_employee(
            db_conn,
            employee_id,
            login,
            user_dn,
            "created"
        )

        logger.info(f"✅ AD пользователь создан и активирован: {user_dn}")

    except Exception as e:
        logger.error(f"❌ AD error: {e}")

        if ad_conn and user_dn:
            try:
                ad_conn.delete(user_dn)
            except Exception:
                pass

        if employee_id:
            db_conn = await get_db_connection()
            await update_ad_account_status(db_conn, employee_id, "error")

        raise

    finally:
        if db_conn:
            await db_conn.close()
        if ad_conn:
            ad_conn.unbind()
