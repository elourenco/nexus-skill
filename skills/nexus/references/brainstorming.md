# Brainstorming — Explore

Use para formular o problema, testar premissas e comparar alternativas antes de
definir a direção. É também a entrada padrão do fluxo guiado de criação/alteração
de features: o agente conduz as etapas e o usuário responde em linguagem natural.
Se a direção já está definida, preserve-a e avance para o aceite pertinente antes
de [Plan](plan.md). Perguntas conceituais simples podem ser respondidas diretamente.
Aplica-se o [contrato de invocação](invocation.md).

## Fluxo guiado por aceites

Ao iniciar por brainstorming, conduza entendimento → solução → plano → execução
com validação/review → entrega. Carregue cada procedimento somente ao entrar na
etapa; o usuário não precisa chamar outras entradas. Explique brevemente esse
percurso no início. Pedido explícito de somente explorar, comparar ou planejar
limita o percurso à entrega solicitada.

| Momento | Entrega e próximo efeito apresentado ao usuário |
| --- | --- |
| Entendimento | Consulte fontes e esclareça lacunas materiais; reapresente objetivo, escopo e restrições para correção, sem exigir um aceite por pergunta. |
| Solução | Apresente recomendação, contratos/comportamento e trade-offs proporcionais. Termine indicando que o aceite dessa solução autoriza elaborar o plano, ainda sem implementar. |
| Plano | Execute [Plan](plan.md), apresente incrementos, aceite, verificações e recuperação pertinentes; ofereça o [método de execução](agents.md#metodo-de-execucao). Indique que aprovar esse plano autoriza implementar, testar, corrigir achados no escopo e revisar localmente. |
| Execução e entrega | Com plano e método aceitos, siga [Build](build.md), aplique review proporcional e entregue evidências/pendências. Continue sem aceite por tarefa ou check; volte ao usuário por decisão material, bloqueio indispensável ou mudança de escopo. |

“Aprovado”, “segue” e “pode continuar” aceitam somente a proposta atual e os efeitos
explicitados na mensagem anterior. Não trate silêncio, leitura, resposta a uma
dúvida ou aprovação parcial como aceite global. Se faltou explicitar o efeito ou
há alvos concorrentes, esclareça antes da ação dependente. Pedido de ajuste mantém
a etapa: incorpore-o e reapresente a proposta afetada, sem reiniciar o fluxo.

Preserve aceites e método já definidos para o mesmo alvo/escopo. Se o usuário já
autorizou etapas seguintes, avance dentro dessa autorização sem nova confirmação.
Aceites não autorizam commit, push, merge, deploy ou outros efeitos externos.
Na retomada, reconcilie alvo, proposta/aceites, método, pendências e estado real na
fonte existente; sem registro suficiente, esclareça somente a lacuna. O chat não
é persistência garantida entre sessões e este fluxo não inicializa helpers.

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

Quando a escolha envolver interfaces, dependências ou sistemas, use a seção
pertinente de [design](architecture-design.md) para investigar o fluxo real e
comparar abordagens. Para alternativas de refatoração, consulte os
[padrões pelo problema](refactoring.md#padroes). Não carregue catálogo para uma
pergunta conceitual simples nem reabra arquitetura aprovada sem evidência material.

Quando houver [gatilho de segurança/ética](ai-safety-ethics.md#risk-triggers),
identifique finalidade, pessoas afetadas e danos previsíveis; compare alternativas
com menor exposição de dados ou autonomia, inclusive sem IA quando suficiente.
Explicite a evidência que falta para avaliar impactos. A discussão não autoriza
coleta de dados sensíveis nem cria auditoria extensa para uma questão simples.

Entregue problema/restrições, alternativas com trade-offs, recomendação e questões
abertas. Use [SPEC](../assets/templates/spec.md) ou [ADR](../assets/templates/adr.md)
somente se um registro persistente for necessário. No fluxo guiado, aguarde o
aceite da solução para planejar e do plano para implementar, salvo autorização
existente suficiente. Se o pedido for apenas explorar, encerre na recomendação.

Exemplo: “Brainstorming do NEXUS: dois dispositivos editam offline o mesmo registro;
compare alternativas, sem implementar.” A entrega distingue política de conflito
de mecanismo de sincronização e explicita que evidência falta para decidir.
