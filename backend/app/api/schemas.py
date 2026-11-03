"""DTOs HTTP. Não são entidades de domínio."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _preco(valor: Decimal) -> Decimal:
    if valor < 0:
        raise ValueError("Preço não pode ser negativo")
    expoente = valor.as_tuple().exponent
    if isinstance(expoente, int) and expoente < -2:
        raise ValueError("Preço deve ter no máximo 2 casas decimais")
    return valor


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=80, examples=["admin"])
    password: str = Field(min_length=1, max_length=200, examples=["admin123"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    nome: str


class ClienteIn(BaseModel):
    nome: str = Field(min_length=2, max_length=200, examples=["Maria Silva"])
    documento: str = Field(min_length=11, max_length=18, examples=["529.982.247-25"])
    email: str | None = Field(default=None, examples=["maria@example.com"])
    telefone: str | None = Field(default=None, examples=["11988887777"])


class ClienteUpdate(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    email: str | None = None
    telefone: str | None = None


class ClienteOut(BaseModel):
    id: UUID
    nome: str
    documento: str
    tipo_documento: str
    email: str | None
    telefone: str | None
    criado_em: str
    atualizado_em: str


class VeiculoIn(BaseModel):
    cliente_id: UUID
    placa: str = Field(min_length=7, max_length=8, examples=["ABC1D23"])
    marca: str = Field(min_length=1, max_length=80, examples=["Fiat"])
    modelo: str = Field(min_length=1, max_length=80, examples=["Argo"])
    ano: int = Field(ge=1900, le=2100, examples=[2022])


class VeiculoUpdate(BaseModel):
    marca: str = Field(min_length=1, max_length=80)
    modelo: str = Field(min_length=1, max_length=80)
    ano: int = Field(ge=1900, le=2100)


class VeiculoOut(BaseModel):
    id: UUID
    cliente_id: UUID
    placa: str
    padrao_placa: str
    marca: str
    modelo: str
    ano: int
    criado_em: str
    atualizado_em: str


class ServicoIn(BaseModel):
    nome: str = Field(min_length=2, max_length=200, examples=["Troca de óleo"])
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal = Field(examples=["150.00"])

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, valor: Decimal) -> Decimal:
        return _preco(valor)


class ServicoOut(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    preco: str
    criado_em: str
    atualizado_em: str


class PecaIn(BaseModel):
    nome: str = Field(min_length=2, max_length=200, examples=["Filtro de óleo"])
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal = Field(examples=["35.00"])
    quantidade_estoque: int = Field(default=0, ge=0, examples=[20])

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, valor: Decimal) -> Decimal:
        return _preco(valor)


class PecaUpdate(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    descricao: str | None = Field(default=None, max_length=500)
    preco: Decimal

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, valor: Decimal) -> Decimal:
        return _preco(valor)


class EntradaEstoqueIn(BaseModel):
    quantidade: int = Field(ge=1, examples=[5])


class AjusteEstoqueIn(BaseModel):
    quantidade: int = Field(ge=0, examples=[10])


class EventoOut(BaseModel):
    id: int
    nome: str
    agregado_tipo: str
    ocorrido_em: str
    payload: dict


class PecaOut(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    preco: str
    quantidade_estoque: int
    criado_em: str
    atualizado_em: str


class PecaDetalheOut(PecaOut):
    eventos: list[EventoOut]


class AbrirOrdemIn(BaseModel):
    documento: str = Field(examples=["529.982.247-25"])
    nome: str | None = Field(default=None, examples=["Maria Silva"])
    email: str | None = None
    telefone: str | None = None
    placa: str = Field(examples=["ABC1D23"])
    marca: str = Field(examples=["Fiat"])
    modelo: str = Field(examples=["Argo"])
    ano: int = Field(ge=1900, le=2100, examples=[2022])
    observacao: str | None = Field(default=None, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documento": "529.982.247-25",
                "nome": "Maria Silva",
                "email": "maria@example.com",
                "telefone": "11988887777",
                "placa": "ABC1D23",
                "marca": "Fiat",
                "modelo": "Argo",
                "ano": 2022,
                "observacao": "Barulho na suspensão",
            }
        }
    )


class DiagnosticoIn(BaseModel):
    observacao: str | None = Field(default=None, max_length=2000)


class IncluirServicoIn(BaseModel):
    servico_id: UUID


class IncluirPecaIn(BaseModel):
    peca_id: UUID
    quantidade: int = Field(ge=1)


class DecisaoOrcamentoIn(BaseModel):
    documento: str = Field(examples=["529.982.247-25"])
    motivo: str | None = Field(default=None, max_length=500)


class ClienteResumoOut(BaseModel):
    id: UUID
    nome: str
    documento: str
    tipo_documento: str


class VeiculoResumoOut(BaseModel):
    id: UUID
    placa: str
    marca: str
    modelo: str
    ano: int


class ItemServicoOut(BaseModel):
    id: UUID
    servico_id: UUID
    descricao: str
    preco: str


class ItemPecaOut(BaseModel):
    id: UUID
    peca_id: UUID
    nome: str
    quantidade: int
    preco_unitario: str
    subtotal: str


class OrcamentoOut(BaseModel):
    id: UUID
    valor_servicos: str
    valor_pecas: str
    valor_total: str
    situacao: str
    gerado_em: str
    decidido_em: str | None
    motivo_rejeicao: str | None


class MarcoOut(BaseModel):
    status: str
    descricao: str
    ocorrido_em: str


class ResumoOrdemOut(BaseModel):
    id: UUID
    numero: int
    status: str
    status_descricao: str
    cliente_id: UUID
    cliente_nome: str
    veiculo_id: UUID
    placa: str
    valor_orcamento: str | None
    aberta_em: str


class OrdemOut(BaseModel):
    id: UUID
    numero: int
    status: str
    status_descricao: str
    observacao: str | None
    cliente: ClienteResumoOut
    veiculo: VeiculoResumoOut
    itens_servico: list[ItemServicoOut]
    itens_peca: list[ItemPecaOut]
    orcamento: OrcamentoOut | None
    marcos: list[MarcoOut]
    aberta_em: str
    diagnostico_iniciado_em: str | None
    orcamento_gerado_em: str | None
    execucao_iniciada_em: str | None
    finalizada_em: str | None
    entregue_em: str | None


class OrdemDetalheOut(OrdemOut):
    eventos: list[EventoOut]


class TempoMedioOut(BaseModel):
    quantidade_os: int
    tempo_medio_segundos: float | None
    tempo_medio_horas: float | None


class ListaOut(BaseModel):
    itens: list
    total: int
    limite: int
    offset: int


class ListaClientesOut(BaseModel):
    itens: list[ClienteOut]
    total: int
    limite: int
    offset: int


class ListaVeiculosOut(BaseModel):
    itens: list[VeiculoOut]
    total: int
    limite: int
    offset: int


class ListaServicosOut(BaseModel):
    itens: list[ServicoOut]
    total: int
    limite: int
    offset: int


class ListaPecasOut(BaseModel):
    itens: list[PecaOut]
    total: int
    limite: int
    offset: int


class ListaOrdensOut(BaseModel):
    itens: list[ResumoOrdemOut]
    total: int
    limite: int
    offset: int


class ErroOut(BaseModel):
    codigo: str
    mensagem: str
    erros: list[dict[str, Any]] | None = Field(default=None, description="Detalhes por campo, só em erro de validação")


_DESCRICOES_ERRO = {
    401: "Credenciais ou token ausentes, inválidos ou expirados",
    404: "Registro não encontrado",
    409: "Conflito com o estado atual: transição inválida, duplicidade, estoque insuficiente ou vínculo existente",
    422: "Dados inválidos",
}


def respostas_erro(*codigos: int) -> dict[int | str, dict[str, Any]]:
    """Documenta no OpenAPI as respostas de erro, todas no formato de ErroOut."""
    return {codigo: {"model": ErroOut, "description": _DESCRICOES_ERRO[codigo]} for codigo in codigos}
