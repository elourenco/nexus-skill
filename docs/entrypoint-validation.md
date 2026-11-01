# Integração da entrada — 2026-10-31

A entrada preserva `name: nexus`, modos e carregamento sob demanda, e passa a apontar para os contratos efetivamente integrados. Não instala componentes nem amplia autorizações.

## Cenários documentais revisados

- Pergunta conceitual simples: resposta direta em Explore, sem artefatos obrigatórios.
- Refatoração em etapas: workflow, políticas e templates pertinentes, com testes proporcionais.
- Retomada com CLI opt-in: JSON é autoridade; projeção Markdown não altera estado; run incerto exige reconciliação.
- Retomada documental sem executor: TASKS Markdown são autoridade, sem simular persistência nativa.
- Memória de projeto: helper JSON e seu contrato; registros SQLite dos hooks não são consultados ou sincronizados automaticamente.
- Hook indisponível: checagem manual explícita mantém gates; recomendações não equivalem a execução ou review.
- Delegação indisponível: fallback sequencial, sem alegar independência.
- Teto rígido sem controle verificável: suspender trabalho dependente até revisar escopo/limite.

A regra de escopo em AGENTS.md agora reflete os componentes já aprovados, mantendo expansão futura dependente de escopo próprio. Estes cenários são avaliação documental, não E2E em hosts consumidores; desempenho, tokens e custos não foram medidos.
