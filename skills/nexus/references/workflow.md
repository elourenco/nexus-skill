# Modos e artefatos

| Modo | Entrega |
| --- | --- |
| Explore | Fontes relevantes, problema e lacunas materiais |
| Plan | Spec proporcional, alternativas quando necessárias, tarefas e validações |
| Build | Incremento autorizado, validado e revisável |
| Review | Achados verificáveis priorizados por impacto |
| Autonomous | Mesmo fluxo, avançando dentro do escopo e das autorizações existentes |

Não transforme os modos em cerimônias obrigatórias para cada ajuste. Autonomous não concede novas permissões.

## Planejamento

Use [spec](../assets/templates/spec.md) quando houver comportamento ou contrato a definir. Use [plano](../assets/templates/plan.md) para múltiplas etapas e [ADR](../assets/templates/adr.md) para decisão arquitetural duradoura. A aprovação exigida é a do host/projeto; reutilize a aprovação que já cobre a tarefa.

No projeto consumidor, mantenha os artefatos em `docs/nexus/specs/`, `docs/nexus/plans/`, `docs/nexus/tasks/` e `docs/nexus/decisions/`, criando apenas diretórios usados. Vincule plano à versão/commit da spec; mudanças materiais invalidam as tarefas afetadas até reconciliação.

## Execução e todo

Use [tarefa](../assets/templates/task.md) para unidades que precisem de retomada. Estados: `pending`, `ready`, `running`, `blocked`, `done`, `cancelled`. Uma tarefa fica `ready` quando suas dependências e autorizações estiverem satisfeitas; `done` exige evidências de aceite. Cancelamento não desfaz efeitos já aplicados.

Mantenha um responsável por arquivo/recurso compartilhado. Antes de executar em paralelo, verifique dependências, banco, portas, worktrees e limites do host. Sem isolamento, execute em sequência. O checklist do plano é a visão manual do progresso; use o todo interativo nativo se disponível, sem afirmar sincronização automática.

## Recuperação

Após duas tentativas sem progresso verificável, interrompa a repetição: registre reprodução, evidências, hipóteses descartadas e dependências. Corrija contexto ou ambiente antes de escalar capacidade. Escale conforme a política do host; se faltar autorização ou insumo indispensável, marque o impedimento e continue apenas tarefas independentes.

Na retomada, confira o estado real dos arquivos e das operações externas. Um checkpoint documentado não prova que uma operação terminou ou foi revertida.
