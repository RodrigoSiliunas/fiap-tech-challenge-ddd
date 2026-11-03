"""Emissão e validação de JWT (HS256) para as APIs administrativas."""

from datetime import timedelta

import jwt

from app.config import get_settings
from app.domain.exceptions import DomainError
from app.domain.shared.clock import now


def create_token(username: str, nome: str) -> str:
    settings = get_settings()
    instante = now()
    payload = {
        "sub": username,
        "nome": nome,
        "papel": "ADMIN",
        "iat": instante,
        "exp": instante + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise DomainError("Token inválido ou expirado", "nao_autenticado") from exc
