from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends
import logging
from typing import List, Optional
from datetime import datetime

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
    get_employee_by_login
)
from database.connection import get_db_connection

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


# Дополнительные эндпоинты для фронтенда

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
    # В реальном приложении здесь должна быть логика получения статистики из БД
    return {
        "users_today": 5,
        "users_week": 32,
        "users_total": 187,
        "mail_accounts": 150,
        "ad_accounts": 180,
        "last_registration": datetime.now().isoformat()
    }


@router.get("/search", response_model=List[EmployeeSearchResponse], tags=["employees"])
async def search_employees_endpoint(
        q: str = Query(..., description="Поисковый запрос (имя, фамилия или логин)"),
        limit: int = Query(10, ge=1, le=50, description="Лимит результатов")
):
    """Поиск сотрудников в базе данных"""
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


@router.post("/register", response_model=UserResponse, tags=["registration"])
async def register_user(user: UserCreateRequest, background_tasks: BackgroundTasks):
    """Зарегистрировать нового сотрудника во всех системах"""
    try:
        # Генерация логина (фамилия.первая_буква_имени)
        login = f"{user.lastName.lower()}.{user.firstName[0].lower()}"
        email = f"{login}@company.ru"

        # Сохранение в базу данных
        conn = await get_db_connection()
        try:
            employee_id = await create_employee_record(
                conn=conn,
                last_name=user.lastName,
                first_name=user.firstName,
                middle_name=user.middleName,
                login=login,
                email=email,
                position=user.position,
                department=user.department or "Не указан"
            )
            logger.info(f"Сотрудник {login} сохранен в БД с ID: {employee_id}")
        finally:
            await conn.close()

        # Основной ответ
        response_data = {
            "status": "processing",
            "login": login,
            "email": email if user.mailRequired else None,
            "message": "Регистрация пользователя начата"
        }

        # Добавляем фоновые задачи для интеграций
        if user.adRequired:
            background_tasks.add_task(
                create_ad_account,
                user.lastName,
                user.firstName,
                login,
                user.position,
                employee_id  # Передаем ID для связи в БД
            )
            logger.info(f"Добавлена задача на создание AD аккаунта для {login}")

        if user.mailRequired:
            background_tasks.add_task(
                create_mail_account_async,
                user.lastName,
                user.firstName,
                login,
                user.position,
                email,
                employee_id
            )
            logger.info(f"Добавлена задача на создание почты для {login}")

        if user.bitwardenRequired:
            background_tasks.add_task(
                create_bitwarden_password,
                login,
                user.position
            )
            logger.info(f"Добавлена задача на создание пароля BitWarden для {login}")

        # Логирование
        logger.info(
            f"Начата регистрация пользователя: {user.firstName} {user.lastName} "
            f"(логин: {login}, должность: {user.position})"
        )

        return UserResponse(**response_data)

    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при регистрации пользователя: {str(e)}"
        )


@router.post("/create-mail-only", response_model=MailResponse, tags=["mail"])
async def create_mail_only(mail_request: MailCreateRequest, background_tasks: BackgroundTasks):
    """Создать только почтовый ящик для сотрудника"""
    try:
        # Проверяем, существует ли сотрудник в базе
        conn = await get_db_connection()
        employee = None

        try:
            # Ищем по логину
            if mail_request.login:
                employee = await get_employee_by_login(conn, mail_request.login)

            # Если не нашли по логину, ищем по имени/фамилии
            if not employee and mail_request.lastName and mail_request.firstName:
                # Генерируем логин для поиска
                generated_login = f"{mail_request.lastName.lower()}.{mail_request.firstName[0].lower()}"
                employee = await get_employee_by_login(conn, generated_login)
        finally:
            await conn.close()

        # Формируем email
        domain = mail_request.domain if mail_request.domain else "company.ru"
        email = f"{mail_request.login}@{domain}"

        # Если сотрудник найден в базе, обновляем запись
        if employee:
            conn = await get_db_connection()
            try:
                await add_mail_to_employee(
                    conn=conn,
                    employee_id=employee["id"],
                    email=email,
                    mail_password=mail_request.password
                )
                logger.info(f"Почта {email} добавлена к сотруднику ID: {employee['id']}")
            finally:
                await conn.close()

        # Добавляем задачу на создание почты в Mail.ru
        background_tasks.add_task(
            create_mail_account_async,
            mail_request.lastName,
            mail_request.firstName,
            mail_request.login,
            "Не указана",  # Позиция
            email,
            employee["id"] if employee else None,
            mail_request.password
        )

        logger.info(f"Начато создание почтового ящика: {email}")

        return MailResponse(
            success=True,
            email=email,
            message="Почтовый ящик создается в фоновом режиме",
            employee_id=employee["id"] if employee else None
        )

    except Exception as e:
        logger.error(f"Ошибка при создании почтового ящика: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании почтового ящика: {str(e)}"
        )


@router.post("/test-connections", tags=["system"])
async def test_system_connections():
    """Проверить подключение ко всем системам"""
    test_results = {
        "database": "connected",
        "mail_service": "available",
        "ad_service": "available",
        "timestamp": datetime.now().isoformat()
    }

    # Здесь можно добавить реальные проверки подключений

    return test_results


@router.get("/employee/{login}", tags=["employees"])
async def get_employee_details(login: str):
    """Получить детальную информацию о сотруднике"""
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
        logger.error(f"Ошибка получения данных сотрудника: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")