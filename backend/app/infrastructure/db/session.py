"""Engine, sessão e criação de schema no startup do monólito."""

import time

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.infrastructure.db.models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


@event.listens_for(Engine, "connect")
def _habilitar_fk_sqlite(dbapi_connection, _connection_record) -> None:
    if "sqlite" not in type(dbapi_connection).__module__:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def build_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        connect_args: dict = {"check_same_thread": False}
    else:
        connect_args = {"connect_timeout": 5}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = build_engine(get_settings().database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory


def reset_database_state() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def init_db(retries: int = 15, delay_seconds: float = 2.0) -> None:
    """Cria tabelas e dados de demonstração. Repete enquanto o Postgres sobe."""
    from app.infrastructure.seed import seed

    last_error: OperationalError | None = None
    for attempt in range(1, retries + 1):
        try:
            engine = get_engine()
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(engine)
            factory = get_session_factory()
            session = factory()
            try:
                seed(session)
                session.commit()
            finally:
                session.close()
            return
        except OperationalError as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay_seconds)
    raise RuntimeError("Banco de dados indisponível") from last_error
