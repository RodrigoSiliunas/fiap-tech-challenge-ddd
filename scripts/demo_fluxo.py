"""Percorre o fluxo feliz contra uma API já no ar. Uso: python scripts/demo_fluxo.py"""

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def chamar(method: str, path: str, body: dict | None = None, token: str | None = None, ok: tuple[int, ...] = (200, 201)):
    dados = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(BASE + path, data=dados, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            bruto = response.read().decode()
            payload = json.loads(bruto) if bruto else None
            if response.status not in ok:
                raise SystemExit(f"{method} {path} -> {response.status} {payload}")
            return payload
    except urllib.error.HTTPError as exc:
        detalhe = exc.read().decode()
        raise SystemExit(f"{method} {path} -> {exc.code} {detalhe}") from exc


def main() -> None:
    token = chamar("POST", "/api/v1/auth/login", {"username": "admin", "password": "admin123"})["access_token"]
    servico = chamar(
        "POST",
        "/api/v1/servicos",
        {"nome": "Troca de óleo demo", "preco": "150.00", "descricao": "Óleo e filtro"},
        token,
    )
    peca = chamar(
        "POST",
        "/api/v1/pecas",
        {"nome": "Filtro demo", "preco": "35.00", "quantidade_estoque": 10, "descricao": "Filtro"},
        token,
    )
    ordem = chamar(
        "POST",
        "/api/v1/ordens-servico",
        {
            "documento": "529.982.247-25",
            "nome": "Maria Silva",
            "email": "maria@example.com",
            "telefone": "11988887777",
            "placa": "ABC1D23",
            "marca": "Fiat",
            "modelo": "Argo",
            "ano": 2022,
            "observacao": "Barulho na suspensão",
        },
        token,
    )
    ordem_id = ordem["id"]
    chamar("POST", f"/api/v1/ordens-servico/{ordem_id}/diagnostico", {"observacao": "Em diagnóstico"}, token)
    chamar("POST", f"/api/v1/ordens-servico/{ordem_id}/servicos", {"servico_id": servico["id"]}, token)
    chamar("POST", f"/api/v1/ordens-servico/{ordem_id}/pecas", {"peca_id": peca["id"], "quantidade": 1}, token)
    orcamento = chamar("POST", f"/api/v1/ordens-servico/{ordem_id}/orcamento", token=token)
    print("Orçamento:", orcamento["orcamento"]["valor_total"], orcamento["status_descricao"])
    publico = chamar(
        "GET",
        f"/api/v1/publico/ordens-servico/{ordem_id}?documento=529.982.247-25",
    )
    print("Consulta pública:", publico["status_descricao"])
    aprovada = chamar(
        "POST",
        f"/api/v1/publico/ordens-servico/{ordem_id}/aprovar",
        {"documento": "529.982.247-25"},
    )
    print("Após aprovação:", aprovada["status_descricao"])
    finalizada = chamar("POST", f"/api/v1/ordens-servico/{ordem_id}/finalizar", token=token)
    entregue = chamar("POST", f"/api/v1/ordens-servico/{ordem_id}/entregar", token=token)
    print("Entrega:", entregue["status_descricao"], "OS", entregue["numero"])
    print("Estoque restante:", chamar("GET", f"/api/v1/pecas/{peca['id']}", token=token)["quantidade_estoque"])
    _ = finalizada


if __name__ == "__main__":
    main()
