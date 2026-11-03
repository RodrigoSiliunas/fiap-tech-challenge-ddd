"""Objetos de valor transversais: Dinheiro e Quantidade."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from oficina.domain.exceptions import DomainError


def _inteiro(valor: object, mensagem: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise DomainError(mensagem, "validacao")
    return valor


@dataclass(frozen=True)
class Dinheiro:
    """Valor monetário em centavos. Imutável; igualdade por valor. Moeda BRL."""

    centavos: int
    moeda: str = "BRL"

    def __post_init__(self) -> None:
        centavos = _inteiro(self.centavos, "Valor monetário inválido")
        if centavos < 0:
            raise DomainError("Valor monetário não pode ser negativo", "dinheiro_invalido")
        if self.moeda != "BRL":
            raise DomainError("Moeda não suportada", "moeda_invalida")
        object.__setattr__(self, "centavos", centavos)

    @classmethod
    def zero(cls) -> "Dinheiro":
        return cls(0)

    @classmethod
    def de_decimal(cls, valor: Decimal | int | str) -> "Dinheiro":
        if isinstance(valor, float):
            raise DomainError("Informe o valor como decimal, sem ponto flutuante", "dinheiro_invalido")
        decimal = valor if isinstance(valor, Decimal) else Decimal(str(valor))
        if decimal < 0:
            raise DomainError("Valor monetário não pode ser negativo", "dinheiro_invalido")
        centavos = int((decimal * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return cls(centavos)

    def para_decimal(self) -> Decimal:
        return (Decimal(self.centavos) / Decimal("100")).quantize(Decimal("0.01"))

    def formatado(self) -> str:
        return f"{self.para_decimal():.2f}"

    def somar(self, outro: "Dinheiro") -> "Dinheiro":
        if outro.moeda != self.moeda:
            raise DomainError("Não é possível somar moedas diferentes", "moeda_invalida")
        return Dinheiro(self.centavos + outro.centavos, self.moeda)

    def multiplicar(self, fator: int) -> "Dinheiro":
        fator = _inteiro(fator, "Fator de multiplicação inválido")
        if fator < 0:
            raise DomainError("Fator de multiplicação não pode ser negativo", "dinheiro_invalido")
        return Dinheiro(self.centavos * fator, self.moeda)


def somar_dinheiros(valores: list[Dinheiro]) -> Dinheiro:
    total = Dinheiro.zero()
    for valor in valores:
        total = total.somar(valor)
    return total


@dataclass(frozen=True)
class Quantidade:
    """Unidades inteiras não negativas. Estoque pode ser zero; item de OS usa `positiva`."""

    valor: int

    def __post_init__(self) -> None:
        valor = _inteiro(self.valor, "Quantidade inválida")
        if valor < 0:
            raise DomainError("Quantidade não pode ser negativa", "quantidade_invalida")
        object.__setattr__(self, "valor", valor)

    @classmethod
    def positiva(cls, valor: int) -> "Quantidade":
        quantidade = cls(valor)
        if quantidade.valor <= 0:
            raise DomainError("Quantidade deve ser maior que zero", "quantidade_invalida")
        return quantidade
