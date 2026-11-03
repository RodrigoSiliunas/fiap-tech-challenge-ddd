"""Testes de unidade dos agregados, objetos de valor e políticas."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.cliente.aggregate import Cliente
from app.domain.cliente.documento import Documento, TipoDocumento
from app.domain.exceptions import DomainError
from app.domain.ordem_servico.aggregate import OrdemDeServico
from app.domain.ordem_servico.status import StatusOS
from app.domain.peca.aggregate import Peca
from app.domain.servico.aggregate import Servico
from app.domain.services.politica_estoque import PoliticaBaixaEstoque, PoliticaDisponibilidadeEstoque
from app.domain.shared.clock import reset_clock, set_clock
from app.domain.shared.validacao import validar_email, validar_telefone
from app.domain.shared.value_objects import Dinheiro, Quantidade, somar_dinheiros
from app.domain.veiculo.aggregate import Veiculo
from app.domain.veiculo.placa import PadraoPlaca, Placa
from app.application.support import paginar

CPF = "529.982.247-25"
CNPJ = "11.444.777/0001-61"


@pytest.fixture(autouse=True)
def _relogio():
    yield
    reset_clock()


def test_cpf_e_cnpj_validos_e_formatados():
    cpf = Documento.criar(CPF)
    assert cpf.tipo == TipoDocumento.CPF
    assert cpf.valor == "52998224725"
    assert cpf.formatado() == "529.982.247-25"
    cnpj = Documento.criar(CNPJ)
    assert cnpj.tipo == TipoDocumento.CNPJ
    assert cnpj.formatado() == "11.444.777/0001-61"
    assert cpf == Documento.criar("52998224725")


@pytest.mark.parametrize(
    "bruto",
    ["", "123", "111.111.111-11", "00000000000000", "529.982.247-24", "11.444.777/0001-60", "abc"],
)
def test_documento_invalido(bruto):
    with pytest.raises(DomainError) as erro:
        Documento.criar(bruto)
    assert erro.value.codigo == "documento_invalido"


def test_documento_construido_direto_revalida():
    with pytest.raises(DomainError):
        Documento("00000000000", TipoDocumento.CPF)


def test_placas_antiga_e_mercosul():
    antiga = Placa.criar("abc-1234")
    assert antiga.padrao == PadraoPlaca.ANTIGA
    assert antiga.valor == "ABC1234"
    assert antiga.formatada() == "ABC-1234"
    mercosul = Placa.criar("abc1d23")
    assert mercosul.padrao == PadraoPlaca.MERCOSUL
    assert mercosul.valor == "ABC1D23"
    assert mercosul.formatada() == "ABC1D23"


@pytest.mark.parametrize("bruto", ["", "ABC123", "ABCD123", "1234ABC", "AB12C34", "AAA00000"])
def test_placa_invalida(bruto):
    with pytest.raises(DomainError) as erro:
        Placa.criar(bruto)
    assert erro.value.codigo == "placa_invalida"


def test_placa_padrao_inconsistente():
    with pytest.raises(DomainError):
        Placa("ABC123", PadraoPlaca.ANTIGA)


def test_dinheiro_e_quantidade():
    a = Dinheiro.de_decimal(Decimal("10.50"))
    b = Dinheiro.de_decimal("2")
    assert a.centavos == 1050
    assert a.somar(b).formatado() == "12.50"
    assert a.multiplicar(3).centavos == 3150
    assert somar_dinheiros([a, b]).formatado() == "12.50"
    assert Dinheiro.zero().centavos == 0
    assert Quantidade(0).valor == 0
    assert Quantidade.positiva(2).valor == 2
    with pytest.raises(DomainError):
        Dinheiro(-1)
    with pytest.raises(DomainError):
        Dinheiro(True)  # type: ignore[arg-type]
    with pytest.raises(DomainError):
        Dinheiro(1, "USD")
    with pytest.raises(DomainError):
        Dinheiro.de_decimal(Decimal("-0.01"))
    with pytest.raises(DomainError):
        Dinheiro.de_decimal(1.5)  # type: ignore[arg-type]
    with pytest.raises(DomainError):
        a.multiplicar(-1)
    with pytest.raises(DomainError):
        Quantidade(-1)
    with pytest.raises(DomainError):
        Quantidade.positiva(0)
    with pytest.raises(DomainError):
        Quantidade(True)  # type: ignore[arg-type]


def test_validacoes_de_contato_e_paginacao():
    assert validar_email(None) is None
    assert validar_email("  Maria@Example.com ") == "maria@example.com"
    with pytest.raises(DomainError):
        validar_email("sem-arroba")
    assert validar_telefone("(11) 98888-7777") == "11988887777"
    with pytest.raises(DomainError):
        validar_telefone("123")
    assert paginar(20, 0) == (20, 0)
    with pytest.raises(DomainError):
        paginar(0, 0)
    with pytest.raises(DomainError):
        paginar(20, -1)


def test_cliente_veiculo_servico_e_peca():
    cliente = Cliente.cadastrar("Maria Silva", Documento.criar(CPF), "maria@example.com", "11988887777")
    assert [evento.nome_evento for evento in cliente.pull_events()] == ["ClienteCadastrado"]
    cliente.identificar()
    cliente.atualizar("Maria S. Silva", None, None)
    assert [evento.nome_evento for evento in cliente.pull_events()] == ["ClienteIdentificado", "ClienteAtualizado"]
    with pytest.raises(DomainError):
        Cliente.cadastrar("A", Documento.criar(CPF))

    veiculo = Veiculo.registrar(cliente.id, Placa.criar("ABC1D23"), "Fiat", "Argo", 2022)
    veiculo.atualizar("VW", "Gol", 2020)
    assert [evento.nome_evento for evento in veiculo.pull_events()] == ["VeiculoRegistrado", "VeiculoAtualizado"]
    with pytest.raises(DomainError):
        Veiculo.registrar(cliente.id, Placa.criar("ABC1234"), "Fiat", "Uno", 1800)

    servico = Servico.cadastrar("Troca de óleo", Dinheiro.de_decimal("150.00"), "  ")
    servico.atualizar("Troca de óleo completa", Dinheiro.de_decimal("180.00"), "Com filtro")
    assert servico.descricao == "Com filtro"
    assert [evento.nome_evento for evento in servico.pull_events()] == [
        "ServicoCatalogoCadastrado",
        "ServicoCatalogoAtualizado",
    ]

    peca = Peca.cadastrar("Filtro", Dinheiro.de_decimal("35.00"), Quantidade(2))
    peca.registrar_entrada(Quantidade.positiva(3))
    assert peca.quantidade_estoque.valor == 5
    peca.ajustar_estoque(Quantidade(1))
    peca.baixar(Quantidade.positiva(1))
    assert peca.quantidade_estoque.valor == 0
    with pytest.raises(DomainError) as erro:
        peca.baixar(Quantidade.positiva(1))
    assert erro.value.codigo == "estoque_insuficiente"
    assert peca.quantidade_estoque.valor == 0
    with pytest.raises(DomainError):
        peca.registrar_entrada(Quantidade(0))
    with pytest.raises(DomainError):
        peca.baixar(Quantidade(0))
    nomes = [evento.nome_evento for evento in peca.pull_events()]
    assert nomes == ["PecaCadastrada", "EstoqueIncrementado", "EstoqueAjustado", "EstoqueDecrementado"]


def _ordem_com_itens() -> tuple[OrdemDeServico, Peca]:
    cliente_id = uuid4()
    veiculo_id = uuid4()
    ordem = OrdemDeServico.abrir(numero=1, cliente_id=cliente_id, veiculo_id=veiculo_id, observacao="barulho")
    ordem.iniciar_diagnostico("suspensão")
    servico_id = uuid4()
    ordem.incluir_servico(servico_id, "Troca de óleo", Dinheiro.de_decimal("100.50"))
    ordem.incluir_servico(uuid4(), "Alinhamento", Dinheiro.de_decimal("50.00"))
    peca = Peca.cadastrar("Óleo", Dinheiro.de_decimal("10.00"), Quantidade(5))
    ordem.incluir_peca(peca.id, peca.nome, Quantidade.positiva(3), Dinheiro.de_decimal("10.00"))
    ordem.incluir_peca(uuid4(), "Filtro", Quantidade.positiva(2), Dinheiro.de_decimal("5.25"))
    return ordem, peca


def test_fluxo_feliz_da_os_calcula_orcamento_e_rejeita_atalhos():
    ordem, peca = _ordem_com_itens()
    with pytest.raises(DomainError) as duplicado:
        ordem.incluir_servico(ordem.itens_servico[0].servico_id, "Outra", Dinheiro.zero())
    assert duplicado.value.codigo == "servico_duplicado"

    ordem.incluir_peca(peca.id, peca.nome, Quantidade.positiva(1), Dinheiro.de_decimal("99.00"))
    assert ordem.quantidade_da_peca(peca.id) == 4
    assert ordem.itens_peca[0].preco_unitario.centavos == 1000

    orcamento = ordem.gerar_orcamento()
    assert ordem.status == StatusOS.AGUARDANDO_APROVACAO
    # serviços 150.50 + peças (10*4=40) + (5.25*2=10.50) = 201.00
    assert orcamento.valor_servicos.formatado() == "150.50"
    assert orcamento.valor_pecas.formatado() == "50.50"
    assert orcamento.valor_total.formatado() == "201.00"

    ordem.remover_peca(ordem.itens_peca[1].id)
    assert ordem.orcamento is not None
    assert ordem.orcamento.valor_total.formatado() == "190.50"
    assert ordem.status == StatusOS.AGUARDANDO_APROVACAO

    with pytest.raises(DomainError):
        ordem.remover_servico(ordem.itens_servico[0].id)
        ordem.remover_servico(ordem.itens_servico[0].id)

    ordem.aprovar_orcamento()
    assert ordem.status == StatusOS.EM_EXECUCAO
    assert ordem.execucao_iniciada_em == ordem.orcamento.decidido_em
    PoliticaBaixaEstoque().aplicar(ordem, {peca.id: peca})
    assert peca.quantidade_estoque.valor == 1

    with pytest.raises(DomainError) as bloqueado:
        ordem.incluir_servico(uuid4(), "Extra", Dinheiro.de_decimal("10.00"))
    assert bloqueado.value.codigo == "itens_bloqueados"

    ordem.finalizar()
    ordem.entregar()
    assert ordem.status == StatusOS.ENTREGUE
    assert ordem.status.encerrada()
    with pytest.raises(DomainError) as invalida:
        ordem.finalizar()
    assert invalida.value.codigo == "transicao_invalida"
    assert ordem.status == StatusOS.ENTREGUE

    nomes = [evento.nome_evento for evento in ordem.pull_events()]
    assert "OrdemDeServicoRecebida" in nomes
    assert "OrcamentoGerado" in nomes
    assert "OrcamentoDisponibilizado" in nomes
    assert "OrcamentoAprovado" in nomes
    assert "ExecucaoIniciada" in nomes
    assert "ServicoFinalizado" in nomes
    assert "VeiculoEntregue" in nomes


def test_rejeicao_e_transicoes_proibidas():
    ordem = OrdemDeServico.abrir(numero=2, cliente_id=uuid4(), veiculo_id=uuid4())
    with pytest.raises(DomainError):
        ordem.incluir_servico(uuid4(), "Troca", Dinheiro.de_decimal("10"))
    with pytest.raises(DomainError):
        ordem.gerar_orcamento()
    with pytest.raises(DomainError):
        ordem.entregar()
    with pytest.raises(DomainError):
        OrdemDeServico.abrir(numero=0, cliente_id=uuid4(), veiculo_id=uuid4())

    ordem.iniciar_diagnostico()
    with pytest.raises(DomainError) as sem_servico:
        ordem.gerar_orcamento()
    assert sem_servico.value.codigo == "orcamento_sem_servico"
    ordem.incluir_servico(uuid4(), "Alinhamento", Dinheiro.de_decimal("80"))
    with pytest.raises(DomainError):
        ordem.incluir_peca(uuid4(), " ", Quantidade.positiva(1), Dinheiro.zero())
    with pytest.raises(DomainError):
        ordem.remover_servico(uuid4())
    with pytest.raises(DomainError):
        ordem.remover_peca(uuid4())

    ordem.gerar_orcamento()
    ordem.rejeitar_orcamento("Cliente desistiu")
    assert ordem.status == StatusOS.REJEITADA
    assert ordem.orcamento is not None
    assert ordem.orcamento.motivo_rejeicao == "Cliente desistiu"
    assert ordem.status.encerrada()
    with pytest.raises(DomainError):
        ordem.aprovar_orcamento()


def test_politica_de_disponibilidade_e_peca_ausente():
    peca = Peca.cadastrar("Pastilha", Dinheiro.de_decimal("10"), Quantidade(1))
    PoliticaDisponibilidadeEstoque().validar(peca, 1)
    with pytest.raises(DomainError) as erro:
        PoliticaDisponibilidadeEstoque().validar(peca, 2)
    assert erro.value.codigo == "estoque_insuficiente"
    with pytest.raises(DomainError):
        PoliticaDisponibilidadeEstoque().validar(peca, -1)

    ordem = OrdemDeServico.abrir(numero=3, cliente_id=uuid4(), veiculo_id=uuid4())
    ordem.iniciar_diagnostico()
    ordem.incluir_servico(uuid4(), "Freio", Dinheiro.de_decimal("10"))
    ordem.incluir_peca(uuid4(), "Pastilha", Quantidade.positiva(1), Dinheiro.de_decimal("10"))
    ordem.gerar_orcamento()
    ordem.aprovar_orcamento()
    with pytest.raises(DomainError) as ausente:
        PoliticaBaixaEstoque().aplicar(ordem, {})
    assert ausente.value.codigo == "nao_encontrado"


def test_descricao_longa_e_relogio_injetado():
    instante = datetime(2024, 1, 1, tzinfo=timezone.utc)
    set_clock(lambda: instante)
    cliente = Cliente.cadastrar("Ana Lima", Documento.criar(CNPJ))
    assert cliente.criado_em == instante
    with pytest.raises(DomainError):
        Servico.cadastrar("Nome", Dinheiro.zero(), "x" * 501)
