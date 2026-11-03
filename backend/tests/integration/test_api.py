"""Fluxos principais via API, com transação real (SQLite ou Postgres)."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from oficina.infrastructure.db.models import OrdemModel

CPF = "529.982.247-25"
CPF_2 = "111.444.777-35"
CNPJ = "11.444.777/0001-61"


def _servico(client, auth, nome="Troca de óleo", preco="150.00"):
    resposta = client.post(
        "/api/v1/servicos",
        headers=auth,
        json={"nome": nome, "preco": preco, "descricao": nome},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _peca(client, auth, nome="Filtro de óleo", preco="35.00", estoque=10):
    resposta = client.post(
        "/api/v1/pecas",
        headers=auth,
        json={"nome": nome, "preco": preco, "quantidade_estoque": estoque, "descricao": nome},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _abrir(client, auth, documento=CPF, nome="Maria Silva", placa="ABC1D23", marca="Fiat", modelo="Argo", ano=2022):
    resposta = client.post(
        "/api/v1/ordens-servico",
        headers=auth,
        json={
            "documento": documento,
            "nome": nome,
            "email": "maria@example.com",
            "telefone": "11988887777",
            "placa": placa,
            "marca": marca,
            "modelo": modelo,
            "ano": ano,
            "observacao": "Barulho",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _ate_orcamento(client, auth, placa="ABC1D23", documento=CPF, pecas=1):
    servico = _servico(client, auth, nome=f"Serviço {placa}", preco="150.00")
    peca = _peca(client, auth, nome=f"Peça {placa}", preco="45.00", estoque=5)
    ordem = _abrir(client, auth, documento=documento, placa=placa)
    ordem_id = ordem["id"]
    diag = client.post(
        f"/api/v1/ordens-servico/{ordem_id}/diagnostico",
        headers=auth,
        json={"observacao": "Em bancada"},
    )
    assert diag.status_code == 200, diag.text
    incluido = client.post(
        f"/api/v1/ordens-servico/{ordem_id}/servicos",
        headers=auth,
        json={"servico_id": servico["id"]},
    )
    assert incluido.status_code == 200, incluido.text
    item_servico = incluido.json()["itens_servico"][0]["id"]
    for _ in range(pecas):
        peca_resp = client.post(
            f"/api/v1/ordens-servico/{ordem_id}/pecas",
            headers=auth,
            json={"peca_id": peca["id"], "quantidade": 2},
        )
        assert peca_resp.status_code == 200, peca_resp.text
    orcamento = client.post(f"/api/v1/ordens-servico/{ordem_id}/orcamento", headers=auth)
    assert orcamento.status_code == 200, orcamento.text
    return orcamento.json(), servico, peca, item_servico


def test_health_login_e_rotas_protegidas(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/", follow_redirects=False).status_code in {302, 307}
    assert client.get("/api/v1/clientes").status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": "admin", "password": "errada"}).status_code == 401
    assert client.get("/api/v1/clientes", headers={"Authorization": "Bearer token-invalido"}).status_code == 401


def test_crud_cliente_veiculo_servico_peca(client, auth):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth,
        json={"nome": "João Souza", "documento": CPF_2, "email": "joao@example.com", "telefone": "11977776666"},
    )
    assert cliente.status_code == 201, cliente.text
    cliente_id = cliente.json()["id"]
    assert cliente.json()["tipo_documento"] == "CPF"
    assert client.get(f"/api/v1/clientes/{cliente_id}", headers=auth).status_code == 200
    atualizado = client.put(
        f"/api/v1/clientes/{cliente_id}",
        headers=auth,
        json={"nome": "João S. Souza", "email": None, "telefone": None},
    )
    assert atualizado.status_code == 200
    assert atualizado.json()["nome"] == "João S. Souza"

    repetido = client.post(
        "/api/v1/clientes",
        headers=auth,
        json={"nome": "Outro", "documento": CPF_2},
    )
    assert repetido.status_code == 409
    invalido = client.post(
        "/api/v1/clientes",
        headers=auth,
        json={"nome": "Inválido", "documento": "111.111.111-11"},
    )
    assert invalido.status_code == 422

    veiculo = client.post(
        "/api/v1/veiculos",
        headers=auth,
        json={"cliente_id": cliente_id, "placa": "abc-1234", "marca": "Ford", "modelo": "Ka", "ano": 2018},
    )
    assert veiculo.status_code == 201, veiculo.text
    assert veiculo.json()["padrao_placa"] == "ANTIGA"
    assert veiculo.json()["placa"] == "ABC-1234"
    veiculo_id = veiculo.json()["id"]
    mercosul = client.post(
        "/api/v1/veiculos",
        headers=auth,
        json={"cliente_id": cliente_id, "placa": "def5g78", "marca": "VW", "modelo": "Gol", "ano": 2024},
    )
    assert mercosul.status_code == 201
    assert mercosul.json()["padrao_placa"] == "MERCOSUL"
    placa_ruim = client.post(
        "/api/v1/veiculos",
        headers=auth,
        json={"cliente_id": cliente_id, "placa": "ABC123", "marca": "Fiat", "modelo": "Uno", "ano": 2010},
    )
    assert placa_ruim.status_code == 422
    placa_duplicada = client.post(
        "/api/v1/veiculos",
        headers=auth,
        json={"cliente_id": cliente_id, "placa": "ABC1234", "marca": "Fiat", "modelo": "Uno", "ano": 2010},
    )
    assert placa_duplicada.status_code == 409
    assert client.put(
        f"/api/v1/veiculos/{veiculo_id}",
        headers=auth,
        json={"marca": "Ford", "modelo": "Ka Sedan", "ano": 2019},
    ).status_code == 200
    listagem = client.get(f"/api/v1/veiculos?cliente_id={cliente_id}", headers=auth)
    assert listagem.status_code == 200
    assert listagem.json()["total"] >= 1

    servico = _servico(client, auth, "Balanceamento", "80.00")
    assert client.put(
        f"/api/v1/servicos/{servico['id']}",
        headers=auth,
        json={"nome": "Balanceamento computadorizado", "preco": "90.00", "descricao": "4 rodas"},
    ).status_code == 200
    peca = _peca(client, auth, "Pastilha", "180.00", 2)
    entrada = client.post(
        f"/api/v1/pecas/{peca['id']}/entrada-estoque",
        headers=auth,
        json={"quantidade": 3},
    )
    assert entrada.json()["quantidade_estoque"] == 5
    ajuste = client.post(
        f"/api/v1/pecas/{peca['id']}/ajuste-estoque",
        headers=auth,
        json={"quantidade": 4},
    )
    assert ajuste.json()["quantidade_estoque"] == 4
    assert "EstoqueAjustado" in [evento["nome"] for evento in client.get(f"/api/v1/pecas/{peca['id']}", headers=auth).json()["eventos"]]
    assert client.post(
        f"/api/v1/pecas/{peca['id']}/ajuste-estoque",
        headers=auth,
        json={"quantidade": -1},
    ).status_code == 422

    assert client.delete(f"/api/v1/veiculos/{mercosul.json()['id']}", headers=auth).status_code == 204
    assert client.delete(f"/api/v1/servicos/{servico['id']}", headers=auth).status_code == 204
    assert client.delete(f"/api/v1/pecas/{peca['id']}", headers=auth).status_code == 204
    assert client.delete(f"/api/v1/veiculos/{veiculo_id}", headers=auth).status_code == 204
    assert client.delete(f"/api/v1/clientes/{cliente_id}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/clientes/{cliente_id}", headers=auth).status_code == 404
    assert client.get(f"/api/v1/clientes/{uuid4()}", headers=auth).status_code == 404


def test_fluxo_feliz_os_aprovacao_estoque_e_tempo_medio(client, auth):
    ordem, servico, peca, _item = _ate_orcamento(client, auth)
    ordem_id = ordem["id"]
    assert ordem["status"] == "AGUARDANDO_APROVACAO"
    assert ordem["status_descricao"] == "Aguardando aprovação"
    # 150 de serviço + 2 * 45 de peça = 240
    assert ordem["orcamento"]["valor_total"] == "240.00"
    assert ordem["orcamento"]["situacao"] == "GERADO"
    eventos = [evento["nome"] for evento in ordem["eventos"]]
    assert "OrdemDeServicoRecebida" in eventos
    assert "OrcamentoGerado" in eventos
    assert "OrcamentoDisponibilizado" in eventos

    # Preço do catálogo muda; o item da OS permanece com o snapshot.
    client.put(
        f"/api/v1/servicos/{servico['id']}",
        headers=auth,
        json={"nome": servico["nome"], "preco": "999.00", "descricao": None},
    )
    consulta = client.get(
        f"/api/v1/publico/ordens-servico/{ordem_id}",
        params={"documento": CPF},
    )
    assert consulta.status_code == 200, consulta.text
    assert consulta.json()["itens_servico"][0]["preco"] == "150.00"
    assert consulta.json()["status"] == "AGUARDANDO_APROVACAO"
    assert client.get(
        f"/api/v1/publico/ordens-servico/{ordem_id}",
        params={"documento": CPF_2},
    ).status_code == 404

    # Incluir a mesma peça de novo soma a quantidade e recalcula o orçamento.
    somada = client.post(
        f"/api/v1/ordens-servico/{ordem_id}/pecas",
        headers=auth,
        json={"peca_id": peca["id"], "quantidade": 1},
    )
    assert somada.status_code == 200, somada.text
    assert somada.json()["itens_peca"][0]["quantidade"] == 3
    assert somada.json()["orcamento"]["valor_total"] == "285.00"
    assert somada.json()["status"] == "AGUARDANDO_APROVACAO"

    sem_estoque = client.post(
        f"/api/v1/ordens-servico/{ordem_id}/pecas",
        headers=auth,
        json={"peca_id": peca["id"], "quantidade": 50},
    )
    assert sem_estoque.status_code == 409

    aprovada = client.post(
        f"/api/v1/publico/ordens-servico/{ordem_id}/aprovar",
        json={"documento": "52998224725"},
    )
    assert aprovada.status_code == 200, aprovada.text
    assert aprovada.json()["status"] == "EM_EXECUCAO"
    saldo = client.get(f"/api/v1/pecas/{peca['id']}", headers=auth).json()
    assert saldo["quantidade_estoque"] == 2
    assert "EstoqueDecrementado" in [evento["nome"] for evento in saldo["eventos"]]

    # Aprovar de novo não é transição válida e não mexe no estoque outra vez.
    de_novo = client.post(
        f"/api/v1/publico/ordens-servico/{ordem_id}/aprovar",
        json={"documento": CPF},
    )
    assert de_novo.status_code == 409
    assert client.get(f"/api/v1/pecas/{peca['id']}", headers=auth).json()["quantidade_estoque"] == 2

    finalizada = client.post(f"/api/v1/ordens-servico/{ordem_id}/finalizar", headers=auth)
    assert finalizada.status_code == 200
    entregue = client.post(f"/api/v1/ordens-servico/{ordem_id}/entregar", headers=auth)
    assert entregue.status_code == 200
    assert entregue.json()["status"] == "ENTREGUE"
    assert any(marco["status"] == "ENTREGUE" for marco in entregue.json()["marcos"])

    lista = client.get("/api/v1/ordens-servico", headers=auth, params={"status": "ENTREGUE"})
    assert lista.status_code == 200
    assert lista.json()["total"] == 1
    assert lista.json()["itens"][0]["numero"] == 1
    detalhe = client.get(f"/api/v1/ordens-servico/{ordem_id}", headers=auth)
    assert detalhe.status_code == 200
    assert detalhe.json()["cliente"]["documento"] == "529.982.247-25"

    inicio = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)
    fim = inicio + timedelta(hours=3)
    session = client.factory()
    try:
        row = session.get(OrdemModel, ordem_id)
        row.execucao_iniciada_em = inicio
        row.finalizada_em = fim
        session.commit()
    finally:
        session.close()
    metrica = client.get("/api/v1/metricas/tempo-medio-execucao", headers=auth)
    assert metrica.status_code == 200
    assert metrica.json()["quantidade_os"] == 1
    assert metrica.json()["tempo_medio_segundos"] == 10800
    assert metrica.json()["tempo_medio_horas"] == 3


def test_rejeicao_nao_baixa_estoque_e_permite_nova_os(client, auth):
    ordem, _servico, peca, item_servico = _ate_orcamento(client, auth, placa="BEZ4C21", documento=CNPJ)
    # Remove a peça antes da decisão: orçamento volta a ter só o serviço.
    removida = client.delete(
        f"/api/v1/ordens-servico/{ordem['id']}/pecas/{ordem['itens_peca'][0]['id']}",
        headers=auth,
    )
    assert removida.status_code == 200, removida.text
    assert removida.json()["orcamento"]["valor_pecas"] == "0.00"
    assert removida.json()["orcamento"]["valor_total"] == "150.00"

    rejeitada = client.post(
        f"/api/v1/publico/ordens-servico/{ordem['id']}/rejeitar",
        json={"documento": CNPJ, "motivo": "Valor acima do esperado"},
    )
    assert rejeitada.status_code == 200, rejeitada.text
    assert rejeitada.json()["status"] == "REJEITADA"
    assert rejeitada.json()["orcamento"]["situacao"] == "REJEITADO"
    assert client.get(f"/api/v1/pecas/{peca['id']}", headers=auth).json()["quantidade_estoque"] == 5

    # Serviço usado não pode ser excluído; cliente com OS também não.
    assert client.delete(f"/api/v1/servicos/{_servico['id']}", headers=auth).status_code == 409
    cliente_id = ordem["cliente"]["id"]
    assert client.delete(f"/api/v1/clientes/{cliente_id}", headers=auth).status_code == 409
    assert client.delete(f"/api/v1/veiculos/{ordem['veiculo']['id']}", headers=auth).status_code == 409

    # Depois de encerrada, o mesmo veículo pode abrir outra OS.
    nova = _abrir(client, auth, documento=CNPJ, nome="Oficina Parceira Ltda", placa="BEZ4C21", marca="Honda", modelo="Civic")
    assert nova["numero"] == 2
    assert nova["status"] == "RECEBIDA"
    # A placa já existe: a abertura reutiliza o veículo e não sobrescreve a marca.
    assert nova["veiculo"]["marca"] == "Fiat"
    assert nova["cliente"]["nome"] == "Maria Silva"

    repetida = client.post(
        "/api/v1/ordens-servico",
        headers=auth,
        json={
            "documento": CNPJ,
            "placa": "BEZ4C21",
            "marca": "Honda",
            "modelo": "Civic",
            "ano": 2020,
        },
    )
    assert repetida.status_code == 409

    # Item de serviço removido durante o diagnóstico da nova OS.
    diag = client.post(f"/api/v1/ordens-servico/{nova['id']}/diagnostico", headers=auth, json={})
    assert diag.status_code == 200
    incluido = client.post(
        f"/api/v1/ordens-servico/{nova['id']}/servicos",
        headers=auth,
        json={"servico_id": _servico["id"]},
    )
    item_id = incluido.json()["itens_servico"][0]["id"]
    sem_item = client.delete(f"/api/v1/ordens-servico/{nova['id']}/servicos/{item_id}", headers=auth)
    assert sem_item.status_code == 200
    assert sem_item.json()["itens_servico"] == []
    assert client.post(f"/api/v1/ordens-servico/{nova['id']}/orcamento", headers=auth).status_code == 409
    assert client.post(f"/api/v1/ordens-servico/{nova['id']}/entregar", headers=auth).status_code == 409
    _ = item_servico


def test_aprovacao_sem_estoque_faz_rollback(client, auth):
    ordem, _servico, peca, _item = _ate_orcamento(client, auth, placa="QWE1A23", documento=CPF, pecas=1)
    ajuste = client.post(
        f"/api/v1/pecas/{peca['id']}/ajuste-estoque",
        headers=auth,
        json={"quantidade": 0},
    )
    assert ajuste.status_code == 200
    falha = client.post(
        f"/api/v1/publico/ordens-servico/{ordem['id']}/aprovar",
        json={"documento": CPF},
    )
    assert falha.status_code == 409
    assert falha.json()["codigo"] == "estoque_insuficiente"
    atual = client.get(f"/api/v1/ordens-servico/{ordem['id']}", headers=auth).json()
    assert atual["status"] == "AGUARDANDO_APROVACAO"
    assert client.get(f"/api/v1/pecas/{peca['id']}", headers=auth).json()["quantidade_estoque"] == 0


def test_placa_de_outro_cliente_e_cliente_novo_sem_nome(client, auth):
    cliente = client.post(
        "/api/v1/clientes",
        headers=auth,
        json={"nome": "Empresa Alfa", "documento": CNPJ},
    )
    assert cliente.status_code == 201
    veiculo = client.post(
        "/api/v1/veiculos",
        headers=auth,
        json={"cliente_id": cliente.json()["id"], "placa": "JKL2M34", "marca": "Toyota", "modelo": "Corolla", "ano": 2021},
    )
    assert veiculo.status_code == 201
    conflito = client.post(
        "/api/v1/ordens-servico",
        headers=auth,
        json={
            "documento": CPF,
            "nome": "Maria",
            "placa": "JKL2M34",
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2021,
        },
    )
    assert conflito.status_code == 409
    sem_nome = client.post(
        "/api/v1/ordens-servico",
        headers=auth,
        json={"documento": CPF_2, "placa": "AAA1B23", "marca": "Fiat", "modelo": "Mobi", "ano": 2023},
    )
    assert sem_nome.status_code == 422
    assert client.get("/api/v1/metricas/tempo-medio-execucao", headers=auth).json()["quantidade_os"] == 0
    assert client.get("/api/v1/servicos", headers=auth).json()["total"] == 0
    assert client.get("/api/v1/pecas", headers=auth).json()["total"] == 0
    assert client.get("/api/v1/clientes", headers=auth).json()["total"] == 1


def test_duplicar_servico_e_ano_invalido(client, auth):
    servico = _servico(client, auth, "Alinhamento", "120.00")
    ordem = _abrir(client, auth, placa="RTY3B45")
    client.post(f"/api/v1/ordens-servico/{ordem['id']}/diagnostico", headers=auth, json={})
    ok = client.post(
        f"/api/v1/ordens-servico/{ordem['id']}/servicos",
        headers=auth,
        json={"servico_id": servico["id"]},
    )
    assert ok.status_code == 200
    duplicado = client.post(
        f"/api/v1/ordens-servico/{ordem['id']}/servicos",
        headers=auth,
        json={"servico_id": servico["id"]},
    )
    assert duplicado.status_code == 409
    ano = client.post(
        "/api/v1/veiculos",
        headers=auth,
        json={"cliente_id": ordem["cliente"]["id"], "placa": "ZZZ9Z99", "marca": "Fiat", "modelo": "Uno", "ano": 2099},
    )
    assert ano.status_code == 422
    preco = client.post(
        "/api/v1/servicos",
        headers=auth,
        json={"nome": "Preço quebrado demais", "preco": "10.555"},
    )
    assert preco.status_code == 422
