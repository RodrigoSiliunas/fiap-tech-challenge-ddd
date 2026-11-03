from dataclasses import dataclass
from typing import ClassVar

from oficina.domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class VeiculoRegistrado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Veiculo"
    cliente_id: str
    placa: str
    marca: str
    modelo: str
    ano: int


@dataclass(frozen=True, kw_only=True)
class VeiculoAtualizado(DomainEvent):
    agregado_tipo: ClassVar[str] = "Veiculo"
    marca: str
    modelo: str
    ano: int
