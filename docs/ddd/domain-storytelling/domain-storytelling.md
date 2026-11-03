# Domain Storytelling — Oficina Mecânica (MVP)

> Pictogramas + sentenças numeradas conforme Aula 02 (FIAP) e notação [Domain Storytelling](https://domainstorytelling.org/) / [Egon](https://egon.io/app/).
> Termos exatos da [linguagem ubíqua](../linguagem-ubiqua.md). Alinhado ao [Event Storming](../event-storming.md).

Arquivos por história (mesmo basename):

| Basename | `.egn` (Egon) | Fallback |
|----------|---------------|----------|
| `01-abertura-os` | importável em egon.io | `.svg` / `.png` |
| `02-diagnostico-orcamento` | idem | idem |
| `03-aprovacao-rejeicao` | idem | idem |
| `04-execucao-entrega` | idem | idem |
| `05-gestao-estoque` | idem | idem |

Formato `.egn`: wrapper `{ "domain": { name, actors, workObjects }, "dst": [ ...elementos, {info}, {version} ] }` (compatível com export v2.2.x / import legado do Egon; ver `WPS/egon.io` → `src/app/tools/import/services/test-files/dst_export_version_2_2_0.json`).

---

## 1. Abertura da Ordem de Serviço

**Arquivos:** `01-abertura-os.egn` · `01-abertura-os.svg` · `01-abertura-os.png`

### Escopo

| Dimensão | Valor | Justificativa |
|----------|-------|---------------|
| Grain | **coarse** | Cobre identificação + veículo + abertura da OS sem detalhar validações de CPF/placa |
| Purity | **digitalized** | Atendente opera o Sistema; cadastro e OS são digitais |
| Point in time | **to-be** | Fluxo do MVP a construir (brief FIAP) |

### Sentenças numeradas

1. **Atendente** *identifica* **Documento** (CPF/CNPJ) → **Cliente** (cadastra se novo).
2. **Atendente** *registra* **Veículo** (placa, marca, modelo, ano).
3. **Atendente** *abre* **Ordem de Serviço** (status **Recebida**).

### Ligação ao Event Storming

| Sentença | Comandos / eventos | Agregados |
|----------|--------------------|-----------|
| 1 | `IdentificarCliente` → `ClienteIdentificado` (ou `ClienteCadastrado`) | **Cliente** |
| 2 | `RegistrarVeiculo` → `VeiculoRegistrado` | **Veículo** |
| 3 | `AbrirOrdemDeServico` → `OrdemDeServicoRecebida` (pivotal) | **OrdemDeServico** |

Hotspot resolvido no ES: cliente inexistente → cadastrar na abertura.

---

## 2. Diagnóstico e orçamento

**Arquivos:** `02-diagnostico-orcamento.egn` · `.svg` · `.png`

### Escopo

| Dimensão | Valor | Justificativa |
|----------|-------|---------------|
| Grain | **fine** | Inclui itens de serviço/peça, verificação de estoque e geração automática |
| Purity | **digitalized** | Sistema gera e disponibiliza o orçamento |
| Point in time | **to-be** | MVP |

### Sentenças numeradas

1. **Mecânico** *inicia diagnóstico em* **Ordem de Serviço** (status **Em diagnóstico**).
2. **Mecânico** *inclui* **Serviços** (catálogo → `ItemServico`).
3. **Mecânico** *inclui* **Peças** (valida disponibilidade no **Estoque**; ainda sem baixa).
4. **Sistema** *gera* **Orçamento** (soma automática; status **Aguardando aprovação**).
5. **Sistema** *disponibiliza* **Orçamento** ao **Cliente**.

### Ligação ao Event Storming

| Sentença | Comandos / eventos / políticas | Agregados |
|----------|--------------------------------|-----------|
| 1 | `IniciarDiagnostico` → `DiagnosticoIniciado` | **OrdemDeServico** |
| 2 | `IncluirServicos` → `ServicosIncluidos` | **OrdemDeServico** (+ catálogo **Serviço**) |
| 3 | `IncluirPecas` → `PecasIncluidas` | **OrdemDeServico** + leitura de **Peça** |
| 4 | Política *Gerar orçamento automático* → `GerarOrcamento` → `OrcamentoGerado` | **OrdemDeServico** (`Orcamento` interno) |
| 5 | Política *Disponibilizar ao cliente* → `OrcamentoDisponibilizado` | read model DetalheOrcamento |

---

## 3. Aprovação ou rejeição do orçamento

**Arquivos:** `03-aprovacao-rejeicao.egn` · `.svg` · `.png`

Duas histórias no mesmo diagrama (Aula 02: condicionais viram histórias distintas — aqui lado a lado).

### Escopo

| Dimensão | Valor | Justificativa |
|----------|-------|---------------|
| Grain | **fine** | Explicitam baixa de estoque e mudança de status |
| Purity | **digitalized** | Decisão do Cliente via API; Sistema aplica políticas |
| Point in time | **to-be** | MVP |

### Sentenças — caminho feliz (aprovação)

1. **Cliente** *aprova* **Orçamento**.
2. **Sistema** *baixa* **Estoque** das **Peças** (`ItemPeca`).
3. **Sistema** *inicia execução de* **Ordem de Serviço** (status **Em execução**).

### Sentenças — caminho alternativo (rejeição)

4. **Cliente** *rejeita* **Orçamento**.
5. **Sistema** *marca como Rejeitada* a **Ordem de Serviço** (fim do fluxo feliz).

### Ligação ao Event Storming

| Sentença | Comandos / eventos / políticas | Agregados |
|----------|--------------------------------|-----------|
| 1 | `AprovarOrcamento` → `OrcamentoAprovado` | **OrdemDeServico** |
| 2–3 | Política *OrcamentoAprovado → BaixarEstoque + iniciar execução* → `EstoqueDecrementado` | **Peça** + **OrdemDeServico** |
| 4–5 | `RejeitarOrcamento` → `OrcamentoRejeitado` (status **Rejeitada**) | **OrdemDeServico** |

Decisão MVP (hotspot ES): baixa de estoque **na aprovação**, não na finalização.

---

## 4. Execução até entrega (e acompanhamento)

**Arquivos:** `04-execucao-entrega.egn` · `.svg` · `.png`

### Escopo

| Dimensão | Valor | Justificativa |
|----------|-------|---------------|
| Grain | **coarse** | Transições de status até entrega + consulta |
| Purity | **digitalized** | Status exposto pela API |
| Point in time | **to-be** | MVP |

### Sentenças numeradas

1. **Mecânico** *executa* **Ordem de Serviço** (permanece **Em execução**).
2. **Mecânico** *finaliza* **Ordem de Serviço** (status **Finalizada**).
3. **Atendente** *entrega* **Veículo** ao **Cliente**.
4. **Atendente** / **Sistema** *atualiza* **Ordem de Serviço** para **Entregue**.
5. **Cliente** *consulta* **Status da OS** via **Sistema / API**.

### Ligação ao Event Storming

| Sentença | Comandos / eventos | Agregados / read models |
|----------|--------------------|-------------------------|
| 1–2 | `FinalizarServico` → `ServicoFinalizado` | **OrdemDeServico** |
| 3–4 | `EntregarVeiculo` → `VeiculoEntregue` | **OrdemDeServico** |
| 5 | `ConsultarStatusOS` (somente leitura) | **StatusOSView** (chave: id da OS + Documento) |

FSM: `Em execução → Finalizada → Entregue`.

---

## 5. Gestão de estoque e catálogo (admin)

**Arquivos:** `05-gestao-estoque.egn` · `.svg` · `.png`

### Escopo

| Dimensão | Valor | Justificativa |
|----------|-------|---------------|
| Grain | **fine** | Cadastro de Peça/Serviço e movimentos de estoque |
| Purity | **digitalized** | Admin autentica (JWT) e opera o Sistema |
| Point in time | **to-be** | MVP |

### Sentenças numeradas

1. **Administrador** *cadastra / atualiza* **Peça**.
2. **Administrador** *cadastra / atualiza* **Serviço** (catálogo).
3. **Administrador** *registra entrada em* **Estoque**.
4. **Administrador** *ajusta* **Estoque** via **Sistema** (quando necessário).

### Ligação ao Event Storming

| Sentença | Comandos / eventos | Agregados |
|----------|--------------------|-----------|
| 1 | `CadastrarPeca` / `AtualizarPeca` → `PecaCadastrada` / `PecaAtualizada` | **Peça** |
| 2 | `ServicoCatalogoCadastrado` / `Atualizado` | catálogo **Serviço** |
| 3 | `RegistrarEntradaEstoque` → `EstoqueIncrementado` | **Peça** |
| 4 | `AjustarEstoque` → `EstoqueAjustado` | **Peça** |

A baixa automática (`BaixarEstoque` / `EstoqueDecrementado`) aparece na história 03, disparada por `OrcamentoAprovado`.

---

## Atores e work objects (vocabulário)

| Papel no diagrama | Tipo Egon | Nome ubíquo |
|-------------------|-----------|-------------|
| Atendente, Mecânico, Administrador, Cliente | `domainStory:actorPerson` | conforme glossário |
| Sistema / API | `domainStory:actorSystem` | Sistema |
| Ordem de Serviço, Documento | `workObjectAssignment` / `Document` | OS, Documento |
| Veículo | `workObjectCar` | Veículo |
| Orçamento | `workObjectEuro` | Orçamento |
| Peça / Estoque | `workObjectShopping` / `Label` | Peça, Estoque |
| Serviço | `workObjectWrench` | Serviço |
| Status da OS | `workObjectInfo` | Status da OS |
| Catálogo | `workObjectFolder` | Catálogo |

Ícones apenas do set built-in do Egon (`builtInIcons.ts`).
