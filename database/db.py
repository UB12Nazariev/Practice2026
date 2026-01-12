import asyncpg
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def create_tables():
    """Создать необходимые таблицы в БД"""
    conn = None
    try:
        from database.connection import get_db_connection
        conn = await get_db_connection()

        # Таблица сотрудников
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                last_name VARCHAR(100) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                middle_name VARCHAR(100),
                login VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE,
                position VARCHAR(200),
                department VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица почтовых аккаунтов
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_mail_accounts (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
                email VARCHAR(255) UNIQUE NOT NULL,
                mail_password VARCHAR(255),
                mail_user_id VARCHAR(100),
                status VARCHAR(50) DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица AD аккаунтов
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_ad_accounts (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
                ad_login VARCHAR(100) UNIQUE NOT NULL,
                ad_ou VARCHAR(500),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица логов операций
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
                operation_type VARCHAR(100) NOT NULL,
                service VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                message TEXT,
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Индексы для быстрого поиска
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_employees_name 
            ON employees(last_name, first_name)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_employees_login 
            ON employees(login)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_employees_email 
            ON employees(email)
        """)

        logger.info("✅ Таблицы БД созданы/проверены")

    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {str(e)}")
        raise
    finally:
        if conn:
            from database.connection import release_connection
            await release_connection(conn)


async def create_employee_record(
        conn: asyncpg.Connection,
        last_name: str,
        first_name: str,
        middle_name: Optional[str],
        login: str,
        email: Optional[str],
        position: str,
        department: str
) -> int:
    """Создать запись сотрудника в базе данных"""
    try:
        employee_id = await conn.fetchval("""
            INSERT INTO employees 
            (last_name, first_name, middle_name, login, email, position, department)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, last_name, first_name, middle_name, login, email, position, department)

        logger.info(f"Сотрудник {login} добавлен в БД (ID: {employee_id})")

        # Логируем операцию
        await conn.execute("""
            INSERT INTO operation_logs 
            (employee_id, operation_type, service, status, message)
            VALUES ($1, $2, $3, $4, $5)
        """, employee_id, "create_employee", "database", "success", "Сотрудник создан в БД")

        return employee_id

    except asyncpg.UniqueViolationError as e:
        logger.error(f"Сотрудник с логином {login} уже существует")
        raise ValueError(f"Сотрудник с логином {login} уже существует")
    except Exception as e:
        logger.error(f"Ошибка при добавлении сотрудника в БД: {str(e)}")
        raise


async def search_employees(
        conn: asyncpg.Connection,
        query: str,
        limit: int = 10
) -> List[Dict[str, Any]]:
    """Поиск сотрудников по имени, фамилии или логину"""
    try:
        # Используем ILIKE для регистронезависимого поиска
        search_pattern = f"%{query}%"

        rows = await conn.fetch("""
            SELECT 
                e.id,
                e.last_name,
                e.first_name,
                e.middle_name,
                e.login,
                e.email,
                e.position,
                e.department,
                e.created_at,
                CASE WHEN em.email IS NOT NULL THEN true ELSE false END as has_mail
            FROM employees e
            LEFT JOIN employee_mail_accounts em ON e.id = em.employee_id
            WHERE 
                e.last_name ILIKE $1 OR
                e.first_name ILIKE $1 OR
                e.login ILIKE $1 OR
                e.email ILIKE $1
            ORDER BY e.last_name, e.first_name
            LIMIT $2
        """, search_pattern, limit)

        employees = []
        for row in rows:
            employees.append({
                "id": row["id"],
                "lastName": row["last_name"],
                "firstName": row["first_name"],
                "middleName": row["middle_name"],
                "login": row["login"],
                "email": row["email"],
                "position": row["position"],
                "department": row["department"],
                "has_mail": row["has_mail"],
                "created_at": row["created_at"]
            })

        logger.info(f"Найдено {len(employees)} сотрудников по запросу '{query}'")
        return employees

    except Exception as e:
        logger.error(f"Ошибка поиска сотрудников: {str(e)}")
        raise


async def get_employee_by_login(conn: asyncpg.Connection, login: str) -> Optional[Dict[str, Any]]:
    """Получить сотрудника по логину"""
    try:
        row = await conn.fetchrow("""
            SELECT 
                e.id,
                e.last_name,
                e.first_name,
                e.middle_name,
                e.login,
                e.email,
                e.position,
                e.department,
                e.created_at,
                CASE WHEN em.email IS NOT NULL THEN true ELSE false END as has_mail
            FROM employees e
            LEFT JOIN employee_mail_accounts em ON e.id = em.employee_id
            WHERE e.login = $1
        """, login)

        if row:
            return {
                "id": row["id"],
                "lastName": row["last_name"],
                "firstName": row["first_name"],
                "middleName": row["middle_name"],
                "login": row["login"],
                "email": row["email"],
                "position": row["position"],
                "department": row["department"],
                "has_mail": row["has_mail"],
                "created_at": row["created_at"]
            }

        return None

    except Exception as e:
        logger.error(f"Ошибка получения сотрудника по логину {login}: {str(e)}")
        raise


async def add_mail_to_employee(
        conn: asyncpg.Connection,
        employee_id: int,
        email: str,
        mail_password: str,
        mail_user_id: Optional[str] = None,
        status: str = "created"
) -> int:
    """Добавить почтовый аккаунт к сотруднику"""
    try:
        mail_account_id = await conn.fetchval("""
            INSERT INTO employee_mail_accounts 
            (employee_id, email, mail_password, mail_user_id, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, employee_id, email, mail_password, mail_user_id, status)

        # Обновляем email в основной таблице сотрудников
        await conn.execute("""
            UPDATE employees 
            SET email = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, email, employee_id)

        # Логируем операцию
        await conn.execute("""
            INSERT INTO operation_logs 
            (employee_id, operation_type, service, status, message)
            VALUES ($1, $2, $3, $4, $5)
        """, employee_id, "add_mail", "mail.ru", "success", f"Почтовый ящик {email} создан")

        logger.info(f"Почтовый аккаунт {email} добавлен к сотруднику ID: {employee_id}")
        return mail_account_id

    except asyncpg.UniqueViolationError as e:
        logger.error(f"Почтовый ящик {email} уже существует")
        raise ValueError(f"Почтовый ящик {email} уже существует")
    except Exception as e:
        logger.error(f"Ошибка добавления почтового аккаунта: {str(e)}")
        raise


async def update_employee_mail_status(
        conn: asyncpg.Connection,
        employee_id: int,
        status: str,
        error_message: Optional[str] = None
) -> None:
    """Обновить статус почтового аккаунта сотрудника"""
    try:
        await conn.execute("""
            UPDATE employee_mail_accounts 
            SET status = $1, 
                error_message = $2,
                updated_at = CURRENT_TIMESTAMP
            WHERE employee_id = $3
        """, status, error_message, employee_id)

        # Логируем операцию
        log_status = "error" if status == "error" else "success"
        await conn.execute("""
            INSERT INTO operation_logs 
            (employee_id, operation_type, service, status, message)
            VALUES ($1, $2, $3, $4, $5)
        """, employee_id, "update_mail_status", "mail.ru", log_status,
                           f"Статус почты обновлен: {status}")

        logger.info(f"Статус почты сотрудника ID:{employee_id} обновлен на '{status}'")

    except Exception as e:
        logger.error(f"Ошибка обновления статуса почты: {str(e)}")
        raise


async def get_employee_statistics(conn: asyncpg.Connection) -> Dict[str, Any]:
    """Получить статистику по сотрудникам"""
    try:
        # Общее количество сотрудников
        total = await conn.fetchval("SELECT COUNT(*) FROM employees")

        # Сотрудники с почтой
        with_mail = await conn.fetchval("""
            SELECT COUNT(DISTINCT employee_id) FROM employee_mail_accounts 
            WHERE status = 'created'
        """)

        # Сегодняшние регистрации
        today = await conn.fetchval("""
            SELECT COUNT(*) FROM employees 
            WHERE DATE(created_at) = CURRENT_DATE
        """)

        # Регистрации за неделю
        week = await conn.fetchval("""
            SELECT COUNT(*) FROM employees 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)

        return {
            "total": total,
            "with_mail": with_mail,
            "today": today,
            "week": week
        }

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {str(e)}")
        raise