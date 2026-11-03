"""Agregado Serviço — item do catálogo da oficina, com preço de referência."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.servico.events import ServicoCatalogoAtualizado, ServicoCatalogoCadastrado
from app.domain.shared.aggregate import RaizAgregado
from app.domain.shared.clock import now
from app.domain.shared.events import DomainEvent
from app.domain.shared.validacao import validar_nome, validar_texto_opcional
from app.domain.shared.value_objects import Dinheiro


@dataclass
class Servico(RaizAgregado):
    id: UUID
    nome: str
    descricao: str | None
    preco: Dinheiro
    criado_em: datetime
    atualizado_em: datetime
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def cadastrar(cls, nome: str, preco: Dinheiro, descricao: str | None = None) -> "Servico":
        instante = now()
        servico = cls(
            id=uuid4(),
            nome=validar_nome(nome, "Nome do serviço"),
            descricao=validar_texto_opcional(descricao, "Descrição", 500),
            preco=preco,
            criado_em=instante,
            atualizado_em=instante,
        )
        servico._registrar(
            ServicoCatalogoCadastrado(
                agregado_id=servico.id,
                nome=servico.nome,
                preco_centavos=servico.preco.centavos,
            )
        )
        return servico

    def atualizar(self, nome: str, preco: Dinheiro, descricao: str | None) -> None:
        self.nome = validar_nome(nome, "Nome do serviço")
        self.descricao = validar_texto_opcional(descricao, "Descrição", 500)
        self.preco = preco
        self.atualizado_em = now()
        self._registrar(
            ServicoCatalogoAtualizado(
                agregado_id=self.id,
                nome=self.nome,
                preco_centavos=self.preco.centavos,
            )
        )
