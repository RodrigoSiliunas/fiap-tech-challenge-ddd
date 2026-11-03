"""Dados de demonstração. Senha e catálogo existem só para o ambiente local."""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from oficina.config import get_settings
from oficina.domain.peca.aggregate import Peca
from oficina.domain.servico.aggregate import Servico
from oficina.domain.shared.value_objects import Dinheiro, Quantidade
from oficina.infrastructure.auth.passwords import hash_password
from oficina.infrastructure.db.models import SequenciaModel, ServicoModel, UsuarioModel
from oficina.infrastructure.db.repositories import (
    EventoRepository,
    SqlAlchemyPecaRepository,
    SqlAlchemyServicoRepository,
    flush,
)


def seed(session: Session, password_hash: str | None = None, catalogo: bool = True) -> None:
    garantir_sequencia(session)
    seed_admin(session, password_hash)
    if catalogo:
        seed_catalogo(session)


def garantir_sequencia(session: Session) -> None:
    if session.get(SequenciaModel, "ordem_servico") is None:
        session.add(SequenciaModel(nome="ordem_servico", valor=0))
        flush(session)


def seed_admin(session: Session, password_hash: str | None = None) -> None:
    settings = get_settings()
    existente = session.query(UsuarioModel).filter(UsuarioModel.username == settings.admin_username).one_or_none()
    if existente is not None:
        return
    session.add(
        UsuarioModel(
            id=str(uuid4()),
            username=settings.admin_username,
            password_hash=password_hash or hash_password(settings.admin_password),
            nome=settings.admin_nome,
        )
    )
    flush(session)


def seed_catalogo(session: Session) -> None:
    if session.query(ServicoModel).count() > 0:
        return
    servicos = SqlAlchemyServicoRepository(session)
    pecas = SqlAlchemyPecaRepository(session)
    eventos = EventoRepository(session)
    catalogo_servicos = [
        ("Troca de óleo", "150.00", "Troca de óleo do motor e anel de vedação"),
        ("Alinhamento", "120.00", "Alinhamento computadorizado"),
        ("Balanceamento", "80.00", "Balanceamento das quatro rodas"),
    ]
    catalogo_pecas = [
        ("Óleo 5W30", "45.00", 20, "Lubrificante sintético"),
        ("Filtro de óleo", "35.00", 20, "Filtro do motor"),
        ("Pastilha de freio", "180.00", 10, "Jogo dianteiro"),
    ]
    agregados = []
    for nome, preco, descricao in catalogo_servicos:
        servico = Servico.cadastrar(nome, Dinheiro.de_decimal(Decimal(preco)), descricao)
        servicos.save(servico)
        agregados.append(servico)
    for nome, preco, estoque, descricao in catalogo_pecas:
        peca = Peca.cadastrar(nome, Dinheiro.de_decimal(Decimal(preco)), Quantidade(estoque), descricao)
        pecas.save(peca)
        agregados.append(peca)
    eventos.salvar_todos([evento for agregado in agregados for evento in agregado.pull_events()])
