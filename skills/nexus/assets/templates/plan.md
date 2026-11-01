# Plano: título

Use [contratos e perfis](contracts.md). O plano descreve como entregar a SPEC;
referencie requisitos/aceites por ID em vez de reproduzi-los.

- ID e revisão:
- spec_id:
- Spec e revisão/commit (link):
- Resultado esperado (aceites da SPEC):
- Estratégia de implementação incremental:
- Arquivos ou módulos previstos:
- Dependências e sequência:
- Estratégia de testes proporcional ao risco:
- Recursos compartilhados e limites de concorrência:
- Recuperação/rollback, quando aplicável (gatilho, ação e verificação):

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
