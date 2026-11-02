# Brainstorming — Explore

Use para formular o problema, testar premissas e comparar alternativas antes de
definir a direção. Se a direção já está definida e o pedido é sequenciar trabalho,
use [Plan](plan.md). Perguntas conceituais simples podem ser respondidas diretamente.
Aplica-se o [contrato de invocação](invocation.md).

## Procedimento

**Entrada:** problema e restrições. **Decisão:** alternativas viáveis e recomendação.
**Evidência:** fontes, premissas e experimento discriminante quando necessário.
**Saída:** direção ou lacuna decisiva; discussão não autoriza implementação.

1. Identifique resultado desejado, contexto existente, restrições e decisões já
   tomadas. Consulte as fontes disponíveis antes de perguntar; esclareça somente
   lacunas que possam mudar a recomendação.
2. Aplique [Cognitive Principles](cognitive.md) quando houver ambiguidade ou decisão
   material. Separe fatos, hipóteses e preferências. Reutilize padrões do projeto.
3. Compare alternativas viáveis, incluindo manter a solução atual quando fizer
   sentido. Avalie complexidade, compatibilidade, reversibilidade e impacto em
   latência, throughput, concorrência e recuperação nas dimensões afetadas. Não
   invente benchmarks nem ofereça alternativas artificiais para preencher tabela.
4. Recomende uma direção com os motivos, o principal trade-off e a evidência que
   mudaria a escolha. Se faltar evidência decisiva, proponha uma investigação ou
   experimento delimitado; execute-o somente se estiver no escopo autorizado.

## Entrega e limite

Entregue problema/restrições, alternativas com trade-offs, recomendação e questões
abertas. Use [SPEC](../assets/templates/spec.md) ou [ADR](../assets/templates/adr.md)
somente se um registro persistente for necessário. Encerre na recomendação quando
o pedido for apenas explorar; não converta discussão em implementação. Um pedido
que também autorize planejar ou construir pode continuar na etapa correspondente.

Exemplo: “Brainstorming do NEXUS: dois dispositivos editam offline o mesmo registro;
compare alternativas, sem implementar.” A entrega distingue política de conflito
de mecanismo de sincronização e explicita que evidência falta para decidir.
