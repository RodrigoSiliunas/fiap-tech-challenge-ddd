from dataclasses import dataclass
from typing import ClassVar

from app.domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class PecaCadastrada(DomainEvent):
    agregado_tipo: ClassVar[str] = "Peca"
    nome: str
    preco_centavos: int
    quantidade_estoque: int


@dataclass(frozen=True, kw_only=True)
class PecaAtualizada(DomainEvent):
    agregado_tipo: ClassVar[str] = "Peca"
    nome: str
    preco_centavos: int


@dataclass(frozen=True, kw_only=True)
class EstoqueIncrementado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Peca"
    quantidade: int
    saldo: int


@dataclass(frozen=True, kw_only=True)
class EstoqueAjustado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Peca"
    saldo: int


@dataclass(frozen=True, kw_only=True)
class EstoqueDecrementado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Peca"
    quantidade: int
    saldo: int
