from dataclasses import dataclass
from typing import ClassVar

from oficina.domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ServicoCatalogoCadastrado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Servico"
    nome: str
    preco_centavos: int


@dataclass(frozen=True, kw_only=True)
class ServicoCatalogoAtualizado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Servico"
    nome: str
    preco_centavos: int
