"""Validações de texto usadas por mais de um agregado."""

import re

from app.domain.exceptions import DomainError

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_nome(nome: str | None, rotulo: str = "Nome", minimo: int = 2, maximo: int = 200) -> str:
    if nome is None or not str(nome).strip():
        raise DomainError(f"{rotulo} é obrigatório", "validacao")
    limpo = " ".join(str(nome).split())
    if len(limpo) < minimo or len(limpo) > maximo:
        raise DomainError(f"{rotulo} deve ter entre {minimo} e {maximo} caracteres", "validacao")
    return limpo


def validar_texto_opcional(valor: str | None, rotulo: str, maximo: int) -> str | None:
    if valor is None:
        return None
    limpo = valor.strip()
    if not limpo:
        return None
    if len(limpo) > maximo:
        raise DomainError(f"{rotulo} excede {maximo} caracteres", "validacao")
    return limpo


def validar_email(valor: str | None) -> str | None:
    if valor is None or not valor.strip():
        return None
    email = valor.strip().lower()
    if len(email) > 200 or not _EMAIL.match(email):
        raise DomainError("E-mail inválido", "validacao")
    return email


def validar_telefone(valor: str | None) -> str | None:
    if valor is None or not valor.strip():
        return None
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) < 10 or len(digitos) > 13:
        raise DomainError("Telefone inválido", "validacao")
    return digitos


def validar_ano(ano: int) -> int:
    from app.domain.shared.clock import now

    if isinstance(ano, bool) or not isinstance(ano, int):
        raise DomainError("Ano do veículo inválido", "validacao")
    if ano < 1900 or ano > now().year + 1:
        raise DomainError("Ano do veículo fora do intervalo aceito", "validacao")
    return ano
