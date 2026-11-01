"""Comandos do fluxo da Ordem de Serviço, do orçamento e da execução."""

from dataclasses import dataclass
from uuid import UUID

from oficina.application.support import concluir, exigir
from oficina.domain.cliente.aggregate import Cliente
from oficina.domain.cliente.documento import Documento
from oficina.domain.exceptions import DomainError
from oficina.domain.ordem_servico.aggregate import OrdemDeServico
from oficina.domain.services.politica_estoque import PoliticaBaixaEstoque, PoliticaDisponibilidadeEstoque
from oficina.domain.shared.value_objects import Quantidade
from oficina.domain.veiculo.aggregate import Veiculo
from oficina.domain.veiculo.placa import Placa


@dataclass
class AbrirOrdemInput:
    documento: str
    nome: str | None
    email: str | None
    telefone: str | None
    placa: str
    marca: str
    modelo: str
    ano: int
    observacao: str | None = None


class AbrirOrdemDeServico:
    """Identifica o cliente, registra o veículo e abre a OS em Recebida — uma transação."""

    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, dados: AbrirOrdemInput) -> OrdemDeServico:
        documento = Documento.criar(dados.documento)
        cliente = self.uow.clientes.get_by_documento(documento)
        if cliente is None:
            if not dados.nome:
                raise DomainError("Nome é obrigatório para cadastrar o cliente", "validacao")
            cliente = Cliente.cadastrar(dados.nome, documento, dados.email, dados.telefone)
            self.uow.clientes.save(cliente)
        cliente.identificar()

        placa = Placa.criar(dados.placa)
        veiculo = self.uow.veiculos.get_by_placa(placa)
        veiculo_novo = veiculo is None
        if veiculo is None:
            veiculo = Veiculo.registrar(cliente.id, placa, dados.marca, dados.modelo, dados.ano)
            self.uow.veiculos.save(veiculo)
        elif veiculo.cliente_id != cliente.id:
            raise DomainError("Placa já cadastrada para outro cliente", "placa_duplicada")

        if self.uow.ordens.existe_nao_encerrada(veiculo.id):
            raise DomainError("Já existe uma ordem de serviço em aberto para este veículo", "conflito")

        ordem = OrdemDeServico.abrir(
            numero=self.uow.ordens.proximo_numero(),
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            observacao=dados.observacao,
        )
        self.uow.ordens.save(ordem)
        agregados = [cliente, ordem]
        if veiculo_novo:
            agregados.append(veiculo)
        concluir(self.uow, *agregados)
        return ordem


class IniciarDiagnostico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, observacao: str | None = None) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        ordem.iniciar_diagnostico(observacao)
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class IncluirServicoNaOrdem:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, servico_id: UUID) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        servico = exigir(self.uow.servicos.get(servico_id), "Serviço não encontrado")
        ordem.incluir_servico(servico.id, servico.nome, servico.preco)
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class RemoverServicoDaOrdem:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, item_id: UUID) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        ordem.remover_servico(item_id)
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class IncluirPecaNaOrdem:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, peca_id: UUID, quantidade: int) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        peca = exigir(self.uow.pecas.get(peca_id), "Peça não encontrada")
        quantidade_vo = Quantidade.positiva(quantidade)
        necessaria = ordem.quantidade_da_peca(peca.id) + quantidade_vo.valor
        PoliticaDisponibilidadeEstoque().validar(peca, necessaria)
        ordem.incluir_peca(peca.id, peca.nome, quantidade_vo, peca.preco)
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class RemoverPecaDaOrdem:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, item_id: UUID) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        ordem.remover_peca(item_id)
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class GerarOrcamento:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        ordem.gerar_orcamento()
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class AprovarOrcamento:
    """Aprova e, na mesma transação, baixa o estoque (política OrcamentoAprovado)."""

    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, documento: str) -> OrdemDeServico:
        ordem = _ordem_do_cliente(self.uow, ordem_id, documento, lock=True)
        pecas = []
        for item in sorted(ordem.itens_peca, key=lambda atual: str(atual.peca_id)):
            pecas.append(exigir(self.uow.pecas.get(item.peca_id, lock=True), "Peça da ordem de serviço não encontrada"))
        ordem.aprovar_orcamento()
        PoliticaBaixaEstoque().aplicar(ordem, {peca.id: peca for peca in pecas})
        self.uow.ordens.save(ordem)
        for peca in pecas:
            self.uow.pecas.save(peca)
        concluir(self.uow, ordem, *pecas)
        return ordem


class RejeitarOrcamento:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, documento: str, motivo: str | None) -> OrdemDeServico:
        ordem = _ordem_do_cliente(self.uow, ordem_id, documento)
        ordem.rejeitar_orcamento(motivo)
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class FinalizarServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        ordem.finalizar()
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


class EntregarVeiculo:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID) -> OrdemDeServico:
        ordem = _ordem(self.uow, ordem_id)
        ordem.entregar()
        self.uow.ordens.save(ordem)
        concluir(self.uow, ordem)
        return ordem


def _ordem(uow, ordem_id: UUID, *, lock: bool = False) -> OrdemDeServico:
    return exigir(uow.ordens.get(ordem_id, lock=lock), "Ordem de serviço não encontrada")


def _ordem_do_cliente(uow, ordem_id: UUID, documento_bruto: str, *, lock: bool = False) -> OrdemDeServico:
    ordem = uow.ordens.get(ordem_id, lock=lock)
    if ordem is None:
        raise DomainError("Ordem de serviço não encontrada", "nao_encontrado")
    cliente = uow.clientes.get(ordem.cliente_id)
    try:
        documento = Documento.criar(documento_bruto)
    except DomainError as exc:
        raise DomainError("Ordem de serviço não encontrada", "nao_encontrado") from exc
    if cliente is None or cliente.documento != documento:
        raise DomainError("Ordem de serviço não encontrada", "nao_encontrado")
    return ordem
