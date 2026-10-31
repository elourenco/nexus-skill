# Eventos lógicos — sem executor nesta fase

Os nomes abaixo organizam decisões do agente. Não são hooks registrados no Codex, Claude ou em outro host. Sem adapter implementado e verificado, realize a checagem diretamente e informe que foi manual.

| Evento | Gatilho | Saída esperada |
| --- | --- | --- |
| `context.load` | Início ou retomada | Fontes pertinentes e estado verificado |
| `architecture.guard` | Mudança de contrato/fronteira | Invariantes e decisão necessária |
| `model.route` | Delegação relevante | Papel e seleção disponível no host |
| `budget.check` | Antes de trabalho limitado por orçamento | Limite conhecido ou indisponibilidade declarada |
| `validation.run` | Incremento revisável | Comando, resultado e evidência |
| `review.dispatch` | Risco que justifique revisão | Pilares, ownership e achados |
| `failure.recover` | Falha de validação/execução | Diagnóstico e próxima ação limitada |
| `memory.capture` | Aprendizado duradouro autorizado | Registro com proveniência |
| `completion.verify` | Conclusão | Aceite satisfeito ou pendências explícitas |

## Contrato para futuros adapters

Um adapter deverá declarar versão, evento, workspace, tarefa, attempt ID, timeout, política de falha e permissões. Eventos não carregam segredos nem histórico completo.

Operações determinísticas não exigem modelo. Operações cognitivas precisam justificar contexto e custo. O executor futuro deverá limitar concorrência, rejeitar efeitos duplicados e tratar cancelamento; nenhuma dessas garantias está implementada nesta base.

Gates obrigatórios não podem virar sucesso quando o executor falhar. Telemetria opcional pode falhar sem impedir trabalho, com falha registrada. Para mutações de resultado incerto, reconciliar estado antes de retry; o nome do evento não garante idempotência.
