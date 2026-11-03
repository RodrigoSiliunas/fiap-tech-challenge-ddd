# Backend — Oficina Mecânica

Monólito FastAPI do Tech Challenge SOAT, Fase 1. Objetivo, arquitetura, banco, Swagger, credenciais e documentação DDD estão no [README da raiz](../README.md). Este arquivo cobre o que é só do backend.

Os comandos abaixo rodam nesta pasta, `backend/`.

## Estrutura de `app/`

`app/main.py` é o entrypoint: `create_app()` monta o FastAPI, registra os erros e as rotas, e o lifespan cria o schema e a semente. `app/config.py` lê as variáveis de ambiente.

| Camada | Pasta | Conteúdo |
|--------|-------|----------|
| Interface | `app/api/` | Routers FastAPI, schemas Pydantic, presenters, dependências (JWT e unidade de trabalho) e tradução de erros para HTTP |
| Aplicação | `app/application/` | Commands e queries; cada comando abre uma transação e faz um `commit` |
| Domínio | `app/domain/` | Agregados, entidades, objetos de valor, eventos, portas dos repositórios e políticas de estoque |
| Infraestrutura | `app/infrastructure/` | SQLAlchemy (modelos, repositórios e sessão), unidade de trabalho, JWT, bcrypt e semente |

O domínio não importa FastAPI, Pydantic nem SQLAlchemy. A relação entre essas pastas e o Event Storming está em [`docs/ddd/mapeamento-codigo.md`](../docs/ddd/mapeamento-codigo.md).

```text
backend/
  app/                # pacote da API (tabela acima)
  tests/
    unit/             # domínio e JWT
    integration/      # API ponta a ponta e semente
  scripts/
    demo_fluxo.py     # percorre o fluxo da OS contra a API no ar
  docs/
    coverage/         # evidência de cobertura
    security/         # relatório do pip-audit
  Dockerfile          # imagem python:3.12-slim, usuário sem root
  pyproject.toml      # metadados, pytest e coverage
  requirements.txt    # dependências de execução, versões fixas
  requirements-dev.txt
  Makefile
  .env.example
```

## Executar fora do Docker

A API precisa de um PostgreSQL. O da raiz serve:

```bash
docker compose up -d db
```

Depois, nesta pasta:

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Os padrões de `app/config.py` já apontam para esse banco em `localhost:5432`. Para mudar algum valor, copie `.env.example` para `.env`. Com `--reload`, cada recarga gera um segredo JWT novo e invalida o token anterior; defina `JWT_SECRET` no `.env` para manter o token entre recargas. O `uvloop` não é instalado no Windows; o Uvicorn usa o loop padrão do asyncio.

## Variáveis de ambiente

| Variável | Padrão | Uso |
|----------|--------|-----|
| `DATABASE_URL` | `postgresql+psycopg://oficina:oficina@localhost:5432/oficina` | Banco da API |
| `JWT_SECRET` | aleatório, gerado a cada subida | Assinatura dos tokens |
| `JWT_ALGORITHM` | `HS256` | Algoritmo do JWT |
| `JWT_EXPIRE_MINUTES` | `120` | Validade do token |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_NOME` | `admin`, `admin123`, `Administrador da Oficina` | Usuário criado pela semente |
| `OFICINA_SKIP_STARTUP` | não definida | Com `1`, o startup não cria o schema nem a semente (usado nos testes) |
| `OFICINA_TEST_DATABASE_URL` | não definida | Roda a suíte contra PostgreSQL em vez de SQLite em memória |

Os padrões são só de desenvolvimento. O `docker-compose.yml` da raiz define os mesmos valores para a API no container, menos o `JWT_SECRET`, que fica fora do repositório.

## Testes e cobertura

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

O atalho é `make test`; `make cov` também grava `coverage.xml`. Abaixo de 80% o pytest falha.

Na última execução, com Python 3.12.16, foram 35 testes. A cobertura de `app` é de 96,13% (2258 de 2349 linhas) e a de `app/domain`, de 94,73% (701 de 740). A saída completa está em [`docs/coverage/coverage-summary.txt`](docs/coverage/coverage-summary.txt).

Os testes usam SQLite em memória, com o mesmo mapeamento SQLAlchemy. Para repetir contra PostgreSQL, crie o database `oficina_test` e exporte a URL:

```bash
export OFICINA_TEST_DATABASE_URL=postgresql+psycopg://oficina:oficina@localhost:5432/oficina_test
pytest
```

## Regenerar as evidências

A cobertura e a análise de vulnerabilidades do repositório saem do Python 3.12, o mesmo da imagem e do CI. Com Docker, nesta pasta:

```bash
docker run --rm -v "$PWD:/src:ro" python:3.12-slim sh -c "cp -r /src /work && cd /work && pip install -q -r requirements-dev.txt pip-audit && pytest --cov=app --cov-report=term-missing && coverage report --show-missing --include='app/domain/*' && pip-audit -r requirements.txt -r requirements-dev.txt"
```

No PowerShell, troque `$PWD` por `${PWD}`. A saída do pytest e do `coverage report` vai para [`docs/coverage/coverage-summary.txt`](docs/coverage/coverage-summary.txt), e a do `pip-audit` para [`docs/security/vulnerability-report.md`](docs/security/vulnerability-report.md). O `pip-audit` não entra nas dependências do projeto.

## Imagem Docker

O `Dockerfile` usa `python:3.12-slim`, instala só o `requirements.txt`, copia `app/` e roda `uvicorn app.main:app` com um usuário sem privilégio. Os testes, os scripts e a documentação ficam fora da imagem. O `docker-compose.yml` da raiz constrói esta pasta com `build: ./backend`.
