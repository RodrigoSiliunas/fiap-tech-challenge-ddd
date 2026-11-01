"""Máquina de estados da Ordem de Serviço."""

from enum import Enum


class StatusOS(str, Enum):
    RECEBIDA = "RECEBIDA"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    EM_EXECUCAO = "EM_EXECUCAO"
    FINALIZADA = "FINALIZADA"
    ENTREGUE = "ENTREGUE"
    REJEITADA = "REJEITADA"

    @property
    def descricao(self) -> str:
        return _DESCRICOES[self]

    def encerrada(self) -> bool:
        return self in {StatusOS.ENTREGUE, StatusOS.REJEITADA}


_DESCRICOES = {
    StatusOS.RECEBIDA: "Recebida",
    StatusOS.EM_DIAGNOSTICO: "Em diagnóstico",
    StatusOS.AGUARDANDO_APROVACAO: "Aguardando aprovação",
    StatusOS.EM_EXECUCAO: "Em execução",
    StatusOS.FINALIZADA: "Finalizada",
    StatusOS.ENTREGUE: "Entregue",
    StatusOS.REJEITADA: "Rejeitada",
}

# Somente estas setas são válidas. Qualquer outro salto é rejeitado pelo agregado.
TRANSICOES: dict[StatusOS, set[StatusOS]] = {
    StatusOS.RECEBIDA: {StatusOS.EM_DIAGNOSTICO},
    StatusOS.EM_DIAGNOSTICO: {StatusOS.AGUARDANDO_APROVACAO},
    StatusOS.AGUARDANDO_APROVACAO: {StatusOS.EM_EXECUCAO, StatusOS.REJEITADA},
    StatusOS.EM_EXECUCAO: {StatusOS.FINALIZADA},
    StatusOS.FINALIZADA: {StatusOS.ENTREGUE},
    StatusOS.ENTREGUE: set(),
    StatusOS.REJEITADA: set(),
}

STATUS_EDITAVEIS = {StatusOS.EM_DIAGNOSTICO, StatusOS.AGUARDANDO_APROVACAO}


class SituacaoOrcamento(str, Enum):
    GERADO = "GERADO"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"
