"""Converte eventos de domínio em JSON persistível."""

from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from app.domain.shared.events import DomainEvent


def _jsonable(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(chave): _jsonable(item) for chave, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def evento_payload(evento: DomainEvent) -> dict:
    return _jsonable(asdict(evento))  # type: ignore[return-value]
