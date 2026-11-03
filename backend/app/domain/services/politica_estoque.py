"""Políticas de estoque derivadas do Event Storming.

- Na inclusão da peça, apenas valida disponibilidade (não reserva).
- Quando o orçamento é aprovado, baixa o estoque de cada ItemPeca.
"""

from uuid import UUID

from app.domain.exceptions import DomainError
from app.domain.ordem_servico.aggregate import OrdemDeServico
from app.domain.peca.aggregate import Peca


class PoliticaDisponibilidadeEstoque:
    def validar(self, peca: Peca, quantidade_necessaria: int) -> None:
        if quantidade_necessaria < 0:
            raise DomainError("Quantidade inválida", "quantidade_invalida")
        if peca.quantidade_estoque.valor < quantidade_necessaria:
            raise DomainError(
                f"Estoque insuficiente de {peca.nome}. Disponível: {peca.quantidade_estoque.valor}",
                "estoque_insuficiente",
            )


class PoliticaBaixaEstoque:
    """Quando OrcamentoAprovado, baixa o estoque de cada ItemPeca."""

    def aplicar(self, ordem: OrdemDeServico, pecas_por_id: dict[UUID, Peca]) -> None:
        for item in ordem.itens_peca:
            peca = pecas_por_id.get(item.peca_id)
            if peca is None:
                raise DomainError("Peça da ordem de serviço não encontrada", "nao_encontrado")
            peca.baixar(item.quantidade)
