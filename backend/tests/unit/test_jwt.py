from datetime import timedelta

import jwt
import pytest

from app.domain.exceptions import DomainError
from app.domain.shared.clock import now
from app.infrastructure.auth.jwt import create_token, decode_token
from app.infrastructure.auth.passwords import hash_password, verify_password
from app.config import Settings, get_settings


def test_jwt_redondo_e_senha():
    token = create_token("admin", "Administrador da Oficina")
    payload = decode_token(token)
    assert payload["sub"] == "admin"
    assert payload["papel"] == "ADMIN"
    senha = hash_password("admin123")
    assert verify_password("admin123", senha)
    assert not verify_password("errada", senha)
    assert not verify_password("admin123", "nao-e-hash")


def test_jwt_invalido_e_expirado():
    with pytest.raises(DomainError):
        decode_token("token-invalido")
    settings = get_settings()
    expirado = jwt.encode(
        {"sub": "admin", "exp": now() - timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(DomainError) as erro:
        decode_token(expirado)
    assert erro.value.codigo == "nao_autenticado"


def test_sem_jwt_secret_cada_subida_gera_um_segredo(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    primeiro = Settings(_env_file=None).jwt_secret
    segundo = Settings(_env_file=None).jwt_secret
    assert primeiro != segundo
    assert len(primeiro) >= 32
