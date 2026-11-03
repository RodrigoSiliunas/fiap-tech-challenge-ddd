"""Agregado Cliente. Documento é identidade fiscal imutável."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from oficina.domain.cliente.documento import Documento
from oficina.domain.cliente.events import ClienteAtualizado, ClienteCadastrado, ClienteIdentificado
from oficina.domain.shared.aggregate import RaizAgregado
from oficina.domain.shared.clock import now
from oficina.domain.shared.events import DomainEvent
from oficina.domain.shared.validacao import validar_email, validar_nome, validar_telefone


@dataclass
class Cliente(RaizAgregado):
    id: UUID
    nome: str
    documento: Documento
    email: str | None
    telefone: str | None
    criado_em: datetime
    atualizado_em: datetime
    _events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def cadastrar(
        cls,
        nome: str,
        documento: Documento,
        email: str | None = None,
        telefone: str | None = None,
    ) -> "Cliente":
        instante = now()
        cliente = cls(
            id=uuid4(),
            nome=validar_nome(nome, "Nome do cliente"),
            documento=documento,
            email=validar_email(email),
            telefone=validar_telefone(telefone),
            criado_em=instante,
            atualizado_em=instante,
        )
        cliente._registrar(
            ClienteCadastrado(
                agregado_id=cliente.id,
                nome=cliente.nome,
                documento=cliente.documento.valor,
            )
        )
        return cliente

    def identificar(self) -> None:
        """Comando IdentificarCliente quando o cliente já existe no cadastro."""
        self._registrar(ClienteIdentificado(agregado_id=self.id, documento=self.documento.valor))

    def atualizar(self, nome: str, email: str | None, telefone: str | None) -> None:
        self.nome = validar_nome(nome, "Nome do cliente")
        self.email = validar_email(email)
        self.telefone = validar_telefone(telefone)
        self.atualizado_em = now()
        self._registrar(ClienteAtualizado(agregado_id=self.id, nome=self.nome))
