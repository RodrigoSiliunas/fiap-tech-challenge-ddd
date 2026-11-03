# Documentação DDD e o código

Este arquivo liga a linguagem ubíqua, o Event Storming e os diagramas ao monólito em `oficina/`. Os nomes do domínio estão em português, como no glossário.

## Contextos e módulos

| Bounded context | Papel | Código |
|-----------------|-------|--------|
| Atendimento / OS (core) | Ordem, itens, orçamento, status | `oficina/domain/ordem_servico/` |
| Cadastro (suporte) | Cliente e Veículo | `oficina/domain/cliente/`, `oficina/domain/veiculo/` |
| Catálogo (suporte) | Serviço | `oficina/domain/servico/` |
| Estoque (suporte) | Peça e quantidade | `oficina/domain/peca/` |
| Identidade (genérico) | JWT administrativo | `oficina/infrastructure/auth/`, `oficina/api/deps.py` |

Os contextos são módulos do mesmo processo. Não há microsserviço nem kernel compartilhado: a OS referencia Cliente, Veículo, Serviço e Peça por id.

## Camadas

| Camada | Pasta | Responsabilidade |
|--------|-------|------------------|
| Interface | `oficina/api/` | Routers FastAPI, DTOs Pydantic, JWT, Swagger |
| Aplicação | `oficina/application/` | Command handlers, consultas, transação |
| Domínio | `oficina/domain/` | Agregados, objetos de valor, eventos, políticas |
| Infraestrutura | `oficina/infrastructure/` | SQLAlchemy, PostgreSQL, repositórios, seed |

A dependência permitida é a do diagrama: API → aplicação → domínio, e aplicação → infraestrutura. O ORM não entra no domínio.

## Agregados, entidades e objetos de valor

| Conceito | Tipo | Código |
|----------|------|--------|
| OrdemDeServico | Agregado raiz | `domain/ordem_servico/aggregate.py` |
| ItemServico, ItemPeca, Orcamento | Entidades internas da OS | mesmo arquivo |
| Cliente | Agregado | `domain/cliente/aggregate.py` |
| Veiculo | Agregado | `domain/veiculo/aggregate.py` |
| Servico | Agregado | `domain/servico/aggregate.py` |
| Peca | Agregado | `domain/peca/aggregate.py` |
| Documento | Objeto de valor | `domain/cliente/documento.py` |
| Placa | Objeto de valor | `domain/veiculo/placa.py` |
| Dinheiro, Quantidade | Objetos de valor | `domain/shared/value_objects.py` |
| StatusOS | Objeto de valor / enum | `domain/ordem_servico/status.py` |

O orçamento permanece dentro da OrdemDeServico. Cliente e Veículo não são aninhados na OS: a ordem guarda `cliente_id` e `veiculo_id`.

## Máquina de estados

`TRANSICOES` em `domain/ordem_servico/status.py` é a única tabela de saltos permitidos. `OrdemDeServico._transicionar` rejeita qualquer outro caminho com o código `transicao_invalida`. Não existe endpoint para “setar status”.

| Comando | Handler | Status resultante |
|---------|---------|-------------------|
| AbrirOrdemDeServico | `application/commands/ordens_servico.py` `AbrirOrdemDeServico` | Recebida |
| IniciarDiagnostico | `IniciarDiagnostico` | Em diagnóstico |
| GerarOrcamento | `GerarOrcamento` | Aguardando aprovação |
| AprovarOrcamento | `AprovarOrcamento` | Em execução |
| RejeitarOrcamento | `RejeitarOrcamento` | Rejeitada |
| FinalizarServico | `FinalizarServico` | Finalizada |
| EntregarVeiculo | `EntregarVeiculo` | Entregue |
| ConsultarStatusOS | `application/queries/ordens_servico.py` `ConsultarAcompanhamento` | leitura |

## Comandos e eventos

Cada comando de escrita é um handler que abre uma unidade de trabalho, altera agregados e faz `commit` uma vez. Os eventos ficam no agregado (`pull_events`) e são gravados na tabela `eventos_dominio` na mesma transação.

| Evento | Classe |
|--------|--------|
| ClienteCadastrado, ClienteIdentificado, ClienteAtualizado | `domain/cliente/events.py` |
| VeiculoRegistrado, VeiculoAtualizado | `domain/veiculo/events.py` |
| ServicoCatalogoCadastrado, ServicoCatalogoAtualizado | `domain/servico/events.py` |
| PecaCadastrada, PecaAtualizada, EstoqueIncrementado, EstoqueAjustado, EstoqueDecrementado | `domain/peca/events.py` |
| OrdemDeServicoRecebida, DiagnosticoIniciado, ServicosIncluidos, PecasIncluidas | `domain/ordem_servico/events.py` |
| OrcamentoGerado, OrcamentoDisponibilizado, OrcamentoAprovado, OrcamentoRejeitado | mesmo arquivo |
| ExecucaoIniciada, ServicoFinalizado, VeiculoEntregue | mesmo arquivo |

`ItemServicoRemovido` e `ItemPecaRemovido` registram a retirada de linha durante o diagnóstico. O board mostra a inclusão; a remoção é o comando inverso, necessário para corrigir o orçamento antes da aprovação.

## Políticas

| Política | Onde |
|----------|------|
| Gerar orçamento quando o diagnóstico está estável | O mecânico dispara `POST /ordens-servico/{id}/orcamento`. O total é calculado pelo agregado, não digitado. |
| Recalcular se os itens mudam em Aguardando aprovação | `OrdemDeServico._recalcular_se_aguardando` |
| Disponibilizar o orçamento ao cliente | Evento `OrcamentoDisponibilizado` e a rota pública de acompanhamento |
| Baixar estoque quando o orçamento é aprovado | `domain/services/politica_estoque.py` `PoliticaBaixaEstoque`, chamada por `AprovarOrcamento` |
| Validar disponibilidade na inclusão, sem reservar | `PoliticaDisponibilidadeEstoque` |
| Recusar transição inválida | `OrdemDeServico._transicionar` |
| Estoque nunca negativo | `Peca.baixar` e `CHECK` no banco |

A aprovação e a baixa de estoque acontecem na mesma unidade de trabalho. Se a baixa falha, a transação desfaz a mudança de status.

## Portas e adaptadores

| Porta | Adaptador |
|-------|-----------|
| `domain/*/repository.py` | `infrastructure/db/repositories.py` |
| Unidade de trabalho usada pelos handlers | `infrastructure/unit_of_work.py` |
| Consulta de tempo médio | `application/queries/tempo_medio_execucao.py` |

O tempo médio é a média de `finalizada_em - execucao_iniciada_em` das OS em Finalizada ou Entregue.

## API e atores

| Ator | Acesso |
|------|--------|
| Atendente, mecânico, administrador | JWT em `/api/v1/auth/login`. No MVP os três usam o mesmo papel ADMIN. |
| Cliente | Sem JWT. Informa o id da OS e o CPF/CNPJ em `/api/v1/publico/ordens-servico`. |
| Sistema | Políticas dentro do comando de aprovação e do recálculo do orçamento. |

Documento inválido ou de outro cliente devolve o mesmo 404 da OS inexistente, para não revelar se a ordem existe.
