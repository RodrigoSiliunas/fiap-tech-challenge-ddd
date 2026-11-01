from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from oficina.domain.exceptions import DomainError
from oficina.infrastructure.auth.jwt import decode_token
from oficina.infrastructure.db.session import get_session_factory
from oficina.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

_bearer = HTTPBearer(auto_error=False)


def get_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    uow = SqlAlchemyUnitOfWork(get_session_factory())
    uow.open()
    try:
        yield uow
    except Exception:
        uow.rollback()
        raise
    finally:
        uow.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise DomainError("Autenticação necessária", "nao_autenticado")
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise DomainError("Token inválido ou expirado", "nao_autenticado")
    return {"username": username, "nome": payload.get("nome"), "papel": payload.get("papel")}
