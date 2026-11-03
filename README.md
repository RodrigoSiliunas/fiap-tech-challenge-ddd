<img src="docs/assets/banner.svg" alt="Oficina Mecânica: sistema integrado de atendimento e execução de serviços. Tech Challenge SOAT, Fase 1, com Python 3.12, FastAPI, DDD, PostgreSQL 16, Docker e JWT." width="100%">

# Oficina Mecânica — Tech Challenge Fase 1

[![CI](https://github.com/RodrigoSiliunas/fiap-tech-challenge-ddd/actions/workflows/ci.yml/badge.svg)](https://github.com/RodrigoSiliunas/fiap-tech-challenge-ddd/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688?logo=fastapi&logoColor=white)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![cobertura](https://img.shields.io/badge/cobertura-98%25-brightgreen)

Back-end da Fase 1 do Tech Challenge SOAT (FIAP): monólito de uma oficina mecânica, com DDD.

Documentação DDD no Miro: [https://miro.com/app/board/uXjVESOKEKE=/](https://miro.com/app/board/uXjVESOKEKE=/)

## Sumário

- [Objetivo](#objetivo)
- [Descrição](#descrição)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Justificativa do banco](#justificativa-do-banco)
- [Pré-requisitos](#pré-requisitos)
- [Execução](#execução)
- [Credenciais de demonstração](#credenciais-de-demonstração)
- [Swagger](#swagger)
- [Testes](#testes)
- [Estrutura de diretórios](#estrutura-de-diretórios)
- [Documentação DDD](#documentação-ddd)
  - [Domain Storytelling](#domain-storytelling)
- [Vídeo](#vídeo)
- [Análise de vulnerabilidades](#análise-de-vulnerabilidades)
- [Proteção da branch main](#proteção-da-branch-main)

## Objetivo

Registrar o atendimento da oficina em um fluxo só: identificar o cliente, cadastrar o veículo, montar a ordem de serviço, calcular o orçamento, guardar a aprovação ou a rejeição e acompanhar o status até a entrega.

## Descrição

A abertura da OS identifica o cliente pelo CPF ou CNPJ e registra o veículo com placa, marca, modelo e ano. Se o documento já existe, o cadastro é reaproveitado. A placa existente do mesmo cliente também é reaproveitada. Placa e documento não mudam depois do cadastro.

A OS entra em **Recebida**. O diagnóstico libera a inclusão de serviços e de peças/insumos (os dois usam o agregado `Peca`), porque é nele que a oficina define do que o veículo precisa. O orçamento é gerado pelo sistema: o valor é a soma dos preços gravados nas linhas, nunca digitado. Para gerá-lo é preciso ao menos um serviço. A OS passa a **Aguardando aprovação**, e o orçamento fica disponível na consulta do cliente.

Na abertura, o atendente entrega ao cliente o id da OS. Com ele e o documento, o cliente consulta e decide sem JWT. Documento errado ou OS inexistente devolvem o mesmo 404. A aprovação vai para **Em execução** e baixa o estoque na mesma transação. A rejeição encerra em **Rejeitada**, um status além dos seis do enunciado, criado para registrar a recusa: o estoque não é baixado e o veículo pode abrir outra OS. Depois da aprovação, a equipe finaliza e entrega.

O agregado recusa transição fora da máquina abaixo. Não há rota para alterar o status direto.

<img src="docs/assets/status-os.svg" alt="Máquina de estados: Recebida, Em diagnóstico, Aguardando aprovação, Em execução, Finalizada e Entregue. De Aguardando aprovação também segue para Rejeitada." width="100%">

<img src="docs/assets/fluxo-os.svg" alt="Fluxo da OS: abrir com cliente e veículo, diagnóstico, itens, orçamento, consulta pública, aprovar com baixa de estoque ou rejeitar, finalizar e entregar, com a rota de cada comando." width="760">

Itens só podem ser alterados em Em diagnóstico e em Aguardando aprovação. Nesse segundo status, incluir ou remover item recalcula o orçamento. A inclusão de peça confere o saldo disponível e não reserva; a baixa ocorre na aprovação. Um veículo não abre outra OS enquanto a atual não estiver Entregue ou Rejeitada.

CPF, CNPJ e placa são validados no domínio. A placa aceita o padrão antigo (`ABC1234`) e o Mercosul (`ABC1D23`).

O tempo médio de execução é a média de `finalizada_em - execucao_iniciada_em` nas OS Finalizada ou Entregue. A média é por OS, sem separar por tipo de serviço.

## Arquitetura

Quatro camadas no mesmo deploy. O domínio não depende de FastAPI nem de SQLAlchemy.

<img src="docs/assets/arquitetura-camadas.svg" alt="Camadas do monólito: Interface, Aplicação, Domínio e Infraestrutura, com PostgreSQL. A aplicação depende do domínio e da infraestrutura. A infraestrutura implementa as portas do domínio." width="960">

| Camada | Pasta | Função |
|--------|-------|--------|
| Interface | `backend/app/api` | FastAPI, DTOs, JWT, Swagger |
| Aplicação | `backend/app/application` | Comandos, consultas, uma transação por comando |
| Domínio | `backend/app/domain` | Agregados, entidades, value objects, eventos, políticas |
| Infraestrutura | `backend/app/infrastructure` | SQLAlchemy, repositórios, JWT, seed |

O entrypoint é `backend/app/main.py`. Os detalhes de cada pasta estão em [`backend/README.md`](backend/README.md).

Os contextos abaixo são módulos, não serviços separados. O orçamento é entidade da `OrdemDeServico`. Cliente, veículo, serviço e peça são agregados próprios, citados por id.

<img src="docs/assets/contextos.svg" alt="Contextos: Atendimento/OS no núcleo; Cadastro, Catálogo e Estoque como suporte, referenciados por id; Identidade com JWT como subdomínio genérico." width="960">

Os nomes de domínio no código estão em português, como no glossário (`OrdemDeServico`, `OrcamentoAprovado`, `Placa`). Pastas técnicas ficam em inglês.

O mapeamento comando a comando está em [`docs/ddd/mapeamento-codigo.md`](docs/ddd/mapeamento-codigo.md).

## Tecnologias

- Python 3.12
- FastAPI 0.162 e Uvicorn
- Pydantic v2
- SQLAlchemy 2
- PostgreSQL 16
- PyJWT e bcrypt
- pytest e pytest-cov
- Docker Compose
- GitHub Actions

O desenho das camadas segue [`docs/ddd/diagramas.md`](docs/ddd/diagramas.md).

## Justificativa do banco

PostgreSQL é o banco da aplicação. A aprovação do orçamento e a baixa de estoque precisam confirmar juntas: se a baixa falha, o status não muda. O modelo é relacional, com unicidade de CPF/CNPJ e de placa e com saldo que não pode ficar negativo. Transação, constraints e o serviço no Docker Compose cobrem isso. Os comandos que alteram uma OS travam a linha dela até o commit (`SELECT ... FOR UPDATE`), então aprovação, rejeição e inclusão de itens simultâneas não se sobrescrevem.

Os testes usam SQLite em memória, com o mesmo mapeamento SQLAlchemy, para rodar sem subir o Postgres. `OFICINA_TEST_DATABASE_URL` repete a suíte contra PostgreSQL.

## Pré-requisitos

- Docker e Docker Compose, para subir a API e o banco
- Python 3.12 ou mais novo, só para testes ou para rodar a API fora do container

## Execução

Na raiz do repositório:

```bash
docker compose up --build
```

A API fica em `http://localhost:8000`. Na subida o schema é criado e a semente entra se o catálogo ainda estiver vazio.

```bash
docker compose down
```

O volume `pgdata` mantém os dados. `docker compose down -v` apaga o volume.

Para percorrer o fluxo completo com a API no ar (cada execução usa uma placa nova; a cliente do exemplo é reaproveitada pelo CPF):

```bash
python backend/scripts/demo_fluxo.py
```

A semente inclui Troca de óleo, Alinhamento, Balanceamento, Óleo 5W30, Filtro de óleo e Pastilha de freio.

Para rodar a API fora do container, com o banco do compose, veja [`backend/README.md`](backend/README.md#executar-fora-do-docker).

## Credenciais de demonstração

Valores só do ambiente local, definidos no `docker-compose.yml` e no `backend/.env.example`.

| Uso | Valor |
|-----|--------|
| Usuário admin | `admin` |
| Senha | `admin123` |
| Banco | usuário `oficina`, senha `oficina`, database `oficina` |
| JWT | segredo aleatório gerado a cada subida da API; defina `JWT_SECRET` para fixá-lo |

O login é `POST /api/v1/auth/login`. O token vale para as rotas administrativas. A consulta e a decisão do cliente não usam esse token.

## Swagger

Com a API no ar:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI: `http://localhost:8000/openapi.json`

Em **Authorize**, cole o `access_token` sem o prefixo `Bearer`.

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

## Testes

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

O atalho é `make test`, dentro de `backend/`.

São 44 testes. Com Python 3.12.16 e SQLite passam 42; os 2 de concorrência só rodam contra PostgreSQL. A cobertura de `app` é **97,97%** (2318 de 2366 linhas) e a de `app/domain`, **98,52%** (733 de 744). Abaixo de 80% o pytest falha.

Relatório: [`backend/docs/coverage/coverage-summary.txt`](backend/docs/coverage/coverage-summary.txt).

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda a suíte em `backend/` a cada push e pull request. Primeiro roda em SQLite, com o mesmo limite de 80%, e publica o `coverage.xml`. Depois roda contra PostgreSQL 16, onde entram também os testes de concorrência.

Para repetir contra PostgreSQL, crie o database `oficina_test` e exporte a URL antes do pytest, ainda em `backend/`:

```bash
export OFICINA_TEST_DATABASE_URL=postgresql+psycopg://oficina:oficina@localhost:5432/oficina_test
pytest
```

A suíte recria o schema nesse banco.

## Estrutura de diretórios

```text
backend/
  app/
    main.py               # entrypoint: FastAPI, lifespan, rotas
    config.py             # variáveis de ambiente
    api/                  # routers, schemas, erros
    application/
      commands/           # abrir OS, aprovar, CRUD, estoque
      queries/            # listagem, acompanhamento, tempo médio
    domain/
      cliente/ veiculo/ servico/ peca/ ordem_servico/
      services/           # políticas de estoque
      shared/             # Dinheiro, Quantidade, eventos
    infrastructure/
      db/                 # modelos ORM e repositórios
      auth/               # JWT e bcrypt
      seed.py
  tests/
    unit/
    integration/
  scripts/                # demo_fluxo.py
  docs/
    coverage/             # saída da cobertura
    security/             # análise de vulnerabilidades (pip-audit, Bandit e Trivy)
  Dockerfile
  pyproject.toml
  requirements.txt
  README.md               # detalhes do backend
docs/
  assets/                 # diagramas SVG deste README
  ddd/                    # Event Storming, diagramas, glossário, domain storytelling, mapeamento
docker-compose.yml        # API e PostgreSQL
.github/workflows/ci.yml  # testes e cobertura
```

Os testes ficam em `backend/tests`, fora da imagem Docker.

## Documentação DDD

Board no Miro: [https://miro.com/app/board/uXjVESOKEKE=/](https://miro.com/app/board/uXjVESOKEKE=/)

Arquivos no repositório, em [`docs/ddd/`](docs/ddd/):

- [`event-storming.md`](docs/ddd/event-storming.md) e [`event-storming.pdf`](docs/ddd/event-storming.pdf)
- [`event-storming.png`](docs/ddd/event-storming.png)
- [`diagramas.md`](docs/ddd/diagramas.md) e [`diagramas.pdf`](docs/ddd/diagramas.pdf)
- [`linguagem-ubiqua.md`](docs/ddd/linguagem-ubiqua.md)
- [`mapeamento-codigo.md`](docs/ddd/mapeamento-codigo.md) — contextos, agregados, eventos e comandos ligados ao código
- [`domain-storytelling/`](docs/ddd/domain-storytelling/) — histórias em `.egn`, SVG e PNG

### Domain Storytelling

Cinco histórias no formato do Egon, com as sentenças em [`docs/ddd/domain-storytelling/domain-storytelling.md`](docs/ddd/domain-storytelling/domain-storytelling.md). Os arquivos `.egn` importam em [https://egon.io/app/](https://egon.io/app/).

**1. Abertura da ordem de serviço**

<img src="docs/ddd/domain-storytelling/01-abertura-os.svg" alt="História 1: o atendente identifica o documento, registra o veículo e abre a ordem de serviço em Recebida." width="980">

**2. Diagnóstico e orçamento**

<img src="docs/ddd/domain-storytelling/02-diagnostico-orcamento.svg" alt="História 2: o mecânico inicia o diagnóstico, inclui serviços e peças, e o sistema gera o orçamento." width="1120">

**3. Aprovação ou rejeição**

<img src="docs/ddd/domain-storytelling/03-aprovacao-rejeicao.svg" alt="História 3: o cliente aprova o orçamento, com baixa de estoque e status Em execução, ou rejeita e a OS vai para Rejeitada." width="1080">

**4. Execução e entrega**

<img src="docs/ddd/domain-storytelling/04-execucao-entrega.svg" alt="História 4: execução, finalização, entrega do veículo e consulta do status pelo cliente." width="1160">

**5. Gestão de estoque e catálogo**

<img src="docs/ddd/domain-storytelling/05-gestao-estoque.svg" alt="História 5: o administrador cadastra peça e serviço e registra entrada ou ajuste de estoque." width="920">

## Vídeo

`COLOQUE_AQUI_O_LINK_DO_YOUTUBE`

## Análise de vulnerabilidades

Relatório em [`backend/docs/security/vulnerability-report.md`](backend/docs/security/vulnerability-report.md).

São três análises:

- Dependências, com `pip-audit` 2.10.1: nenhuma vulnerabilidade conhecida.
- Código, com Bandit 1.9.4: 3 achados de severidade baixa, avaliados e aceitos.
- Imagem Docker, com Trivy 0.76.1: nenhuma vulnerabilidade crítica e nenhuma com correção publicada. O pip saiu da imagem, e com ele as CVEs que trazia; as 9 altas restantes estão em pacotes do Debian sem correção publicada.

## Proteção da branch main

A `main` só recebe mudança por pull request. A proteção é o ruleset **Proteção da main**, ativo e visível no GitHub em **Settings → Rules → Rulesets**:

- pull request obrigatório para chegar à `main`;
- o check `tests` do workflow CI precisa passar antes do merge;
- push forçado e exclusão da branch são bloqueados;
- ninguém tem bypass, nem os administradores.

O check exigido é o nome do job do CI (`tests`). Se o job for renomeado, o ruleset precisa ser atualizado junto.
