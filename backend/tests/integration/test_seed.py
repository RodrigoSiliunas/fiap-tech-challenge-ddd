"""Inicialização idempotente do banco e retry quando o Postgres ainda não subiu."""

from sqlalchemy.exc import OperationalError

from oficina.config import get_settings
from oficina.infrastructure.db.models import PecaModel, ServicoModel, UsuarioModel
from oficina.infrastructure.db.session import get_engine, get_session_factory, init_db, reset_database_state
from oficina.infrastructure.seed import seed


def test_seed_e_idempotente(tmp_path, admin_hash, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'oficina.db'}")
    get_settings.cache_clear()
    reset_database_state()
    init_db(retries=1, delay_seconds=0)
    init_db(retries=1, delay_seconds=0)
    session = get_session_factory()()
    try:
        assert session.query(UsuarioModel).count() == 1
        assert session.query(ServicoModel).count() == 3
        assert session.query(PecaModel).count() == 3
        seed(session, password_hash=admin_hash, catalogo=True)
        session.commit()
        assert session.query(ServicoModel).count() == 3
    finally:
        session.close()
        reset_database_state()
        get_settings.cache_clear()


def test_init_db_repete_quando_o_banco_recusa(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'retry.db'}")
    get_settings.cache_clear()
    reset_database_state()
    original = get_engine
    tentativas = {"n": 0}

    def flaky():
        tentativas["n"] += 1
        engine = original()
        if tentativas["n"] == 1:
            raise OperationalError("SELECT 1", {}, Exception("ainda subindo"))
        return engine

    monkeypatch.setattr("oficina.infrastructure.db.session.get_engine", flaky)
    init_db(retries=3, delay_seconds=0)
    assert tentativas["n"] >= 2
    reset_database_state()
    get_settings.cache_clear()
