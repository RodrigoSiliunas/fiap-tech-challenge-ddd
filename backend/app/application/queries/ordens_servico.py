"""Read models de listagem, detalhe administrativo e acompanhamento do cliente."""

from dataclasses import dataclass
from uuid import UUID

from oficina.application.commands.ordens_servico import _ordem_do_cliente
from oficina.application.support import exigir, paginar
from oficina.domain.cliente.aggregate import Cliente
from oficina.domain.ordem_servico.aggregate import OrdemDeServico
from oficina.domain.ordem_servico.status import StatusOS
from oficina.domain.veiculo.aggregate import Veiculo


@dataclass
class ResumoOrdem:
    ordem: OrdemDeServico
    cliente_nome: str
    placa: str


@dataclass
class DetalheOrdem:
    ordem: OrdemDeServico
    cliente: Cliente
    veiculo: Veiculo
    eventos: list[dict]


class ListarOrdensDeServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, status: StatusOS | None, limite: int, offset: int) -> tuple[list[ResumoOrdem], int]:
        limite, offset = paginar(limite, offset)
        ordens, total = self.uow.ordens.listar(status, limite, offset)
        resumos = []
        for ordem in ordens:
            cliente = self.uow.clientes.get(ordem.cliente_id)
            veiculo = self.uow.veiculos.get(ordem.veiculo_id)
            resumos.append(
                ResumoOrdem(
                    ordem=ordem,
                    cliente_nome=cliente.nome if cliente else "",
                    placa=veiculo.placa.formatada() if veiculo else "",
                )
            )
        return resumos, total


class ObterOrdemDeServico:
    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID) -> DetalheOrdem:
        ordem = exigir(self.uow.ordens.get(ordem_id), "Ordem de serviço não encontrada")
        cliente = exigir(self.uow.clientes.get(ordem.cliente_id), "Cliente não encontrado")
        veiculo = exigir(self.uow.veiculos.get(ordem.veiculo_id), "Veículo não encontrado")
        eventos = self.uow.eventos.listar_por_agregado(ordem.id)
        return DetalheOrdem(ordem=ordem, cliente=cliente, veiculo=veiculo, eventos=eventos)


class ConsultarAcompanhamento:
    """Consulta pública: id da OS + documento do cliente."""

    def __init__(self, uow) -> None:
        self.uow = uow

    def executar(self, ordem_id: UUID, documento: str) -> DetalheOrdem:
        ordem = _ordem_do_cliente(self.uow, ordem_id, documento)
        cliente = exigir(self.uow.clientes.get(ordem.cliente_id), "Cliente não encontrado")
        veiculo = exigir(self.uow.veiculos.get(ordem.veiculo_id), "Veículo não encontrado")
        return DetalheOrdem(ordem=ordem, cliente=cliente, veiculo=veiculo, eventos=[])
