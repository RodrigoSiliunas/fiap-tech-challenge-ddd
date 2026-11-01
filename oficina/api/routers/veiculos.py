from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from oficina.api.deps import get_current_user, get_uow
from oficina.api.presenters import pagina, veiculo_out
from oficina.api.schemas import ListaVeiculosOut, VeiculoIn, VeiculoOut, VeiculoUpdate
from oficina.application.commands.cadastros import (
    AtualizarVeiculo,
    CadastrarVeiculo,
    ExcluirVeiculo,
    ListarVeiculos,
    ObterVeiculo,
)

router = APIRouter(
    prefix="/veiculos",
    tags=["Veículos"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=VeiculoOut, status_code=201, summary="Cadastrar veículo")
def cadastrar(body: VeiculoIn, uow=Depends(get_uow)) -> dict:
    veiculo = CadastrarVeiculo(uow).executar(body.cliente_id, body.placa, body.marca, body.modelo, body.ano)
    return veiculo_out(veiculo)


@router.get("", response_model=ListaVeiculosOut, summary="Listar veículos")
def listar(
    cliente_id: UUID | None = None,
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow=Depends(get_uow),
) -> dict:
    itens, total = ListarVeiculos(uow).executar(cliente_id, limite, offset)
    return pagina([veiculo_out(item) for item in itens], total, limite, offset)


@router.get("/{veiculo_id}", response_model=VeiculoOut, summary="Detalhar veículo")
def obter(veiculo_id: UUID, uow=Depends(get_uow)) -> dict:
    return veiculo_out(ObterVeiculo(uow).executar(veiculo_id))


@router.put("/{veiculo_id}", response_model=VeiculoOut, summary="Atualizar veículo")
def atualizar(veiculo_id: UUID, body: VeiculoUpdate, uow=Depends(get_uow)) -> dict:
    veiculo = AtualizarVeiculo(uow).executar(veiculo_id, body.marca, body.modelo, body.ano)
    return veiculo_out(veiculo)


@router.delete("/{veiculo_id}", status_code=204, summary="Excluir veículo")
def excluir(veiculo_id: UUID, uow=Depends(get_uow)) -> Response:
    ExcluirVeiculo(uow).executar(veiculo_id)
    return Response(status_code=204)
