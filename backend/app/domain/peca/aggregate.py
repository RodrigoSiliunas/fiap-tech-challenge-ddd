"""Agregado Peça. Invariante: quantidade em estoque nunca fica negativa."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.exceptions import DomainError
from app.domain.peca.events import (
    EstoqueAjustado,
    EstoqueDecrementado,
    EstoqueIncrementado,
    PecaAtualizada,
    PecaCadastrada,
)
from app.domain.shared.aggregate import RaizAgregado
from app.domain.shared.clock import now
from app.domain.shared.events import DomainEvent
from app.domain.shared.validacao import validar_nome, validar_texto_opcional
from app.domain.shared.value_objects import Dinheiro, Quantidade


@dataclass
class Peca(RaizAgregado):
    id: UUID
    nome: str
    descricao: str | None
    preco: Dinheiro
    quantidade_estoque: Quantidade
    criado_em: datetime
    atualizado_em: datetime
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def cadastrar(
        cls,
        nome: str,
        preco: Dinheiro,
        quantidade_estoque: Quantidade,
        descricao: str | None = None,
    ) -> "Peca":
        instante = now()
        peca = cls(
            id=uuid4(),
            nome=validar_nome(nome, "Nome da peça"),
            descricao=validar_texto_opcional(descricao, "Descrição", 500),
            preco=preco,
            quantidade_estoque=quantidade_estoque,
            criado_em=instante,
            atualizado_em=instante,
        )
        peca._registrar(
            PecaCadastrada(
                agregado_id=peca.id,
                nome=peca.nome,
                preco_centavos=peca.preco.centavos,
                quantidade_estoque=peca.quantidade_estoque.valor,
            )
        )
        return peca

    def atualizar(self, nome: str, preco: Dinheiro, descricao: str | None) -> None:
        self.nome = validar_nome(nome, "Nome da peça")
        self.descricao = validar_texto_opcional(descricao, "Descrição", 500)
        self.preco = preco
        self.atualizado_em = now()
        self._registrar(
            PecaAtualizada(
                agregado_id=self.id,
                nome=self.nome,
                preco_centavos=self.preco.centavos,
            )
        )

    def registrar_entrada(self, quantidade: Quantidade) -> None:
        if quantidade.valor <= 0:
            raise DomainError("Entrada de estoque deve ser maior que zero", "quantidade_invalida")
        self.quantidade_estoque = Quantidade(self.quantidade_estoque.valor + quantidade.valor)
        self.atualizado_em = now()
        self._registrar(
            EstoqueIncrementado(
                agregado_id=self.id,
                quantidade=quantidade.valor,
                saldo=self.quantidade_estoque.valor,
            )
        )

    def ajustar_estoque(self, nova_quantidade: Quantidade) -> None:
        self.quantidade_estoque = nova_quantidade
        self.atualizado_em = now()
        self._registrar(EstoqueAjustado(agregado_id=self.id, saldo=self.quantidade_estoque.valor))

    def baixar(self, quantidade: Quantidade) -> None:
        if quantidade.valor <= 0:
            raise DomainError("Quantidade de baixa deve ser maior que zero", "quantidade_invalida")
        if self.quantidade_estoque.valor < quantidade.valor:
            raise DomainError(
                f"Estoque insuficiente de {self.nome}. Disponível: {self.quantidade_estoque.valor}",
                "estoque_insuficiente",
            )
        self.quantidade_estoque = Quantidade(self.quantidade_estoque.valor - quantidade.valor)
        self.atualizado_em = now()
        self._registrar(
            EstoqueDecrementado(
                agregado_id=self.id,
                quantidade=quantidade.valor,
                saldo=self.quantidade_estoque.valor,
            )
        )
