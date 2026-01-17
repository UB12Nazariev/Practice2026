from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from ldap3 import Server, Connection, ALL, Tls
import socket

from api.models import (
    UserCreateRequest,
    UserResponse,
    PositionResponse,
    MailCreateRequest,
    MailResponse,
    EmployeeSearchResponse
)
from services.mail_service import create_mail_account_async
from services.ad_service import create_ad_account
from services.bitwarden_service import create_bitwarden_password
from database.db import (
    search_employees,
    create_employee_record,
    add_mail_to_employee,
    get_employee_by_login,
    get_employee_statistics,
    get_employees_paginated
)
from database.connection import get_db_connection
from config.config import load_config

router = APIRouter()
logger = logging.getLogger(__name__)

# Предопределенные должности
POSITIONS = [
    "DevOps Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Product Manager",
    "QA Engineer",
    "System Administrator",
    "Network Engineer",
    "Security Analyst",
    "Data Scientist",
    "UX/UI Designer",
    "Team Lead",
    "Project Manager",
    "Business Analyst",
    "HR Manager"
]


@router.get("/health", tags=["health"])
async def api_health():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "service": "StaffFlow API",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/positions", response_model=PositionResponse, tags=["positions"])
async def get_positions():
    """Получить список доступных должностей"""
    return PositionResponse(positions=POSITIONS)


@router.get("/stats", tags=["statistics"])
async def get_statistics():
    """Получить статистику системы"""
    try:
        conn = await get_db_connection()
        try:
            stats = await get_employee_statistics(conn)
            stats["last_registration"] = datetime.now().isoformat()
            return stats
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {
            "users_today": 0,
            "users_week": 0,
            "users_total": 0,
            "with_mail": 0,
            "last_registration": datetime.now().isoformat()
        }


@router.get("/search", response_model=List[EmployeeSearchResponse], tags=["employees"])
async def search_employees_endpoint(
        q: str = Query(..., description="Поисковый запрос"),
        limit: int = Query(10, ge=1, le=50)
):
    try:
        conn = await get_db_connection()
        try:
            employees = await search_employees(conn, q, limit)
            return employees
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Ошибка поиска сотрудников: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка поиска сотрудников")


@router.get("/employees", tags=["employees"])
async def get_employees_list(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100)
):
    try:
        offset = (page - 1) * size
        conn = await get_db_connection()
        try:
            data = await get_employees_paginated(conn, size, offset)
            return data
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Ошибка загрузки списка сотрудников: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки данных")


@router.post("/register", response_model=UserResponse, tags=["registration"])
async def register_user(user: UserCreateRequest, background_tasks: BackgroundTasks):
    try:
        login = f"{user.lastName.lower()}.{user.firstName[0].lower()}"

        # Транслитерация
        translit_dict = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z',
            'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
            'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh',
            'щ': 'sch', 'ь': '', 'ы': 'y', 'ъ': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        safe_login = "".join([translit_dict.get(char, char) for char in login])
        login = safe_login
        email = f"{login}@company.ru"

        conn = await get_db_connection()
        try:
            employee_id = await create_employee_record(
                conn=conn,
                last_name=user.lastName,
                first_name=user.firstName,
                middle_name=user.middleName,
                login=login,
                email=email if user.mailRequired else None,
                position=user.position,
                department=user.department or "Не указан"
            )
        finally:
            await conn.close()

        response_data = {
            "status": "processing",
            "login": login,
            "email": email if user.mailRequired else None,
            "message": "Регистрация пользователя начата"
        }

        if user.adRequired:
            background_tasks.add_task(create_ad_account, user.lastName, user.firstName, login, user.position,
                                      employee_id)

        if user.mailRequired:
            background_tasks.add_task(create_mail_account_async, user.lastName, user.firstName, login, user.position,
                                      email, employee_id)

        if user.bitwardenRequired:
            background_tasks.add_task(create_bitwarden_password, login, user.position)

        return UserResponse(**response_data)

    except Exception as e:
        logger.error(f"Ошибка при регистрации: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-mail-only", response_model=MailResponse, tags=["mail"])
async def create_mail_only(mail_request: MailCreateRequest, background_tasks: BackgroundTasks):
    try:
        conn = await get_db_connection()
        employee = None
        try:
            if mail_request.login:
                employee = await get_employee_by_login(conn, mail_request.login)
            if not employee and mail_request.lastName and mail_request.firstName:
                gen_login = f"{mail_request.lastName.lower()}.{mail_request.firstName[0].lower()}"
                employee = await get_employee_by_login(conn, gen_login)
        finally:
            await conn.close()

        domain = mail_request.domain or "company.ru"
        email = f"{mail_request.login}@{domain}"

        if employee:
            conn = await get_db_connection()
            try:
                await add_mail_to_employee(conn, employee["id"], email, mail_request.password)
            finally:
                await conn.close()

        background_tasks.add_task(
            create_mail_account_async,
            mail_request.lastName,
            mail_request.firstName,
            mail_request.login,
            "Не указана",
            email,
            employee["id"] if employee else None,
            mail_request.password
        )

        return MailResponse(
            success=True,
            email=email,
            message="Почтовый ящик создается",
            employee_id=employee["id"] if employee else None
        )

    except Exception as e:
        logger.error(f"Ошибка создания почты: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === ИСПРАВЛЕННЫЙ ЭНДПОИНТ ПРОВЕРКИ ===
@router.get("/test-connections", tags=["system"])
async def test_system_connections():
    """Реальная проверка подключения ко всем системам"""
    results = {
        "database": "unknown",
        "mail_service": "unknown",
        "ad_service": "unknown",
        "timestamp": datetime.now().isoformat()
    }

    config = load_config()

    # 1. Честная проверка БД
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        results["database"] = "connected"
    except Exception as e:
        logger.error(f"DB Check fail: {e}")
        results["database"] = "error"

    # 2. Честная проверка Active Directory (LDAP)
    try:
        # Устанавливаем короткий таймаут, чтобы не вешать API
        server = Server(config.ad.server, get_info=ALL, connect_timeout=3)
        # Пытаемся просто подключиться (без логина, чтобы проверить доступность порта)
        conn_ad = Connection(
            server,
            user=config.ad.admin_user,
            password=config.ad.admin_password,
            auto_bind=True
        )
        results["ad_service"] = "connected"
        conn_ad.unbind()
    except Exception as e:
        logger.error(f"AD Connection fail ({config.ad.server}): {e}")
        results["ad_service"] = "offline"

    # 3. Проверка Mail.ru API (проверяем доступность хоста biz.mail.ru)
    try:
        # Пытаемся разрешить DNS имя или проверить порт 443
        socket.create_connection(("biz.mail.ru", 443), timeout=3)
        if config.mail.api_key and config.mail.api_key != "your_api_key":
            results["mail_service"] = "available"
        else:
            results["mail_service"] = "auth_error (check keys)"
    except Exception:
        results["mail_service"] = "unreachable"

    return results


@router.get("/settings", tags=["system"])
async def get_system_settings():
    """Получить текущие настройки"""
    config = load_config()
    return {
        "mail_domain": "company.ru",
        "ad_domain": config.ad.domain,
        "db_host": config.db.host,
        "log_level": config.log.level
    }


@router.get("/employee/{login}", tags=["employees"])
async def get_employee_details(login: str):
    try:
        conn = await get_db_connection()
        try:
            employee = await get_employee_by_login(conn, login)
            if not employee:
                raise HTTPException(status_code=404, detail="Сотрудник не найден")
            return employee
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка сервера")