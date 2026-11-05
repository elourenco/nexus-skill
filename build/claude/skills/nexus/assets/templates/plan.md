# Plano: título

Use [contratos e perfis](contracts.md). O plano descreve como entregar a SPEC;
referencie requisitos/aceites por ID em vez de reproduzi-los.
Apresente o arquivo conforme [painel nativo](../../references/chat.md#spec-e-plano-em-painel-nativo).

- ID e revisão:
- spec_id:
- Spec e revisão/commit (link):

## Resultado e estratégia

- Resultado esperado (aceites da SPEC):
- Estratégia de implementação incremental:
- Arquivos ou módulos previstos:
- Dependências e sequência:

## Execução Git — quando aplicável

Use a [política Git](../../references/git.md); referencie decisões já registradas.
Esta seção é documental e não adiciona campos ao store da CLI.

- Base/destino e revisão conhecida (ou proposta a confirmar antes de editar):
- Branch/worktree do plan e isolamento de tasks paralelas, quando houver:
- Autorizações existentes e pendentes (implementar, commits locais, integração e publicação):
- Incrementos previstos de commit e checks pertinentes (sem contagem artificial):
- Responsável, ordem e estratégia de integração; validação do resultado combinado:

## Etapas de entrega

Repita o bloco por incremento verificável, com título concreto e numeração em
ordem de dependência. Ele descreve o trabalho proposto; estado de execução vem
da fonte adotada no Todo. Omita orientações do template no documento preenchido.

### 1. Título da entrega

- Mudança e arquivos/componentes:
- Dependências e responsável, quando houver mais de um:
- Validação proposta (cenário/comando e aceite referenciado):
- Condição de conclusão:

## Validação e recuperação

- Estratégia de testes proporcional ao risco:
- Recursos compartilhados e limites de concorrência:
- Recuperação/rollback, quando aplicável (gatilho, ação e verificação):

Quando houver [produto com IA](../../references/ai-safety-ethics.md#ai-products),
use estratégia/dependências para atribuir controles e responsáveis; testes para
cenários de dano/erro pertinentes; recuperação para controle indisponível, revisão
humana e efeitos incertos. Referencie o aceite da SPEC, sem duplicar seus critérios.

## Decisões, quando necessárias

- Arquitetura proposta e fronteiras afetadas:
- Alternativas e trade-offs relevantes (ou link para ADR):

## Todo

No modo documental, visão derivada das TASKS conforme o [Interactive Todo Contract](contracts.md#interactive-todo-contract).
Cada linha contém ID/link, estado, responsável/papel, modelo efetivo ou
indisponível, dependências, bloqueios e próxima ação. Declare data da leitura
quando salvar a visão; reabra a TASK antes de executar. Não mantenha outro estado
independente em checkboxes.

Com a CLI de workflow opt-in, o Todo é derivado exclusivamente do store JSON por `show`; consulte a revisão global antes de `apply`. Este PLAN continua documento, sem sincronização bidirecional. Não edite TASKS Markdown para alterar o estado do executor.

## Validação final

- Comandos/cenários necessários e aceites cobertos:
- Evidências coletadas (IDs/links):
- Pendências e riscos residuais:
