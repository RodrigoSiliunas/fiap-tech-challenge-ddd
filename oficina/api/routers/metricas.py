from fastapi import APIRouter, Depends

from oficina.api.deps import get_current_user, get_uow
from oficina.api.schemas import TempoMedioOut
from oficina.application.queries.tempo_medio_execucao import CalcularTempoMedioExecucao

router = APIRouter(
    prefix="/metricas",
    tags=["Métricas"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/tempo-medio-execucao",
    response_model=TempoMedioOut,
    summary="Tempo médio de execução dos serviços",
    description=(
        "Média, em segundos e horas, entre o início da execução (aprovação do orçamento) "
        "e a finalização, considerando ordens Finalizadas ou Entregues."
    ),
)
def tempo_medio(uow=Depends(get_uow)) -> dict:
    return CalcularTempoMedioExecucao(uow).executar()
