from fastapi import APIRouter, Depends

from app.api.deps import get_uow
from app.api.schemas import LoginIn, TokenOut
from app.application.commands.autenticar import AutenticarUsuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Autenticar usuário administrativo",
    description="Retorna um JWT Bearer para as rotas administrativas. Credencial de demonstração: admin / admin123.",
)
def login(body: LoginIn, uow=Depends(get_uow)) -> dict:
    return AutenticarUsuario(uow).executar(body.username, body.password)
