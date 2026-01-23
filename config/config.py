from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class DatabaseConfig(BaseSettings):
    host: str = "localhost"
    port: int = "5432"
    name: str = "staffflow"
    user: str = "postgres"
    password: str = "postgres"

    model_config = SettingsConfigDict(
        env_prefix="postgres_",
        extra="ignore"  # Игнорировать лишние переменные окружения
    )


class Bitwarden(BaseSettings):
    organization_id: str = "d7821ae8-b00b-4f7a-a8bf-b3d600f618c3"
    collection_id: str = "ee1b460f-ff68-467d-a361-b3d600f618cc"

    model_config = SettingsConfigDict(
        env_prefix='btw_'
    )


class LoggingConfig(BaseSettings):
    """Конфигурация логирования"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = SettingsConfigDict(
        env_prefix="log_"
    )


class ServerConfig(BaseSettings):
    """Конфигурация сервера"""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True

    model_config = SettingsConfigDict(
        env_prefix="server_"
    )


class MailConfig(BaseSettings):
    """Конфигурация Mail.ru"""
    domain_id: str = "8025776"
    api_url: str = "https://biz.mail.ru/api/v1"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="mail_"
    )


class ADConfig(BaseSettings):
    """Конфигурация Active Directory"""
    server: str = "192.168.76.101"
    domain: str = "testdomain.local"
    admin_user: str = "admin"
    admin_password: str = "SecurePass123"

    model_config = SettingsConfigDict(
        env_prefix="ad_"
    )


class AuthConfig(BaseSettings):
    secret_key: str = "CHANGE_ME_SUPER_SECRET_KEY"
    cookie_name: str = "staffflow_session"

    model_config = SettingsConfigDict(env_prefix="auth_")


class Config(BaseSettings):
    """Основная конфигурация приложения"""
    db: DatabaseConfig = DatabaseConfig()
    log: LoggingConfig = LoggingConfig()
    server: ServerConfig = ServerConfig()
    mail: MailConfig = MailConfig()
    ad: ADConfig = ADConfig()
    btw: Bitwarden = Bitwarden()
    auth: AuthConfig = AuthConfig()

    # Переменные окружения, которые вы видите в ошибке
    postgres_db: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_port: Optional[int] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    pgadmin_default_email: Optional[str] = None
    pgadmin_default_password: Optional[str] = None
    pgadmin_port: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Игнорировать лишние поля в .env
    )


def load_config() -> Config:
    """Загрузить конфигурацию"""
    config = Config()

    # Если в корневом уровне есть postgres_ переменные, используем их
    if config.postgres_db:
        config.db.name = config.postgres_db
    if config.postgres_host:
        config.db.host = config.postgres_host
    if config.postgres_port:
        config.db.port = config.postgres_port
    if config.postgres_user:
        config.db.user = config.postgres_user
    if config.postgres_password:
        config.db.password = config.postgres_password

    return config
