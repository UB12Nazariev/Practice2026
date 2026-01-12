from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserCreateRequest(BaseModel):
    """Модель для создания пользователя"""
    lastName: str = Field(..., min_length=2, max_length=50, description="Фамилия")
    firstName: str = Field(..., min_length=2, max_length=50, description="Имя")
    middleName: Optional[str] = Field(None, max_length=50, description="Отчество")
    position: str = Field(..., min_length=2, max_length=100, description="Должность")
    department: Optional[str] = Field(None, max_length=100, description="Отдел")
    adRequired: bool = Field(True, description="Создать учетную запись в AD")
    mailRequired: bool = Field(True, description="Создать почтовый ящик")
    bitwardenRequired: bool = Field(True, description="Создать пароль в BitWarden")


class MailCreateRequest(BaseModel):
    """Модель для создания только почтового ящика"""
    lastName: str = Field(..., min_length=2, max_length=50, description="Фамилия")
    firstName: str = Field(..., min_length=2, max_length=50, description="Имя")
    login: str = Field(..., min_length=3, max_length=50, description="Логин для почты")
    password: str = Field(..., min_length=8, max_length=100, description="Пароль")
    domain: Optional[str] = Field("company.ru", description="Домен для почты")
    employee_id: Optional[int] = Field(None, description="ID сотрудника в БД (если есть)")


class UserResponse(BaseModel):
    """Модель ответа с данными пользователя"""
    status: str
    login: str
    email: Optional[str] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class MailResponse(BaseModel):
    """Модель ответа для создания почты"""
    success: bool
    email: str
    message: str
    employee_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PositionResponse(BaseModel):
    """Модель ответа со списком должностей"""
    positions: List[str]


class EmployeeSearchResponse(BaseModel):
    """Модель ответа для поиска сотрудников"""
    id: int
    lastName: str
    firstName: str
    middleName: Optional[str]
    login: str
    email: Optional[str]
    position: Optional[str]
    department: Optional[str]
    has_mail: bool = False
    created_at: datetime


class SystemStatus(BaseModel):
    """Модель статуса системы"""
    service: str
    status: str
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
