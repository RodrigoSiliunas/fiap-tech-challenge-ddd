"""Modelos ORM. Não são o modelo de domínio — apenas a persistência."""

from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from oficina.domain.ordem_servico.status import SituacaoOrcamento, StatusOS


class Base(DeclarativeBase):
    pass


def _status_in() -> str:
    valores = ", ".join(f"'{status.value}'" for status in StatusOS)
    return f"status IN ({valores})"


def _situacao_in() -> str:
    valores = ", ".join(f"'{situacao.value}'" for situacao in SituacaoOrcamento)
    return f"situacao IN ({valores})"


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)


class SequenciaModel(Base):
    __tablename__ = "sequencias"

    nome: Mapped[str] = mapped_column(String(50), primary_key=True)
    valor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ClienteModel(Base):
    __tablename__ = "clientes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    documento: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    tipo_documento: Mapped[str] = mapped_column(String(4), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200))
    telefone: Mapped[str | None] = mapped_column(String(13))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VeiculoModel(Base):
    __tablename__ = "veiculos"
    __table_args__ = (CheckConstraint("ano >= 1900", name="ck_veiculo_ano"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True)
    placa: Mapped[str] = mapped_column(String(7), unique=True, nullable=False)
    padrao_placa: Mapped[str] = mapped_column(String(10), nullable=False)
    marca: Mapped[str] = mapped_column(String(80), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ServicoModel(Base):
    __tablename__ = "servicos"
    __table_args__ = (CheckConstraint("preco_centavos >= 0", name="ck_servico_preco"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    preco_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PecaModel(Base):
    __tablename__ = "pecas"
    __table_args__ = (
        CheckConstraint("preco_centavos >= 0", name="ck_peca_preco"),
        CheckConstraint("quantidade_estoque >= 0", name="ck_peca_estoque"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    preco_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_estoque: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OrdemModel(Base):
    __tablename__ = "ordens_servico"
    __table_args__ = (
        UniqueConstraint("numero", name="uq_os_numero"),
        CheckConstraint(_status_in(), name="ck_os_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True)
    veiculo_id: Mapped[str] = mapped_column(ForeignKey("veiculos.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    observacao: Mapped[str | None] = mapped_column(Text)
    aberta_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    diagnostico_iniciado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    orcamento_gerado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execucao_iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    itens_servico: Mapped[list["ItemServicoModel"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        back_populates="ordem",
    )
    itens_peca: Mapped[list["ItemPecaModel"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        back_populates="ordem",
    )
    orcamento: Mapped["OrcamentoModel | None"] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
        back_populates="ordem",
    )


class ItemServicoModel(Base):
    __tablename__ = "itens_servico"
    __table_args__ = (CheckConstraint("preco_centavos >= 0", name="ck_item_servico_preco"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ordem_id: Mapped[str] = mapped_column(ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False, index=True)
    servico_id: Mapped[str] = mapped_column(ForeignKey("servicos.id", ondelete="RESTRICT"), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    preco_centavos: Mapped[int] = mapped_column(Integer, nullable=False)

    ordem: Mapped[OrdemModel] = relationship(back_populates="itens_servico")


class ItemPecaModel(Base):
    __tablename__ = "itens_peca"
    __table_args__ = (
        CheckConstraint("preco_unitario_centavos >= 0", name="ck_item_peca_preco"),
        CheckConstraint("quantidade >= 1", name="ck_item_peca_quantidade"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ordem_id: Mapped[str] = mapped_column(ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False, index=True)
    peca_id: Mapped[str] = mapped_column(ForeignKey("pecas.id", ondelete="RESTRICT"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario_centavos: Mapped[int] = mapped_column(Integer, nullable=False)

    ordem: Mapped[OrdemModel] = relationship(back_populates="itens_peca")


class OrcamentoModel(Base):
    __tablename__ = "orcamentos"
    __table_args__ = (
        UniqueConstraint("ordem_id", name="uq_orcamento_ordem"),
        CheckConstraint("valor_servicos_centavos >= 0", name="ck_orcamento_servicos"),
        CheckConstraint("valor_pecas_centavos >= 0", name="ck_orcamento_pecas"),
        CheckConstraint("valor_total_centavos >= 0", name="ck_orcamento_total"),
        CheckConstraint(_situacao_in(), name="ck_orcamento_situacao"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    ordem_id: Mapped[str] = mapped_column(ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False)
    valor_servicos_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_pecas_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_total_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False)
    gerado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decidido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_rejeicao: Mapped[str | None] = mapped_column(Text)

    ordem: Mapped[OrdemModel] = relationship(back_populates="orcamento")


class EventoDominioModel(Base):
    __tablename__ = "eventos_dominio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    agregado_tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    agregado_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
