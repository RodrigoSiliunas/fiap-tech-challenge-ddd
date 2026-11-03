"""Funções comuns dos casos de uso."""

from oficina.domain.exceptions import DomainError
from oficina.domain.shared.aggregate import RaizAgregado


def paginar(limite: int, offset: int) -> tuple[int, int]:
    if limite < 1 or limite > 100:
        raise DomainError("Limite deve estar entre 1 e 100", "validacao")
    if offset < 0:
        raise DomainError("Offset inválido", "validacao")
    return limite, offset


def exigir(entidade, mensagem: str):
    if entidade is None:
        raise DomainError(mensagem, "nao_encontrado")
    return entidade


def concluir(uow, *agregados: RaizAgregado) -> None:
    eventos = []
    for agregado in agregados:
        eventos.extend(agregado.pull_events())
    uow.eventos.salvar_todos(eventos)
    uow.commit()
