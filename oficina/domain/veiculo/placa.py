"""Objeto de valor Placa — padrão antigo (ABC1234) ou Mercosul (ABC1D23)."""

import re
from dataclasses import dataclass
from enum import Enum

from oficina.domain.exceptions import DomainError

_ANTIGA = re.compile(r"^[A-Z]{3}[0-9]{4}$")
_MERCOSUL = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")


class PadraoPlaca(str, Enum):
    ANTIGA = "ANTIGA"
    MERCOSUL = "MERCOSUL"


@dataclass(frozen=True)
class Placa:
    valor: str
    padrao: PadraoPlaca

    def __post_init__(self) -> None:
        if self.padrao == PadraoPlaca.ANTIGA and not _ANTIGA.match(self.valor):
            raise DomainError("Placa inválida", "placa_invalida")
        if self.padrao == PadraoPlaca.MERCOSUL and not _MERCOSUL.match(self.valor):
            raise DomainError("Placa inválida", "placa_invalida")

    @staticmethod
    def criar(bruto: str) -> "Placa":
        if bruto is None or not str(bruto).strip():
            raise DomainError("Placa é obrigatória", "placa_invalida")
        normalizada = re.sub(r"[^A-Za-z0-9]", "", str(bruto)).upper()
        if _ANTIGA.match(normalizada):
            return Placa(normalizada, PadraoPlaca.ANTIGA)
        if _MERCOSUL.match(normalizada):
            return Placa(normalizada, PadraoPlaca.MERCOSUL)
        raise DomainError(
            "Placa inválida. Use o padrão antigo (ABC1234) ou Mercosul (ABC1D23).",
            "placa_invalida",
        )

    def formatada(self) -> str:
        if self.padrao == PadraoPlaca.ANTIGA:
            return f"{self.valor[:3]}-{self.valor[3:]}"
        return self.valor
