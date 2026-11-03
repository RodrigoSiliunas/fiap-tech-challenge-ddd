"""Configuração da aplicação. Valores padrão são exclusivos de desenvolvimento."""

import secrets
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://oficina:oficina@localhost:5432/oficina"
    # Sem JWT_SECRET, cada subida da API gera o seu segredo: nenhum segredo fica no
    # repositório, e os tokens emitidos valem até a API reiniciar.
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_nome: str = "Administrador da Oficina"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
