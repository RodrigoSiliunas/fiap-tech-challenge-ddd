from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

from oficina.domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ClienteCadastrado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Cliente"
    nome: str
    documento: str


@dataclass(frozen=True, kw_only=True)
class ClienteIdentificado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Cliente"
    documento: str


@dataclass(frozen=True, kw_only=True)
class ClienteAtualizado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Cliente"
    nome: str
