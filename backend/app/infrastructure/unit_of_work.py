"""Unidade de trabalho: uma transação por comando."""

from sqlalchemy.orm import Session, sessionmaker

from oficina.infrastructure.db.repositories import (
    EventoRepository,
    SqlAlchemyClienteRepository,
    SqlAlchemyOrdemRepository,
    SqlAlchemyPecaRepository,
    SqlAlchemyServicoRepository,
    SqlAlchemyVeiculoRepository,
    UsuarioRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self.clientes: SqlAlchemyClienteRepository
        self.veiculos: SqlAlchemyVeiculoRepository
        self.servicos: SqlAlchemyServicoRepository
        self.pecas: SqlAlchemyPecaRepository
        self.ordens: SqlAlchemyOrdemRepository
        self.eventos: EventoRepository
        self.usuarios: UsuarioRepository

    def open(self) -> "SqlAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.clientes = SqlAlchemyClienteRepository(self.session)
        self.veiculos = SqlAlchemyVeiculoRepository(self.session)
        self.servicos = SqlAlchemyServicoRepository(self.session)
        self.pecas = SqlAlchemyPecaRepository(self.session)
        self.ordens = SqlAlchemyOrdemRepository(self.session)
        self.eventos = EventoRepository(self.session)
        self.usuarios = UsuarioRepository(self.session)
        return self

    def commit(self) -> None:
        assert self.session is not None
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
            self.session = None
