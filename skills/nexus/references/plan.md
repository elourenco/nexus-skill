# Planejamento — Plan

Use quando houver uma direção a detalhar em contratos, etapas e validação.
Aplica-se o [contrato de invocação](invocation.md). Preserve decisões já tomadas;
reabra somente as contraditas por novas evidências ou restrições materiais.

## Procedimento

**Entrada:** direção e restrições existentes. **Decisão:** contratos, sequência e
ownership. **Evidência:** fontes e validações propostas identificadas como tais.
**Saída:** etapas verificáveis; aceite de planejamento não comprova implementação.

1. Consulte objetivo, fontes atuais, SPEC/ADR/plano existente e escopo autorizado.
   Sem direção suficiente, delimite a decisão pendente e use
   [brainstorming](brainstorming.md) apenas para resolvê-la. Lacunas independentes
   não impedem planejar o restante.
2. Aplique [Workflows](workflow.md) para decomposição e fonte de estado. Defina
   contratos, invariantes, critérios de aceite e compatibilidade nas fronteiras
   alteradas. Não crie SPEC, ADR e DAG completos para uma tarefa trivial.
3. Decomponha em incrementos verificáveis: arquivos ou componentes afetados,
   dependências, ownership, validação e condição de conclusão. Trate latência,
   throughput, concorrência e falhas conforme o comportamento; reserve recursos
   compartilhados antes de propor execução paralela.
4. Inclua migração, rollout compatível e recuperação quando pertinentes. Distinga
   rollback de código de reversão de dados/efeitos. Nomeie hipóteses, bloqueios e
   verificações ainda necessárias; não estime desempenho sem dados.

## Entrega e limite

Entregue objetivo/escopo, decisões preservadas, etapas com dependências, aceite,
estratégia de validação, riscos/recuperação e pendências. Use o
[template de plano](../assets/templates/plan.md) se houver necessidade de arquivo,
vinculando fontes e revisões conhecidas; não invente hashes ou aceites.

Planejar não autoriza implementar. Quando o pedido incluir execução e as decisões
necessárias estiverem resolvidas, continue em Build dentro da autorização existente.
Uma lacuna que altere contrato ou risco bloqueia somente a ação dependente.

Exemplo: “NEXUS plan: versão otimista já escolhida; planeje resposta 409 e preservação
da edição local.” Preserve a escolha e detalhe atualização atômica, contrato do
conflito e cenários de concorrência, em vez de rediscutir toda a arquitetura.
