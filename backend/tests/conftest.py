"""Fixtures de integração. Os testes usam SQLite em memória; o app usa PostgreSQL."""

import os

os.environ["OFICINA_SKIP_STARTUP"] = "1"
os.environ["JWT_SECRET"] = "test-secret-dev-only-not-a-real-secret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "120"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["ADMIN_NOME"] = "Administrador da Oficina"
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.infrastructure.auth.passwords import hash_password
from app.infrastructure.db.models import Base
from app.infrastructure.db.session import build_engine, reset_database_state
from app.infrastructure.seed import seed
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.main import create_app

get_settings.cache_clear()
reset_database_state()


@pytest.fixture(scope="session")
def admin_hash() -> str:
    return hash_password("admin123")


@pytest.fixture
def database(admin_hash: str):
    url = os.getenv("OFICINA_TEST_DATABASE_URL")
    if url:
        engine = build_engine(url)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    else:
        engine = build_engine("sqlite://")
        engine.dispose()
        engine = __import__("sqlalchemy").create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        seed(session, password_hash=admin_hash, catalogo=False)
        session.commit()
    finally:
        session.close()
    yield engine, factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(database) -> Generator[TestClient, None, None]:
    _engine, factory = database
    app = create_app()

    def override_uow():
        uow = SqlAlchemyUnitOfWork(factory)
        uow.open()
        try:
            yield uow
        except Exception:
            uow.rollback()
            raise
        finally:
            uow.close()

    from app.api.deps import get_uow

    app.dependency_overrides[get_uow] = override_uow
    with TestClient(app) as test_client:
        test_client.factory = factory  # type: ignore[attr-defined]
        yield test_client


@pytest.fixture
def auth(client: TestClient) -> dict[str, str]:
    resposta = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resposta.status_code == 200, resposta.text
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
