"""Ponto de entrada do monólito."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from oficina import __version__
from oficina.api.errors import registrar_erros
from oficina.api.routers import auth, clientes, metricas, ordens_servico, pecas, publico, servicos, veiculos

DESCRICAO = """
API do **Sistema Integrado de Atendimento e Execução de Serviços** de uma oficina mecânica.

Monólito em camadas com Domain-Driven Design:

- **Cadastro** — clientes (CPF/CNPJ) e veículos (placa antiga ou Mercosul)
- **Catálogo** — serviços
- **Estoque** — peças e insumos
- **Atendimento** — ordem de serviço, orçamento, status e execução

As rotas administrativas exigem JWT (`POST /api/v1/auth/login`, depois **Authorize**).
O cliente acompanha e decide o orçamento nas rotas públicas, com o id da OS e o documento.

Status da OS: Recebida → Em diagnóstico → Aguardando aprovação → Em execução → Finalizada → Entregue.
A rejeição do orçamento encerra o fluxo em Rejeitada.
"""

TAGS = [
    {"name": "Autenticação", "description": "Login JWT das APIs administrativas."},
    {"name": "Clientes", "description": "CRUD de clientes."},
    {"name": "Veículos", "description": "CRUD de veículos."},
    {"name": "Serviços", "description": "Catálogo de serviços."},
    {"name": "Peças e insumos", "description": "Catálogo e controle de estoque."},
    {"name": "Ordens de serviço", "description": "Abertura, diagnóstico, itens, orçamento e execução."},
    {"name": "Acompanhamento (cliente)", "description": "Consulta pública e aprovação ou rejeição do orçamento."},
    {"name": "Métricas", "description": "Tempo médio de execução."},
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.getenv("OFICINA_SKIP_STARTUP") != "1":
        from oficina.infrastructure.db.session import init_db

        init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Oficina Mecânica API",
        summary="MVP — atendimento, orçamento e execução de serviços",
        description=DESCRICAO,
        version=__version__,
        openapi_tags=TAGS,
        lifespan=lifespan,
    )
    registrar_erros(app)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(clientes.router, prefix="/api/v1")
    app.include_router(veiculos.router, prefix="/api/v1")
    app.include_router(servicos.router, prefix="/api/v1")
    app.include_router(pecas.router, prefix="/api/v1")
    app.include_router(ordens_servico.router, prefix="/api/v1")
    app.include_router(publico.router, prefix="/api/v1")
    app.include_router(metricas.router, prefix="/api/v1")

    @app.get("/health", tags=["Saúde"], summary="Verifica se a API está no ar")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def raiz():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
