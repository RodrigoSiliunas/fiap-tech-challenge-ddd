import json

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from oficina.domain.exceptions import DomainError


def _jsonavel(valor):
    if isinstance(valor, BaseException):
        return str(valor)
    if isinstance(valor, dict):
        return {str(chave): _jsonavel(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_jsonavel(item) for item in valor]
    try:
        json.dumps(valor)
    except TypeError:
        return str(valor)
    return valor

_STATUS = {
    "nao_encontrado": 404,
    "conflito": 409,
    "documento_duplicado": 409,
    "placa_duplicada": 409,
    "estoque_insuficiente": 409,
    "transicao_invalida": 409,
    "servico_duplicado": 409,
    "itens_bloqueados": 409,
    "orcamento_sem_servico": 409,
    "credenciais_invalidas": 401,
    "nao_autenticado": 401,
    "erro_interno": 500,
}


def registrar_erros(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def dominio(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_STATUS.get(exc.codigo, 422),
            content={"codigo": exc.codigo, "mensagem": exc.mensagem},
        )

    @app.exception_handler(RequestValidationError)
    async def validacao(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"codigo": "validacao", "mensagem": "Dados inválidos", "erros": _jsonavel(exc.errors())},
        )
