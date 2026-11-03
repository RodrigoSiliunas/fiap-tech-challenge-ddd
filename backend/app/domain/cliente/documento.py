"""Objeto de valor Documento — CPF ou CNPJ validado e imutável."""

import re
from dataclasses import dataclass
from enum import Enum

from oficina.domain.exceptions import DomainError


class TipoDocumento(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


def _cpf_valido(digitos: str) -> bool:
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * ((tamanho + 1) - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(digitos[tamanho]):
            return False
    return True


def _cnpj_valido(digitos: str) -> bool:
    if len(digitos) != 14 or digitos == digitos[0] * 14:
        return False
    pesos_primeiro = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    pesos_segundo = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)

    def calcular(base: str, pesos: tuple[int, ...]) -> int:
        soma = sum(int(numero) * peso for numero, peso in zip(base, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    primeiro = calcular(digitos[:12], pesos_primeiro)
    segundo = calcular(digitos[:13], pesos_segundo)
    return primeiro == int(digitos[12]) and segundo == int(digitos[13])


@dataclass(frozen=True)
class Documento:
    valor: str
    tipo: TipoDocumento

    def __post_init__(self) -> None:
        if self.tipo == TipoDocumento.CPF and not _cpf_valido(self.valor):
            raise DomainError("CPF inválido", "documento_invalido")
        if self.tipo == TipoDocumento.CNPJ and not _cnpj_valido(self.valor):
            raise DomainError("CNPJ inválido", "documento_invalido")

    @staticmethod
    def criar(bruto: str) -> "Documento":
        if bruto is None or not str(bruto).strip():
            raise DomainError("CPF ou CNPJ é obrigatório", "documento_invalido")
        digitos = re.sub(r"\D", "", str(bruto))
        if len(digitos) == 11 and _cpf_valido(digitos):
            return Documento(digitos, TipoDocumento.CPF)
        if len(digitos) == 14 and _cnpj_valido(digitos):
            return Documento(digitos, TipoDocumento.CNPJ)
        raise DomainError(
            "Documento inválido. Informe um CPF ou CNPJ válido.",
            "documento_invalido",
        )

    def formatado(self) -> str:
        if self.tipo == TipoDocumento.CPF:
            d = self.valor
            return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"
        d = self.valor
        return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"
