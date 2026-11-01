from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from oficina.api.deps import get_current_user, get_uow
from oficina.api.presenters import cliente_out, pagina
from oficina.api.schemas import ClienteIn, ClienteOut, ClienteUpdate, ListaClientesOut
from oficina.application.commands.cadastros import (
    AtualizarCliente,
    CadastrarCliente,
    ExcluirCliente,
    ListarClientes,
    ObterCliente,
)
router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=ClienteOut, status_code=201, summary="Cadastrar cliente")
def cadastrar(body: ClienteIn, uow=Depends(get_uow)) -> dict:
    cliente = CadastrarCliente(uow).executar(body.nome, body.documento, body.email, body.telefone)
    return cliente_out(cliente)


@router.get("", response_model=ListaClientesOut, summary="Listar clientes")
def listar(
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow=Depends(get_uow),
) -> dict:
    itens, total = ListarClientes(uow).executar(limite, offset)
    return pagina([cliente_out(item) for item in itens], total, limite, offset)


@router.get("/{cliente_id}", response_model=ClienteOut, summary="Detalhar cliente")
def obter(cliente_id: UUID, uow=Depends(get_uow)) -> dict:
    return cliente_out(ObterCliente(uow).executar(cliente_id))


@router.put("/{cliente_id}", response_model=ClienteOut, summary="Atualizar cliente")
def atualizar(cliente_id: UUID, body: ClienteUpdate, uow=Depends(get_uow)) -> dict:
    cliente = AtualizarCliente(uow).executar(cliente_id, body.nome, body.email, body.telefone)
    return cliente_out(cliente)


@router.delete("/{cliente_id}", status_code=204, summary="Excluir cliente")
def excluir(cliente_id: UUID, uow=Depends(get_uow)) -> Response:
    ExcluirCliente(uow).executar(cliente_id)
    return Response(status_code=204)
