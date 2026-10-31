---
name: nexus
description: Use when a software engineering task needs coordinated specification, architecture, implementation or review across multiple steps, or when the user explicitly requests NEXUS.
---

# NEXUS

Conduza a tarefa até um resultado verificável, com a menor complexidade suficiente. Este pacote fornece instruções e um executor local de estado de tarefas; implementação, testes e dispatch usam as capacidades verificadas do host.

## Entrada

1. Leia o objetivo, as instruções do projeto e o estado atual das fontes relevantes. Reaproveite decisões e autorizações já dadas.
2. Escolha o modo em [workflow](references/workflow.md). Pergunte apenas sobre lacunas que mudam materialmente a entrega e não podem ser resolvidas pelas fontes disponíveis.
3. Registre escopo, critérios de aceite e incertezas proporcionalmente à tarefa. Use os templates somente quando agregarem rastreabilidade.
4. Execute e valide o que foi autorizado. Diferencie resultado observado, inferência e pendência.

## Referências sob demanda

| Situação | Ler |
| --- | --- |
| Planejamento ou execução em etapas | [Workflow](references/workflow.md) |
| Persistência de tarefas, DAG, retomada ou CLI/Markdown do Todo | [Contrato executável](references/workflow-state.md) |
| Escolha de testes, modelo ou contexto | [Políticas](references/policies.md) |
| Delegação ou review independente | [Agentes](references/agents.md) |
| Integração com eventos do host | [Hooks](references/hooks.md) |
| Retomada ou conhecimento reutilizável | [Memória](references/memory.md) |
| Decisão ambígua ou difícil de reverter | [Princípios cognitivos](references/cognitive.md) |

Não carregue todas as referências por padrão. Para uma alteração pequena e clara, trabalhe diretamente com validação proporcional.

## Invariantes

- Siga as instruções de maior prioridade, a política de modelos e os limites de autorização do ambiente. Não peça novamente autorização já concedida; não amplie seu alcance.
- Não invente ferramentas, subagentes, hooks executados, modelos usados, custos, resultados ou persistência. Declare o fallback quando uma capacidade faltar.
- Ao alterar comportamento, considere latência, concorrência, throughput, falhas e recuperação. Aprofunde apenas as dimensões afetadas.
- Não repita mutações externas com resultado incerto. Consulte o estado antes de decidir a recuperação.
- Conclua com mudanças, evidências e limitações materiais. Não trate testes não executados como aprovados.
