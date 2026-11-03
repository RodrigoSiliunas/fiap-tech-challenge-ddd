from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_current_user, get_uow
from app.api.presenters import pagina, servico_out
from app.api.schemas import ListaServicosOut, ServicoIn, ServicoOut, respostas_erro
from app.application.commands.cadastros import (
    AtualizarServico,
    CadastrarServico,
    ExcluirServico,
    ListarServicos,
    ObterServico,
)
from app.domain.shared.value_objects import Dinheiro

router = APIRouter(
    prefix="/servicos",
    tags=["Serviços"],
    dependencies=[Depends(get_current_user)],
    responses=respostas_erro(401, 404, 409, 422),
)


@router.post("", response_model=ServicoOut, status_code=201, summary="Cadastrar serviço do catálogo")
def cadastrar(body: ServicoIn, uow=Depends(get_uow)) -> dict:
    servico = CadastrarServico(uow).executar(body.nome, Dinheiro.de_decimal(body.preco), body.descricao)
    return servico_out(servico)


@router.get("", response_model=ListaServicosOut, summary="Listar serviços")
def listar(
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow=Depends(get_uow),
) -> dict:
    itens, total = ListarServicos(uow).executar(limite, offset)
    return pagina([servico_out(item) for item in itens], total, limite, offset)


@router.get("/{servico_id}", response_model=ServicoOut, summary="Detalhar serviço")
def obter(servico_id: UUID, uow=Depends(get_uow)) -> dict:
    return servico_out(ObterServico(uow).executar(servico_id))


@router.put("/{servico_id}", response_model=ServicoOut, summary="Atualizar serviço")
def atualizar(servico_id: UUID, body: ServicoIn, uow=Depends(get_uow)) -> dict:
    servico = AtualizarServico(uow).executar(
        servico_id, body.nome, Dinheiro.de_decimal(body.preco), body.descricao
    )
    return servico_out(servico)


@router.delete("/{servico_id}", status_code=204, summary="Excluir serviço")
def excluir(servico_id: UUID, uow=Depends(get_uow)) -> Response:
    ExcluirServico(uow).executar(servico_id)
    return Response(status_code=204)
