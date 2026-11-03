from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_uow
from app.api.presenters import ordem_detalhe_out, pagina, resumo_ordem_out
from app.api.schemas import (
    AbrirOrdemIn,
    DiagnosticoIn,
    IncluirPecaIn,
    IncluirServicoIn,
    ListaOrdensOut,
    OrdemDetalheOut,
)
from app.application.commands.ordens_servico import (
    AbrirOrdemDeServico,
    AbrirOrdemInput,
    EntregarVeiculo,
    FinalizarServico,
    GerarOrcamento,
    IncluirPecaNaOrdem,
    IncluirServicoNaOrdem,
    IniciarDiagnostico,
    RemoverPecaDaOrdem,
    RemoverServicoDaOrdem,
)
from app.application.queries.ordens_servico import ListarOrdensDeServico, ObterOrdemDeServico
from app.domain.ordem_servico.status import StatusOS

router = APIRouter(
    prefix="/ordens-servico",
    tags=["Ordens de serviço"],
    dependencies=[Depends(get_current_user)],
)


def _detalhe(uow, ordem_id: UUID) -> dict:
    return ordem_detalhe_out(ObterOrdemDeServico(uow).executar(ordem_id))


@router.post("", response_model=OrdemDetalheOut, status_code=201, summary="Abrir ordem de serviço")
def abrir(body: AbrirOrdemIn, uow=Depends(get_uow)) -> dict:
    ordem = AbrirOrdemDeServico(uow).executar(
        AbrirOrdemInput(
            documento=body.documento,
            nome=body.nome,
            email=body.email,
            telefone=body.telefone,
            placa=body.placa,
            marca=body.marca,
            modelo=body.modelo,
            ano=body.ano,
            observacao=body.observacao,
        )
    )
    return _detalhe(uow, ordem.id)


@router.get("", response_model=ListaOrdensOut, summary="Listar ordens de serviço")
def listar(
    status: StatusOS | None = None,
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow=Depends(get_uow),
) -> dict:
    itens, total = ListarOrdensDeServico(uow).executar(status, limite, offset)
    return pagina([resumo_ordem_out(item) for item in itens], total, limite, offset)


@router.get("/{ordem_id}", response_model=OrdemDetalheOut, summary="Detalhar ordem de serviço")
def obter(ordem_id: UUID, uow=Depends(get_uow)) -> dict:
    return _detalhe(uow, ordem_id)


@router.post("/{ordem_id}/diagnostico", response_model=OrdemDetalheOut, summary="Iniciar diagnóstico")
def diagnostico(ordem_id: UUID, body: DiagnosticoIn | None = None, uow=Depends(get_uow)) -> dict:
    observacao = body.observacao if body else None
    ordem = IniciarDiagnostico(uow).executar(ordem_id, observacao)
    return _detalhe(uow, ordem.id)


@router.post("/{ordem_id}/servicos", response_model=OrdemDetalheOut, summary="Incluir serviço na OS")
def incluir_servico(ordem_id: UUID, body: IncluirServicoIn, uow=Depends(get_uow)) -> dict:
    ordem = IncluirServicoNaOrdem(uow).executar(ordem_id, body.servico_id)
    return _detalhe(uow, ordem.id)


@router.delete(
    "/{ordem_id}/servicos/{item_id}",
    response_model=OrdemDetalheOut,
    summary="Remover serviço da OS",
)
def remover_servico(ordem_id: UUID, item_id: UUID, uow=Depends(get_uow)) -> dict:
    ordem = RemoverServicoDaOrdem(uow).executar(ordem_id, item_id)
    return _detalhe(uow, ordem.id)


@router.post("/{ordem_id}/pecas", response_model=OrdemDetalheOut, summary="Incluir peça ou insumo na OS")
def incluir_peca(ordem_id: UUID, body: IncluirPecaIn, uow=Depends(get_uow)) -> dict:
    ordem = IncluirPecaNaOrdem(uow).executar(ordem_id, body.peca_id, body.quantidade)
    return _detalhe(uow, ordem.id)


@router.delete(
    "/{ordem_id}/pecas/{item_id}",
    response_model=OrdemDetalheOut,
    summary="Remover peça da OS",
)
def remover_peca(ordem_id: UUID, item_id: UUID, uow=Depends(get_uow)) -> dict:
    ordem = RemoverPecaDaOrdem(uow).executar(ordem_id, item_id)
    return _detalhe(uow, ordem.id)


@router.post(
    "/{ordem_id}/orcamento",
    response_model=OrdemDetalheOut,
    summary="Gerar orçamento e enviar para aprovação",
)
def gerar_orcamento(ordem_id: UUID, uow=Depends(get_uow)) -> dict:
    ordem = GerarOrcamento(uow).executar(ordem_id)
    return _detalhe(uow, ordem.id)


@router.post("/{ordem_id}/finalizar", response_model=OrdemDetalheOut, summary="Finalizar serviço")
def finalizar(ordem_id: UUID, uow=Depends(get_uow)) -> dict:
    ordem = FinalizarServico(uow).executar(ordem_id)
    return _detalhe(uow, ordem.id)


@router.post("/{ordem_id}/entregar", response_model=OrdemDetalheOut, summary="Entregar veículo")
def entregar(ordem_id: UUID, uow=Depends(get_uow)) -> dict:
    ordem = EntregarVeiculo(uow).executar(ordem_id)
    return _detalhe(uow, ordem.id)
