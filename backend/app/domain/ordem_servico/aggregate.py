"""Agregado OrdemDeServico.

Concentra itens, orçamento e a máquina de estados. O orçamento não existe
fora da OS neste MVP: total, aprovação e status mudam na mesma consistência.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.exceptions import DomainError
from app.domain.ordem_servico.events import (
    DiagnosticoIniciado,
    ExecucaoIniciada,
    ItemPecaRemovido,
    ItemServicoRemovido,
    OrcamentoAprovado,
    OrcamentoDisponibilizado,
    OrcamentoGerado,
    OrcamentoRejeitado,
    OrdemDeServicoRecebida,
    PecasIncluidas,
    ServicoFinalizado,
    ServicosIncluidos,
    VeiculoEntregue,
)
from app.domain.ordem_servico.status import (
    STATUS_EDITAVEIS,
    TRANSICOES,
    SituacaoOrcamento,
    StatusOS,
)
from app.domain.shared.aggregate import RaizAgregado
from app.domain.shared.clock import now
from app.domain.shared.events import DomainEvent
from app.domain.shared.validacao import validar_texto_opcional
from app.domain.shared.value_objects import Dinheiro, Quantidade, somar_dinheiros


@dataclass
class ItemServico:
    id: UUID
    servico_id: UUID
    descricao: str
    preco: Dinheiro


@dataclass
class ItemPeca:
    id: UUID
    peca_id: UUID
    nome: str
    quantidade: Quantidade
    preco_unitario: Dinheiro

    def subtotal(self) -> Dinheiro:
        return self.preco_unitario.multiplicar(self.quantidade.valor)


@dataclass
class Orcamento:
    id: UUID
    valor_servicos: Dinheiro
    valor_pecas: Dinheiro
    valor_total: Dinheiro
    situacao: SituacaoOrcamento
    gerado_em: datetime
    decidido_em: datetime | None = None
    motivo_rejeicao: str | None = None


@dataclass
class OrdemDeServico(RaizAgregado):
    id: UUID
    numero: int
    cliente_id: UUID
    veiculo_id: UUID
    status: StatusOS
    aberta_em: datetime
    itens_servico: list[ItemServico] = field(default_factory=list)
    itens_peca: list[ItemPeca] = field(default_factory=list)
    orcamento: Orcamento | None = None
    observacao: str | None = None
    diagnostico_iniciado_em: datetime | None = None
    orcamento_gerado_em: datetime | None = None
    execucao_iniciada_em: datetime | None = None
    finalizada_em: datetime | None = None
    entregue_em: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def abrir(
        cls,
        *,
        numero: int,
        cliente_id: UUID,
        veiculo_id: UUID,
        observacao: str | None = None,
    ) -> "OrdemDeServico":
        if numero <= 0:
            raise DomainError("Número da ordem de serviço inválido", "validacao")
        ordem = cls(
            id=uuid4(),
            numero=numero,
            cliente_id=cliente_id,
            veiculo_id=veiculo_id,
            status=StatusOS.RECEBIDA,
            aberta_em=now(),
            observacao=validar_texto_opcional(observacao, "Observação", 2000),
        )
        ordem._registrar(
            OrdemDeServicoRecebida(
                agregado_id=ordem.id,
                numero=numero,
                cliente_id=str(cliente_id),
                veiculo_id=str(veiculo_id),
            )
        )
        return ordem

    def iniciar_diagnostico(self, observacao: str | None = None) -> None:
        self._transicionar(StatusOS.EM_DIAGNOSTICO)
        self.diagnostico_iniciado_em = now()
        if observacao is not None:
            self.observacao = validar_texto_opcional(observacao, "Observação", 2000)
        self._registrar(DiagnosticoIniciado(agregado_id=self.id))

    def incluir_servico(self, servico_id: UUID, descricao: str, preco: Dinheiro) -> ItemServico:
        self._garantir_itens_editaveis()
        if any(item.servico_id == servico_id for item in self.itens_servico):
            raise DomainError("Serviço já incluído nesta ordem de serviço", "servico_duplicado")
        item = ItemServico(id=uuid4(), servico_id=servico_id, descricao=descricao.strip(), preco=preco)
        if not item.descricao:
            raise DomainError("Descrição do serviço é obrigatória", "validacao")
        self.itens_servico.append(item)
        self._registrar(
            ServicosIncluidos(agregado_id=self.id, item_id=str(item.id), servico_id=str(servico_id))
        )
        self._recalcular_se_aguardando()
        return item

    def remover_servico(self, item_id: UUID) -> None:
        self._garantir_itens_editaveis()
        if not any(item.id == item_id for item in self.itens_servico):
            raise DomainError("Item de serviço não encontrado na ordem", "nao_encontrado")
        if self.status == StatusOS.AGUARDANDO_APROVACAO and len(self.itens_servico) == 1:
            raise DomainError(
                "Mantenha ao menos um serviço enquanto o orçamento aguarda aprovação",
                "orcamento_sem_servico",
            )
        self.itens_servico = [item for item in self.itens_servico if item.id != item_id]
        self._registrar(ItemServicoRemovido(agregado_id=self.id, item_id=str(item_id)))
        self._recalcular_se_aguardando()

    def incluir_peca(
        self,
        peca_id: UUID,
        nome: str,
        quantidade: Quantidade,
        preco_unitario: Dinheiro,
    ) -> ItemPeca:
        self._garantir_itens_editaveis()
        if quantidade.valor <= 0:
            raise DomainError("Quantidade da peça deve ser maior que zero", "quantidade_invalida")
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise DomainError("Nome da peça é obrigatório", "validacao")
        existente = next((item for item in self.itens_peca if item.peca_id == peca_id), None)
        if existente:
            existente.quantidade = Quantidade(existente.quantidade.valor + quantidade.valor)
            item = existente
        else:
            item = ItemPeca(
                id=uuid4(),
                peca_id=peca_id,
                nome=nome_limpo,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
            )
            self.itens_peca.append(item)
        self._registrar(
            PecasIncluidas(
                agregado_id=self.id,
                item_id=str(item.id),
                peca_id=str(peca_id),
                quantidade=item.quantidade.valor,
            )
        )
        self._recalcular_se_aguardando()
        return item

    def remover_peca(self, item_id: UUID) -> None:
        self._garantir_itens_editaveis()
        if not any(item.id == item_id for item in self.itens_peca):
            raise DomainError("Item de peça não encontrado na ordem", "nao_encontrado")
        self.itens_peca = [item for item in self.itens_peca if item.id != item_id]
        self._registrar(ItemPecaRemovido(agregado_id=self.id, item_id=str(item_id)))
        self._recalcular_se_aguardando()

    def quantidade_da_peca(self, peca_id: UUID) -> int:
        item = next((atual for atual in self.itens_peca if atual.peca_id == peca_id), None)
        return item.quantidade.valor if item else 0

    def gerar_orcamento(self) -> Orcamento:
        if self.status == StatusOS.EM_DIAGNOSTICO:
            self._exigir_servico()
            self.orcamento = self._montar_orcamento()
            self._transicionar(StatusOS.AGUARDANDO_APROVACAO)
            self.orcamento_gerado_em = self.orcamento.gerado_em
            self._publicar_orcamento()
            return self.orcamento
        if self.status == StatusOS.AGUARDANDO_APROVACAO:
            return self._substituir_orcamento()
        raise DomainError(
            "Orçamento só pode ser gerado em diagnóstico ou atualizado enquanto aguarda aprovação",
            "transicao_invalida",
        )

    def aprovar_orcamento(self) -> None:
        if self.orcamento is None:
            raise DomainError("Ordem de serviço sem orçamento", "regra_negocio")
        self._transicionar(StatusOS.EM_EXECUCAO)
        instante = now()
        self.orcamento.situacao = SituacaoOrcamento.APROVADO
        self.orcamento.decidido_em = instante
        self.execucao_iniciada_em = instante
        self._registrar(
            OrcamentoAprovado(agregado_id=self.id, valor_total_centavos=self.orcamento.valor_total.centavos)
        )
        self._registrar(ExecucaoIniciada(agregado_id=self.id))

    def rejeitar_orcamento(self, motivo: str | None = None) -> None:
        if self.orcamento is None:
            raise DomainError("Ordem de serviço sem orçamento", "regra_negocio")
        self._transicionar(StatusOS.REJEITADA)
        self.orcamento.situacao = SituacaoOrcamento.REJEITADO
        self.orcamento.decidido_em = now()
        self.orcamento.motivo_rejeicao = validar_texto_opcional(motivo, "Motivo da rejeição", 500)
        self._registrar(OrcamentoRejeitado(agregado_id=self.id, motivo=self.orcamento.motivo_rejeicao))

    def finalizar(self) -> None:
        self._transicionar(StatusOS.FINALIZADA)
        self.finalizada_em = now()
        self._registrar(ServicoFinalizado(agregado_id=self.id))

    def entregar(self) -> None:
        self._transicionar(StatusOS.ENTREGUE)
        self.entregue_em = now()
        self._registrar(VeiculoEntregue(agregado_id=self.id))

    def _transicionar(self, destino: StatusOS) -> None:
        if destino not in TRANSICOES[self.status]:
            raise DomainError(
                f"Transição de status inválida: {self.status.descricao} → {destino.descricao}",
                "transicao_invalida",
            )
        self.status = destino

    def _garantir_itens_editaveis(self) -> None:
        if self.status not in STATUS_EDITAVEIS:
            raise DomainError(
                "Itens só podem ser alterados em diagnóstico ou enquanto o orçamento aguarda aprovação",
                "itens_bloqueados",
            )

    def _exigir_servico(self) -> None:
        if not self.itens_servico:
            raise DomainError(
                "Inclua ao menos um serviço antes de gerar o orçamento",
                "orcamento_sem_servico",
            )

    def _montar_orcamento(self) -> Orcamento:
        valor_servicos = somar_dinheiros([item.preco for item in self.itens_servico])
        valor_pecas = somar_dinheiros([item.subtotal() for item in self.itens_peca])
        return Orcamento(
            id=self.orcamento.id if self.orcamento else uuid4(),
            valor_servicos=valor_servicos,
            valor_pecas=valor_pecas,
            valor_total=valor_servicos.somar(valor_pecas),
            situacao=SituacaoOrcamento.GERADO,
            gerado_em=now(),
        )

    def _substituir_orcamento(self) -> Orcamento:
        self._exigir_servico()
        self.orcamento = self._montar_orcamento()
        self.orcamento_gerado_em = self.orcamento.gerado_em
        self._publicar_orcamento()
        return self.orcamento

    def _publicar_orcamento(self) -> None:
        assert self.orcamento is not None
        centavos = self.orcamento.valor_total.centavos
        self._registrar(OrcamentoGerado(agregado_id=self.id, valor_total_centavos=centavos))
        self._registrar(OrcamentoDisponibilizado(agregado_id=self.id, valor_total_centavos=centavos))

    def _recalcular_se_aguardando(self) -> None:
        if self.status == StatusOS.AGUARDANDO_APROVACAO:
            self._substituir_orcamento()
