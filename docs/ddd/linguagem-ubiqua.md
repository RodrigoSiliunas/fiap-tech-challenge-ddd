# Linguagem Ubíqua — Oficina Mecânica (MVP)

> Glossário do domínio do Sistema Integrado de Atendimento e Execução de Serviços.
> Alinhado à Aula 03 (Descoberta e formação do conhecimento): termos únicos, sem ambiguidade, usados no código e na conversa com o negócio.

## Decisão de nomenclatura no código

**Escolha:** nomes de domínio em **português** no código (`OrdemDeServico`, `Cliente`, `Peca`, `Orcamento`); camadas técnicas e infraestrutura em inglês (`application`, `infrastructure`, `api`, `repository`).

**Por quê:** a linguagem ubíqua deve “falar a língua do negócio” (Evans / Aula 03). O Domain Expert da oficina pensa em OS, orçamento, peça e placa — não em `WorkOrder` ou `Quote`. Manter os mesmos termos no domínio reduz a distância mental entre documentação, apresentação e implementação, o que é exatamente o que a FIAP avalia no vídeo e na defesa.

**Alternativa descartada:** inglês puro no domínio (comum em libs Python). Descartada porque o avaliador e o brief estão em português e a consistência com a linguagem ubíqua da disciplina pesa mais que o idiomático “Pythonic English” neste MVP acadêmico.

**Convenção consistente:**
| Camada | Idioma | Exemplos |
|--------|--------|----------|
| Domínio (entidades, VOs, agregados, eventos, comandos) | Português | `OrdemDeServico`, `StatusOS`, `OrcamentoAprovado` |
| Aplicação / API / Infra | Inglês técnico | `CriarOrdemDeServicoHandler`, `router`, `SQLAlchemy` |
| Pacotes raiz | Inglês (estrutura) + domínio PT | `domain/ordem_servico/`, `application/commands/` |

---

## Glossário

| Termo | Definição | Contexto | Nome no código |
|-------|-----------|----------|----------------|
| **Ordem de Serviço (OS)** | Documento que registra o atendimento de um veículo: serviços solicitados, peças, orçamento e ciclo de status até a entrega. | Atendimento / Execução | `OrdemDeServico` |
| **Status da OS** | Estado atual do ciclo de vida da OS. Valores: Recebida, Em diagnóstico, Aguardando aprovação, Em execução, Finalizada, Entregue; e Rejeitada (caminho de rejeição do orçamento). | Atendimento | `StatusOS` (enum / VO) |
| **Cliente** | Pessoa física ou jurídica dona do veículo, identificada por CPF ou CNPJ. | Cadastro | `Cliente` |
| **Documento (CPF/CNPJ)** | Identificador fiscal validado do cliente. Imutável como valor; troca implica novo VO. | Cadastro | `Documento` |
| **Veículo** | Automóvel atendido pela oficina, identificado pela placa, com marca, modelo e ano. | Cadastro | `Veiculo` |
| **Placa** | Identificador legal do veículo (padrão Mercosul ou antigo), validado. | Cadastro | `Placa` |
| **Serviço (catálogo)** | Tipo de serviço oferecido pela oficina (ex.: troca de óleo, alinhamento), com preço de referência. | Catálogo | `Servico` |
| **Item de Serviço** | Linha da OS que referencia um serviço do catálogo (e preço aplicado naquele momento). | Atendimento | `ItemServico` |
| **Peça / Insumo** | Material físico controlado em estoque, usado na execução de serviços. | Estoque | `Peca` |
| **Item de Peça** | Linha da OS que reserva/consome quantidade de uma peça, com preço unitário. | Atendimento / Estoque | `ItemPeca` |
| **Estoque** | Quantidade disponível de uma peça. Decrementa na aprovação/execução conforme política. | Estoque | `QuantidadeEstoque` (atributo do agregado `Peca`) |
| **Orçamento** | Soma automática dos itens de serviço e peças da OS, apresentada ao cliente para aprovação ou rejeição. | Atendimento | `Orcamento` (entidade interna do agregado OS) |
| **Aprovação do orçamento** | Decisão do cliente que autoriza a execução. Dispara transição para Em execução e políticas de estoque. | Atendimento | evento `OrcamentoAprovado` |
| **Rejeição do orçamento** | Decisão do cliente que recusa o orçamento. OS vai para status Rejeitada (fim do fluxo feliz). | Atendimento | evento `OrcamentoRejeitado` |
| **Diagnóstico** | Fase em que a oficina avalia o veículo e pode ajustar serviços/peças antes de gerar o orçamento final. | Atendimento | status `EM_DIAGNOSTICO` |
| **Tempo médio de execução** | Métrica calculada entre início da execução e finalização das OS concluídas. | Monitoramento (read model) | `TempoMedioExecucao` (modelo de leitura) |
| **Atendente / Mecânico** | Atores internos que operam a OS (abertura, diagnóstico, execução, finalização, entrega). | Atores | (atores do Event Storming; usuário autenticado via JWT) |
| **Cliente (ator)** | Papel que consulta status e aprova/rejeita orçamento via API. | Atores | endpoint público/cliente |
| **Dinheiro** | Valor monetário (centavos + moeda), imutável. | Transversal | `Dinheiro` |
| **Quantidade** | Medida de unidades de peça (≥ 0), imutável. | Estoque / OS | `Quantidade` |

### Termos ambíguos resolvidos (Aula 03)

| Risco | Resolução |
|-------|-----------|
| “Serviço” = tipo do catálogo **ou** linha da OS | Catálogo = `Servico`; linha = `ItemServico` |
| “Cliente” = pessoa cadastrada **ou** ator da API | Cadastro = `Cliente`; ator = “Cliente (ator)” na documentação |
| “Orçamento” como documento separado | No MVP, `Orcamento` vive **dentro** do agregado `OrdemDeServico` (ver diagramas) |

### Sinônimos evitados

- Não usamos “pedido”, “ticket” ou “work order” no domínio.
- Não usamos “produto” para peça — sempre **Peça/Insumo**.
- Status sempre com os nomes do brief (Recebida, Em diagnóstico, …), nunca “open/closed”.
