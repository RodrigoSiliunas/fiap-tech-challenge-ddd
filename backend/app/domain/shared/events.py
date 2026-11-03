"""Evento de domínio — fato ocorrido, nome no passado, imutável."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from uuid import UUID

from oficina.domain.shared.clock import now


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    agregado_id: UUID
    ocorrido_em: datetime = field(default_factory=now)
    agregado_tipo: ClassVar[str] = "Desconhecido"

    @property
    def nome_evento(self) -> str:
        return type(self).__name__
