"""Agregado Veículo. A placa é a identidade legal e não muda."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from oficina.domain.shared.aggregate import RaizAgregado
from oficina.domain.shared.clock import now
from oficina.domain.shared.events import DomainEvent
from oficina.domain.shared.validacao import validar_ano, validar_nome
from oficina.domain.veiculo.events import VeiculoAtualizado, VeiculoRegistrado
from oficina.domain.veiculo.placa import Placa


@dataclass
class Veiculo(RaizAgregado):
    id: UUID
    cliente_id: UUID
    placa: Placa
    marca: str
    modelo: str
    ano: int
    criado_em: datetime
    atualizado_em: datetime
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def registrar(cls, cliente_id: UUID, placa: Placa, marca: str, modelo: str, ano: int) -> "Veiculo":
        instante = now()
        veiculo = cls(
            id=uuid4(),
            cliente_id=cliente_id,
            placa=placa,
            marca=validar_nome(marca, "Marca", minimo=1, maximo=80),
            modelo=validar_nome(modelo, "Modelo", minimo=1, maximo=80),
            ano=validar_ano(ano),
            criado_em=instante,
            atualizado_em=instante,
        )
        veiculo._registrar(
            VeiculoRegistrado(
                agregado_id=veiculo.id,
                cliente_id=str(cliente_id),
                placa=placa.valor,
                marca=veiculo.marca,
                modelo=veiculo.modelo,
                ano=veiculo.ano,
            )
        )
        return veiculo

    def atualizar(self, marca: str, modelo: str, ano: int) -> None:
        self.marca = validar_nome(marca, "Marca", minimo=1, maximo=80)
        self.modelo = validar_nome(modelo, "Modelo", minimo=1, maximo=80)
        self.ano = validar_ano(ano)
        self.atualizado_em = now()
        self._registrar(
            VeiculoAtualizado(
                agregado_id=self.id,
                marca=self.marca,
                modelo=self.modelo,
                ano=self.ano,
            )
        )
