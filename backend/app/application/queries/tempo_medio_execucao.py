"""Tempo médio entre o início da execução e a finalização das OS concluídas."""


class CalcularTempoMedioExecucao:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self) -> dict:
        duracoes = self.uow.ordens.duracoes_execucao_segundos()
        if not duracoes:
            return {"quantidade_os": 0, "tempo_medio_segundos": None, "tempo_medio_horas": None}
        media = sum(duracoes) / len(duracoes)
        return {
            "quantidade_os": len(duracoes),
            "tempo_medio_segundos": round(media, 2),
            "tempo_medio_horas": round(media / 3600, 4),
        }
