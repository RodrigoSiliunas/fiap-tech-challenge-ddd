from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_current_user, get_uow
from app.api.presenters import pagina, peca_out
from app.api.schemas import (
    AjusteEstoqueIn,
    EntradaEstoqueIn,
    ListaPecasOut,
    PecaDetalheOut,
    PecaIn,
    PecaOut,
    PecaUpdate,
)
from app.application.commands.cadastros import (
    AjustarEstoque,
    AtualizarPeca,
    CadastrarPeca,
    ExcluirPeca,
    ListarPecas,
    ObterPeca,
    RegistrarEntradaEstoque,
)
from app.domain.shared.value_objects import Dinheiro

router = APIRouter(
    prefix="/pecas",
    tags=["Peças e insumos"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=PecaOut, status_code=201, summary="Cadastrar peça ou insumo")
def cadastrar(body: PecaIn, uow=Depends(get_uow)) -> dict:
    peca = CadastrarPeca(uow).executar(
        body.nome, Dinheiro.de_decimal(body.preco), body.quantidade_estoque, body.descricao
    )
    return peca_out(peca)


@router.get("", response_model=ListaPecasOut, summary="Listar peças e insumos")
def listar(
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow=Depends(get_uow),
) -> dict:
    itens, total = ListarPecas(uow).executar(limite, offset)
    return pagina([peca_out(item) for item in itens], total, limite, offset)


@router.get("/{peca_id}", response_model=PecaDetalheOut, summary="Detalhar peça e eventos de estoque")
def obter(peca_id: UUID, uow=Depends(get_uow)) -> dict:
    peca, eventos = ObterPeca(uow).executar(peca_id)
    return peca_out(peca, eventos)


@router.put("/{peca_id}", response_model=PecaOut, summary="Atualizar dados da peça")
def atualizar(peca_id: UUID, body: PecaUpdate, uow=Depends(get_uow)) -> dict:
    peca = AtualizarPeca(uow).executar(peca_id, body.nome, Dinheiro.de_decimal(body.preco), body.descricao)
    return peca_out(peca)


@router.delete("/{peca_id}", status_code=204, summary="Excluir peça")
def excluir(peca_id: UUID, uow=Depends(get_uow)) -> Response:
    ExcluirPeca(uow).executar(peca_id)
    return Response(status_code=204)


@router.post(
    "/{peca_id}/entrada-estoque",
    response_model=PecaOut,
    summary="Registrar entrada de estoque",
)
def entrada(peca_id: UUID, body: EntradaEstoqueIn, uow=Depends(get_uow)) -> dict:
    return peca_out(RegistrarEntradaEstoque(uow).executar(peca_id, body.quantidade))


@router.post(
    "/{peca_id}/ajuste-estoque",
    response_model=PecaOut,
    summary="Ajustar saldo de estoque",
)
def ajuste(peca_id: UUID, body: AjusteEstoqueIn, uow=Depends(get_uow)) -> dict:
    return peca_out(AjustarEstoque(uow).executar(peca_id, body.quantidade))
