class StaffFlowError(Exception):
    """Базовое исключение приложения"""
    pass


class MailServiceError(StaffFlowError):
    """Ошибка сервиса Mail.ru"""
    pass


class ADServiceError(StaffFlowError):
    """Ошибка сервиса Active Directory"""
    pass


class DatabaseError(StaffFlowError):
    """Ошибка базы данных"""
    pass


class ValidationError(StaffFlowError):
    """Ошибка валидации данных"""
    pass
