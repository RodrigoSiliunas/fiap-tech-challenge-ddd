from oficina.domain.exceptions import DomainError
from oficina.infrastructure.auth.jwt import create_token
from oficina.infrastructure.auth.passwords import verify_password
from oficina.config import get_settings


class AutenticarUsuario:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, username: str, password: str) -> dict:
        usuario = self.uow.usuarios.get_by_username((username or "").strip())
        if usuario is None or not verify_password(password or "", usuario.password_hash):
            raise DomainError("Credenciais inválidas", "credenciais_invalidas")
        return {
            "access_token": create_token(usuario.username, usuario.nome),
            "token_type": "bearer",
            "expires_in": get_settings().jwt_expire_minutes * 60,
            "nome": usuario.nome,
        }
