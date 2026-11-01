# Oficina Mecânica — SOAT Tech Challenge Fase 1

![cobertura](https://img.shields.io/badge/cobertura-96%25-brightgreen)

MVP do back-end do **Sistema Integrado de Atendimento e Execução de Serviços** de uma oficina mecânica. Monólito em camadas, com Domain-Driven Design, PostgreSQL e autenticação JWT nas APIs administrativas.

- Documentação DDD (Miro ou equivalente): `COLOQUE_AQUI_O_LINK_DO_MIRO`
- Vídeo da entrega (YouTube, público, até 15 minutos): `COLOQUE_AQUI_O_LINK_DO_YOUTUBE`

Os artefatos de DDD exportados estão em [`docs/ddd/`](docs/ddd/). O vínculo com o código está em [`docs/ddd/mapeamento-codigo.md`](docs/ddd/mapeamento-codigo.md).

## Objetivo

Substituir anotações e planilhas por um fluxo único de atendimento: identificar o cliente, registrar o veículo, montar a ordem de serviço com serviços, peças e insumos, gerar o orçamento, registrar a aprovação ou a rejeição e acompanhar o status até a entrega. O cliente consulta o andamento por API. A equipe interna opera as rotas administrativas.

## Descrição da solução

A ordem de serviço nasce em **Recebida**. O diagnóstico libera a inclusão de serviços e peças. O orçamento é calculado pelo sistema (soma dos preços fotografados na inclusão) e a OS passa a **Aguardando aprovação**. O cliente aprova ou rejeita informando o CPF/CNPJ. A aprovação muda o status para **Em execução** e baixa o estoque na mesma transação. Em seguida a equipe finaliza e entrega o veículo.

Status controlados pelo agregado, sem endpoint para alterar o status à mão:

`Recebida → Em diagnóstico → Aguardando aprovação → Em execução → Finalizada → Entregue`

A rejeição encerra em `Rejeitada`. Transições fora dessa máquina são recusadas.

## Arquitetura

Monólito em quatro camadas, no mesmo deploy:

| Camada | Pasta | O que faz |
|--------|-------|-----------|
| Interface | `oficina/api` | FastAPI, DTOs, Swagger, JWT |
| Aplicação | `oficina/application` | Comandos, consultas, transação |
| Domínio | `oficina/domain` | Agregados, objetos de valor, eventos, políticas |
| Infraestrutura | `oficina/infrastructure` | SQLAlchemy, PostgreSQL, repositórios, semente |

Bounded contexts lógicos, não microsserviços:

- **Atendimento / OS** (núcleo): `OrdemDeServico`, itens, orçamento e status
- **Cadastro**: `Cliente` e `Veiculo`
- **Catálogo**: `Servico`
- **Estoque**: `Peca`
- **Identidade**: JWT, subdomínio genérico

O orçamento vive dentro da ordem de serviço. Cliente e veículo são agregados separados, referenciados por id. A linguagem de domínio no código está em português (`OrdemDeServico`, `OrcamentoAprovado`, `Placa`), alinhada ao glossário.

## Tecnologias

- Python 3.12
- FastAPI e Uvicorn
- Pydantic v2
- SQLAlchemy 2
- PostgreSQL 16
- PyJWT e bcrypt
- pytest e pytest-cov
- Docker Compose
- GitHub Actions

A escolha acompanha o desenho em [`docs/ddd/diagramas.md`](docs/ddd/diagramas.md): um monólito em camadas com portas de repositório e handlers de comando.

## Banco de dados

**PostgreSQL.**

A aprovação do orçamento e a baixa de estoque precisam ser atômicas. O modelo é relacional (agregados ligados por id, unicidade de CPF/CNPJ e de placa, saldo que não pode ficar negativo). PostgreSQL entrega transação ACID, constraints e um fluxo simples no Docker Compose. Os testes automatizados usam SQLite em memória para rodar sem subir o banco; o schema é o mesmo SQLAlchemy. Há também a variável `OFICINA_TEST_DATABASE_URL` para repetir a suíte contra PostgreSQL.

MongoDB foi descartado porque o fluxo crítico cruza dois agregados na mesma transação. SQLite serve ao teste, mas não demonstra concorrência nem é o banco do ambiente executável.

## Pré-requisitos

- Docker e Docker Compose
- Python 3.12, só se for rodar os testes ou a API fora do container

## Execução

Na raiz do repositório:

```bash
docker compose up --build
```

A API sobe em `http://localhost:8000`. O schema é criado na subida e a semente de demonstração é inserida se ainda não existir.

Para encerrar:

```bash
docker compose down
```

O volume `pgdata` guarda o banco entre as subidas. `docker compose down -v` apaga esse volume.

### Credenciais de demonstração

Somente para o ambiente local. Não são segredo de produção.

| Uso | Valor |
|-----|--------|
| Usuário admin | `admin` |
| Senha | `admin123` |
| Banco | usuário `oficina`, senha `oficina`, database `oficina` |
| JWT | segredo de desenvolvimento definido no `docker-compose.yml` |

O login é `POST /api/v1/auth/login`. O token Bearer vale para as rotas administrativas. O cliente não usa JWT: consulta e decide o orçamento com o id da OS e o CPF ou CNPJ.

Catálogo semeado na primeira subida: Troca de óleo, Alinhamento, Balanceamento, Óleo 5W30, Filtro de óleo e Pastilha de freio.

Para repetir o fluxo feliz com um cliente e uma placa novos:

```bash
python scripts/demo_fluxo.py
```

## Swagger

Com a API no ar:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

No Swagger, use **Authorize** com o `access_token` do login (sem o prefixo `Bearer`; a interface acrescenta).

Rotas principais:

| Ação | Método e caminho |
|------|------------------|
| Login | `POST /api/v1/auth/login` |
| Clientes, veículos, serviços, peças | `/api/v1/clientes`, `/veiculos`, `/servicos`, `/pecas` |
| Entrada e ajuste de estoque | `POST /api/v1/pecas/{id}/entrada-estoque` e `/ajuste-estoque` |
| Abrir OS | `POST /api/v1/ordens-servico` |
| Diagnóstico, itens, orçamento | `POST /api/v1/ordens-servico/{id}/diagnostico`, `/servicos`, `/pecas`, `/orcamento` |
| Finalizar e entregar | `POST /api/v1/ordens-servico/{id}/finalizar` e `/entregar` |
| Consulta do cliente | `GET /api/v1/publico/ordens-servico/{id}?documento=` |
| Aprovar ou rejeitar | `POST /api/v1/publico/ordens-servico/{id}/aprovar` e `/rejeitar` |
| Tempo médio de execução | `GET /api/v1/metricas/tempo-medio-execucao` |

O tempo médio é a média, em segundos e horas, entre o início da execução (aprovação) e a finalização, nas OS `Finalizada` ou `Entregue`.

CPF, CNPJ e placa (padrão antigo `ABC1234` e Mercosul `ABC1D23`) são validados no domínio.

## Testes e cobertura

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=oficina --cov-report=term-missing --cov-fail-under=80
```

Ou `make test`.

Evidência desta entrega: **96,17%** de cobertura de linhas no pacote `oficina` (2257 de 2347). O domínio, em `oficina/domain`, fica em **95%** (740 statements). Os agregados de OS, cliente, veículo, serviço, peça e as políticas de estoque estão cobertos por testes de unidade; os fluxos de API, inclusive o rollback quando o estoque não fecha na aprovação, estão nos testes de integração.

Relatório: [`docs/coverage/coverage-summary.txt`](docs/coverage/coverage-summary.txt).

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda a mesma suíte em todo push e pull request e falha se a cobertura ficar abaixo de 80%.

Para repetir a suíte contra PostgreSQL:

```bash
export OFICINA_TEST_DATABASE_URL=postgresql+psycopg://oficina:oficina@localhost:5432/oficina_test
pytest
```

Crie o database `oficina_test` antes. A suíte recria o schema nesse banco.

## Estrutura de diretórios

```text
oficina/
  main.py                 # FastAPI, lifespan, rotas
  api/                    # routers, schemas, apresentadores
  application/
    commands/             # abrir OS, aprovar, CRUD, estoque
    queries/              # listagem, acompanhamento, tempo médio
  domain/
    cliente/ veiculo/ servico/ peca/ ordem_servico/
    services/             # políticas de estoque
    shared/               # Dinheiro, Quantidade, eventos
  infrastructure/
    db/                   # modelos ORM e repositórios
    auth/                 # JWT e bcrypt
    seed.py
tests/
  unit/                   # domínio e JWT
  integration/            # API e semente
docs/
  ddd/                    # Event Storming, diagramas, glossário, mapeamento
  security/               # relatório do pip-audit
  coverage/               # saída da cobertura
```

Os testes ficam na raiz, fora da imagem Docker, no lugar que o pytest espera. O diagrama de pacotes os mostra junto do código; a separação evita publicá-los na imagem.

## Análise de vulnerabilidades

Relatório em [`docs/security/vulnerability-report.md`](docs/security/vulnerability-report.md).

`pip-audit` 2.10.1 sobre `requirements.txt` e `requirements-dev.txt`: **nenhuma vulnerabilidade conhecida**. Não houve achado alto ou crítico para corrigir.

## Proteção da branch main

A `main` deve aceitar mudança só por pull request.

No GitHub: **Settings → Branches → Add branch protection rule** para `main`.

- Require a pull request before merging
- Require status checks to pass before merging, marcando o check `tests` do workflow CI
- Do not allow bypassing the above settings

Nada deve ser enviado direto à `main`.

## Roteiro sugerido do vídeo (até 15 minutos)

1. Proposta: dores da oficina e o que o MVP cobre.
2. Arquitetura em camadas e os bounded contexts no monólito. Justificar PostgreSQL.
3. Event Storming (`docs/ddd/event-storming.png`) e a máquina de estados.
4. Agregados, objetos de valor e eventos, com o glossário ao lado do código.
5. Subir `docker compose up` e abrir o Swagger.
6. Login JWT e uma chamada administrativa sem token (401).
7. Abrir uma OS por CPF ou CNPJ, registrar o veículo, incluir serviço e peça.
8. Gerar o orçamento, consultar pela rota pública e aprovar. Mostrar a baixa de estoque.
9. Finalizar, entregar e o tempo médio de execução.
10. Rejeição em outra OS, ou uma transição inválida.
11. Testes (`pytest`) e o relatório de cobertura.
12. Relatório de vulnerabilidades e os nomes de quem apresenta.
