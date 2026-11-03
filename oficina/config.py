"""Configuração da aplicação. Valores padrão são exclusivos de desenvolvimento."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://oficina:oficina@localhost:5432/oficina"
    jwt_secret: str = "dev-only-change-me-not-a-real-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_nome: str = "Administrador da Oficina"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
