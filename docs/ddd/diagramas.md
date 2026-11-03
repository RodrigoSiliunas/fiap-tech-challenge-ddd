# Diagramas DDD — Oficina Mecânica (MVP)

> Diagramas solicitados pela disciplina (Aulas 01, 04, 05 e 06) alinhados à solução implementada em `backend/app/`.
> Os mesmos diagramas estão no [board do Miro](https://miro.com/app/board/uXjVESOKEKE=/), e o export fica em `diagramas.pdf`.

---

## 1. Subdomínios (Design Estratégico — Aula 01)

```mermaid
flowchart TB
  Dom[Domínio: Oficina Mecânica<br/>Atendimento e Execução de Serviços]
  Dom --> Core[Subdomínio Principal CORE<br/>Gestão de Ordens de Serviço<br/>orçamento, status, execução]
  Dom --> Sup1[Subdomínio de Suporte<br/>Cadastro Cliente / Veículo]
  Dom --> Sup2[Subdomínio de Suporte<br/>Catálogo de Serviços]
  Dom --> Sup3[Subdomínio de Suporte<br/>Estoque de Peças e Insumos]
  Dom --> Gen[Subdomínio Genérico<br/>Identidade e Acesso JWT]
```

**Por quê Core = OS?** É o que diferencia a oficina neste desafio: priorização, fluxo de orçamento/autorização e acompanhamento em tempo real — exatamente as dores do brief.

**Alternativa descartada:** tratar Estoque como Core. Estoque é importante, mas é CRUD + invariante de quantidade; não é o diferencial competitivo do MVP.

---

## 2. Contextos Delimitados e Mapa de Contexto (Aulas 03–04)

No MVP monolítico, os BCs são **módulos lógicos** no mesmo deploy (não microsserviços).

```mermaid
flowchart LR
  subgraph U1[Upstream]
    CAD[BC Cadastro<br/>Cliente, Veículo]
    CAT[BC Catálogo<br/>Serviço]
    ID[BC Identidade<br/>JWT]
  end
  subgraph CORE[Core]
    OS[BC Atendimento / OS<br/>OrdemDeServico, Orçamento, Status]
  end
  subgraph U2[Upstream/Downstream]
    EST[BC Estoque<br/>Peça]
  end
  CAD -->|Cliente-Fornecedor<br/>U → D| OS
  CAT -->|Cliente-Fornecedor<br/>U → D| OS
  OS -->|Cliente-Fornecedor<br/>evento/política| EST
  ID -->|OHS interno<br/>protege admin| OS
  ID --> EST
  ID --> CAD
  APP[App Cliente futuro] -.->|Conformista / ACL futura| OS
```

| Relação | Padrão (Aula 04) | Justificativa |
|---------|------------------|---------------|
| Cadastro → OS | Cliente-Fornecedor (Cadastro U) | OS consome identidade de Cliente/Veículo por id; não altera regras de cadastro |
| Catálogo → OS | Cliente-Fornecedor | OS copia preço/descrição no ItemServico no momento da inclusão |
| OS → Estoque | Cliente-Fornecedor / política | Evento OrcamentoAprovado dispara baixa |
| Identidade → demais | Open-Host Service interno | JWT padronizado para APIs admin |
| Kernel compartilhado | **Evitado** | Aula 04 desencoraja; módulos separam modelos |

**Alternativa descartada:** um único BC “Oficina” sem fronteiras. Funciona em código pequeno, mas a documentação DDD da FIAP pede Bounded Contexts identificados — módulos deixam a defesa clara sem over-engineering.

---

## 3. Agregados, Entidades e Objetos de Valor (Aula 05)

### 3.1 Visão dos agregados

```mermaid
flowchart TB
  subgraph AgOS[Agregado OrdemDeServico]
    OS[RAÍZ: OrdemDeServico]
    IS[Entidade: ItemServico]
    IP[Entidade: ItemPeca]
    ORC[Entidade: Orcamento]
    OS --> IS
    OS --> IP
    OS --> ORC
    OS -. VO .- ST[StatusOS]
    ORC -. VO .- DIN[Dinheiro]
    IP -. VO .- QTD[Quantidade]
  end
  subgraph AgCli[Agregado Cliente]
    C[RAÍZ: Cliente]
    C -. VO .- DOC[Documento CPF/CNPJ]
  end
  subgraph AgVei[Agregado Veiculo]
    V[RAÍZ: Veiculo]
    V -. VO .- PL[Placa]
  end
  subgraph AgPeca[Agregado Peca]
    P[RAÍZ: Peca]
    P -. VO .- QE[Quantidade em estoque]
    P -. VO .- PRECO[Dinheiro]
  end
  subgraph AgServ[Agregado Servico]
    S[RAÍZ: Servico]
    S -. VO .- PRECO2[Dinheiro]
  end
  AgCli -.->|ref por id| AgOS
  AgVei -.->|ref por id| AgOS
  AgServ -.->|ref por id no ItemServico| AgOS
  AgPeca -.->|ref por id no ItemPeca| AgOS
```

### 3.2 Por que Orçamento está DENTRO de OrdemDeServico?

| Critério | Análise |
|----------|---------|
| Invariantes juntos? | Sim: total = soma dos itens; aprovação só se status = Aguardando aprovação; rejeição encerra a OS |
| Transação única? | Sim: gerar/aprovar orçamento muda status da OS na mesma consistência |
| Ciclo de vida | Orçamento não existe sem OS neste MVP |

**Alternativa descartada:** agregado `Orcamento` separado. Útil se houvesse versionamento complexo, múltiplos orçamentos concorrentes ou BC financeiro. Para MVP de ~2 dias, aumenta fronteiras sem ganho.

### 3.3 Por que Cliente e Veículo são agregados separados?

Brief exige CRUD independente. Veículo pode mudar de dono no futuro; placa é identidade própria. OS referencia ambos por id (não aninha entidades de outro agregado — regra de Vernon/Evans).

### 3.4 Invariantes por agregado

| Agregado | Invariantes |
|----------|-------------|
| **OrdemDeServico** | Transições de status só pelas setas permitidas; orçamento ≥ 0 e com ao menos um serviço; aprovação/rejeição só em Aguardando aprovação; entrega só após Finalizada; itens só alteráveis em Em diagnóstico e Aguardando aprovação |
| **Cliente** | Documento válido (CPF ou CNPJ); documento único no repositório |
| **Veiculo** | Placa válida e única; ano coerente |
| **Peca** | `quantidade_estoque` ≥ 0; baixa não pode resultar negativo |
| **Servico** | Preço ≥ 0; nome obrigatório |

### 3.5 Entidade vs Objeto de Valor

| Conceito | Tipo | Motivo |
|----------|------|--------|
| OrdemDeServico, Cliente, Veiculo, Peca, Servico, ItemServico, ItemPeca, Orcamento | Entidade | Identidade + ciclo de vida / mutabilidade |
| Documento, Placa, Dinheiro, Quantidade, StatusOS | Objeto de Valor | Sem id próprio; imutáveis; igualdade por valor (Aula 05) |

---

## 4. Máquina de estados da OS (transições permitidas)

```mermaid
stateDiagram-v2
  direction LR
  [*] --> Recebida
  Recebida --> EmDiagnostico: IniciarDiagnostico
  EmDiagnostico --> AguardandoAprovacao: GerarOrcamento
  AguardandoAprovacao --> EmExecucao: AprovarOrcamento
  AguardandoAprovacao --> Rejeitada: RejeitarOrcamento
  EmExecucao --> Finalizada: FinalizarServico
  Finalizada --> Entregue: EntregarVeiculo
  Rejeitada --> [*]
  Entregue --> [*]

  note right of AguardandoAprovacao
    Caminho de rejeição
    explícito no brief
  end note
```

Transições **proibidas** (exemplos para defesa): Recebida → Entregue; Em execução → Aguardando aprovação; Rejeitada → Em execução.

---

## 5. Arquitetura em camadas + pacotes Python/FastAPI (Aula 05)

```mermaid
flowchart TB
  UI[Interface · api/<br/>routers FastAPI, schemas, JWT, Swagger]
  APP[Aplicação · application/<br/>commands, queries, transação]
  DOM[Domínio · domain/<br/>agregados, VOs, eventos, políticas, portas]
  INF[Infraestrutura · infrastructure/<br/>SQLAlchemy, repositórios, unidade de trabalho, JWT, seed]
  DB[(PostgreSQL 16)]
  UI --> APP
  APP --> DOM
  APP --> INF
  INF -->|implementa as portas| DOM
  INF --> DB
```

### Estrutura de pacotes

Pacote `app`, em `backend/app/`. O entrypoint é `main.py`.

```text
backend/
  app/
    main.py                     # create_app(): rotas, erros, lifespan
    config.py                   # variáveis de ambiente
    api/                        # Interface (HTTP)
      deps.py                   # JWT e unidade de trabalho por requisição
      errors.py                 # DomainError → HTTP
      schemas.py                # DTOs Pydantic (não são domínio)
      presenters.py             # domínio → resposta
      routers/
        auth.py  clientes.py  veiculos.py  servicos.py  pecas.py
        ordens_servico.py  publico.py  metricas.py
    application/                # Camada de Aplicação
      support.py                # concluir(): grava eventos e faz commit
      commands/
        autenticar.py
        cadastros.py            # CRUD de cliente, veículo, serviço e peça; estoque
        ordens_servico.py       # AbrirOrdemDeServico ... EntregarVeiculo
      queries/
        ordens_servico.py       # listagem, detalhe, ConsultarAcompanhamento
        tempo_medio_execucao.py
    domain/                     # Coração do software
      exceptions.py
      shared/                   # Dinheiro, Quantidade, RaizAgregado, DomainEvent
      cliente/                  # aggregate.py, documento.py, events.py, repository.py
      veiculo/                  # aggregate.py, placa.py, events.py, repository.py
      servico/                  # aggregate.py, events.py, repository.py
      peca/                     # aggregate.py, events.py, repository.py
      ordem_servico/            # aggregate.py (OS, itens, orçamento), status.py, events.py, repository.py
      services/
        politica_estoque.py     # PoliticaDisponibilidadeEstoque, PoliticaBaixaEstoque
    infrastructure/
      db/
        models.py               # ORM
        repositories.py         # adaptadores das portas
        session.py              # engine, sessão, criação do schema
      auth/
        jwt.py
        passwords.py
      unit_of_work.py
      serialization.py          # eventos → JSON
      seed.py
  tests/
    unit/domain/
    integration/
```

**Mapeamento bloco DDD → módulo** (caminhos relativos a `backend/app/`)

| Bloco DDD | Onde |
|-----------|------|
| Entity / Aggregate / VO / Domain Event | `domain/<bc>/` |
| Domain Service | `domain/services/` |
| Repository (porta) | `domain/<bc>/repository.py` |
| Repository (adaptador) | `infrastructure/db/repositories.py` |
| Unidade de trabalho | `infrastructure/unit_of_work.py` |
| Application Service / Command | `application/commands/` |
| Read model / Query | `application/queries/` |
| Controllers | `api/routers/` |

---

## 6. Banco de dados — recomendação

**Escolha: PostgreSQL.**

| Critério | Justificativa |
|----------|---------------|
| Transações ACID | OS + baixa de estoque na aprovação precisam de atomicidade (requisito explícito do brief) |
| Modelo relacional | Agregados e relacionamentos por id encaixam bem em tabelas |
| Ecossistema Python | SQLAlchemy 2 e psycopg 3 maduros; fácil no docker-compose |
| MVP | Um único banco; schemas/tabelas por módulo se quiser isolar BCs logicamente |

**Alternativas descartadas:**  
- **MongoDB** — flexível, mas enfraquece invariantes transacionais multi-documento no MVP.  
- **SQLite** — ótimo para teste local, fraco para demonstrar decisão de arquitetura e concorrência de estoque.

---

## 7. Relação documentação ↔ implementação

Caminhos relativos a `backend/app/`.

| Artefato | Implementação |
|----------|---------------|
| Eventos laranja | Dataclasses em `domain/*/events.py`, gravadas na tabela `eventos_dominio` na mesma transação |
| Comandos azuis | Handlers em `application/commands/` |
| Políticas roxas | `domain/services/politica_estoque.py` e métodos de `OrdemDeServico`, chamados pelos comandos |
| Agregados | Classes raiz em `domain/*/aggregate.py` |
| Modelos de leitura verdes | Consultas em `application/queries/`; as de cadastro em `application/commands/cadastros.py` |
| Linguagem ubíqua | Nomes PT no domínio = glossário |
| Máquina de estados | `TRANSICOES` em `domain/ordem_servico/status.py` e `OrdemDeServico._transicionar` |
