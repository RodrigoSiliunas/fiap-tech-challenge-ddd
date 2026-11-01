from dataclasses import dataclass
from typing import ClassVar

from oficina.domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrdemDeServicoRecebida(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    numero: int
    cliente_id: str
    veiculo_id: str


@dataclass(frozen=True, kw_only=True)
class DiagnosticoIniciado(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"


@dataclass(frozen=True, kw_only=True)
class ServicosIncluidos(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    item_id: str
    servico_id: str


@dataclass(frozen=True, kw_only=True)
class ItemServicoRemovido(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    item_id: str


@dataclass(frozen=True, kw_only=True)
class PecasIncluidas(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    item_id: str
    peca_id: str
    quantidade: int


@dataclass(frozen=True, kw_only=True)
class ItemPecaRemovido(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    item_id: str


@dataclass(frozen=True, kw_only=True)
class OrcamentoGerado(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    valor_total_centavos: int


@dataclass(frozen=True, kw_only=True)
class OrcamentoDisponibilizado(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    valor_total_centavos: int


@dataclass(frozen=True, kw_only=True)
class OrcamentoAprovado(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    valor_total_centavos: int


@dataclass(frozen=True, kw_only=True)
class OrcamentoRejeitado(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
    motivo: str | None


@dataclass(frozen=True, kw_only=True)
class ExecucaoIniciada(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"


@dataclass(frozen=True, kw_only=True)
class ServicoFinalizado(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"


@dataclass(frozen=True, kw_only=True)
class VeiculoEntregue(DomainEvent):
    agregado_tipo: ClassVar[str] = "OrdemDeServico"
