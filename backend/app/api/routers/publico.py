from uuid import UUID

from fastapi import APIRouter, Depends, Query

from oficina.api.deps import get_uow
from oficina.api.presenters import ordem_out
from oficina.api.schemas import DecisaoOrcamentoIn, OrdemOut
from oficina.application.commands.ordens_servico import AprovarOrcamento, RejeitarOrcamento
from oficina.application.queries.ordens_servico import ConsultarAcompanhamento, ObterOrdemDeServico

router = APIRouter(prefix="/publico/ordens-servico", tags=["Acompanhamento (cliente)"])


@router.get(
    "/{ordem_id}",
    response_model=OrdemOut,
    summary="Consultar andamento da OS",
    description="Endpoint público. O cliente informa o id da OS e o CPF/CNPJ. Não exige JWT.",
)
def consultar(ordem_id: UUID, documento: str = Query(min_length=11, max_length=18), uow=Depends(get_uow)) -> dict:
    return ordem_out(ConsultarAcompanhamento(uow).executar(ordem_id, documento))


@router.post(
    "/{ordem_id}/aprovar",
    response_model=OrdemOut,
    summary="Aprovar orçamento",
    description="Registra a aprovação do cliente e baixa o estoque das peças na mesma transação.",
)
def aprovar(ordem_id: UUID, body: DecisaoOrcamentoIn, uow=Depends(get_uow)) -> dict:
    ordem = AprovarOrcamento(uow).executar(ordem_id, body.documento)
    return ordem_out(ObterOrdemDeServico(uow).executar(ordem.id))


@router.post("/{ordem_id}/rejeitar", response_model=OrdemOut, summary="Rejeitar orçamento")
def rejeitar(ordem_id: UUID, body: DecisaoOrcamentoIn, uow=Depends(get_uow)) -> dict:
    ordem = RejeitarOrcamento(uow).executar(ordem_id, body.documento, body.motivo)
    return ordem_out(ObterOrdemDeServico(uow).executar(ordem.id))
