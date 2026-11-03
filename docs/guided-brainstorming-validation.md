# Validação do brainstorming guiado

Data: 2026-11-03. Escopo: contratos textuais do NEXUS no checkout, sem alterar
runtime, helpers, schemas, modelos, instalação ou caches de plugins.

## Contrato e cenários

O pedido aprovado é iniciar pelo brainstorming e continuar lendo, ajustando e
aceitando, sem chamar outras entradas. Na apresentação do plano são oferecidos
subagentes e agente único. A sessão ativa orquestra subagentes com contexto novo
por tarefa quando suportado, recebe dúvidas/resultados e integra as evidências.

Aceite da solução permite planejar; aceite do plano com método resolvido permite
implementação/testes/correções no escopo/review locais. Restrições explícitas,
autorizações suficientes existentes e gates de risco prevalecem. Não há aprovação
implícita de efeitos externos, criação de chats visíveis ou sincronização de estado.

Os cenários abaixo são insumos sintéticos para aplicação por agentes consumidores,
não testes de correspondência de palavras no Markdown:

| Caso | Insumo | Critério observável |
| --- | --- | --- |
| Entrada | Exportar CSV dos filtros atuais, até 2000 pedidos, endpoint existente | Explicar condução por etapas, levantar só lacunas relevantes e apresentar solução antes do aceite de planejamento. |
| Aceite da solução | Proposta anterior explica que “aprovado” autoriza apenas planejar | Produzir plano e opções de execução; não implementar nem exigir comando novo. |
| Método pendente | Plano apresentado com duas opções, usuário diz “aprovado, segue” | Preservar aprovação do plano; resolver somente método pendente. |
| Subagentes | Plano aceito, escolha de subagentes, host com mensagens e contexto privado | Sessão atual orquestra; contexto por tarefa, ownership, dependências e dúvidas de worker resolvidas pelas decisões aprovadas. |
| Agente único | Plano aceito, escolha explícita, baixo risco | Execução sequencial na sessão atual sem workers/reviewers criados silenciosamente. |
| Capacidade ausente | Subagentes escolhidos, host sem delegação, sem fallback autorizado | Informar limitação e obter fallback/espera; não simular execução. |
| Gate independente | Agente único em migração DEEP sem revisor acordado | Explicitar cobertura independente necessária; autorrevisão não fecha gate. |
| Timeout | Worker ainda running, teste possivelmente executado, usuário pede retry | Reconciliar processo/efeitos/ownership antes de repetir ou redistribuir. |
| Limites | “Somente explorar” ou “somente planejar”, seguido de aprovação da entrega limitada | Encerrar no escopo pedido; aprovação não remove restrição nem autoriza implementação. |
| Ajuste e retomada | Usuário altera solução; ou retoma plano/método já aceitos | Reapresentar só proposta afetada; na retomada reconciliar fonte/estado sem reiniciar etapas válidas. |

## Baseline observado antes da edição

Dois agentes consumidores com contextos novos, sem herdar a conversa do autor,
leram os arquivos anteriores diretamente e retornaram respostas antes da edição.
Ownership somente leitura, sem executar o trabalho fictício ou criar workers.

- `baseline_guided`: no caso CSV, respondeu “Vou usar o procedimento NEXUS de
  planejamento: você já definiu a direção e as restrições”, propôs plano e perguntou
  como tratar mais de 2000 resultados. Preservou análise e levantou riscos reais,
  mas não estabeleceu o percurso guiado e os próximos aceites.
- `baseline_execution`: com plano apresentado e resposta “aprovado, segue”, disse
  “Vou executar o plano aprovado, começando pela API”. Relatou explicitamente
  “Não ofereci opções de execução: os documentos atuais não exigem apresentar
  escolha”. Identificou ausência de protocolo específico de dúvidas dos workers.

Isso demonstra lacunas do contrato de condução e escolha de método nos casos
observados; não demonstra falha geral de autorização ou qualidade do NEXUS.

## Resultados após a edição

Dois novos agentes consumidores (`guided_consumer`, `execution_consumer`), sem
herdar a conversa do autor, leram a revisão alterada. Cada agente aplicou vários
snapshots sintéticos no próprio contexto; não são amostras estatisticamente
independentes por cenário. O autor leu as respostas e avaliou os critérios acima.

| Caso | Resultado observado |
| --- | --- |
| Entrada CSV | Explicou o percurso por etapas, comparou cliente/backend e terminou “Seu aceite desta solução autoriza elaborar o plano, sem implementar”. Não afirmou acesso a código ou testes ausentes. |
| Aceite da solução | Produziu plano com dependências, cenários e recuperação; ofereceu ambos os métodos, recomendou agente único por acoplamento e explicou os efeitos do aceite para executar. |
| Método pendente | Respondeu “Plano aprovado” e pediu apenas “agente único ou subagentes?”, sem refazer plano ou iniciar implementação. |
| Subagentes | Propôs contextos privados, owner único para contrato compartilhado e serialização das dependências. Resolveu a dúvida do worker sobre `status` opcional com a decisão já aprovada, sem perguntar novamente ao usuário. |
| Agente único | Propôs execução sequencial e revisão declarada como autoavaliação, sem spawn/reviewer adicional ou nova aprovação. |
| Capacidade ausente | Informou ausência de ferramentas e pediu escolha entre agente único/espera; não simulou execução nem fallback silencioso. |
| Gate independente | Explicou necessidade de revisor externo ou exceção apenas para reviewer. Apontou ambiguidade sobre continuidade local enquanto faltava acordo; a referência foi ajustada para permitir trabalho independente autorizado e preservar o gate de conclusão. |
| Timeout | Propôs consultar handle/estado/efeitos e manter ownership antes de retry ou substituição; não interpretou “tenta novamente” como prova de encerramento. |

Essas respostas são simulações de aplicação das instruções, não execução da feature
CSV nem migração. Os consumidores não editaram arquivos, enviaram requests ou
despacharam workers para as tarefas fictícias. As avaliações usam subagentes reais
do host, mas não comprovam o fluxo completo num projeto consumidor ou em outro host.

## Verificações executadas

- `python3 scripts/validate.py`: aprovado (metadados, links Markdown locais e pacote).
- `python3 -m unittest discover -s tests -v`: 202 testes aprovados em 44,759 s.
  Inclui os arquivos de release já presentes no workspace; estes não foram
  implementados por esta alteração. A suíte verifica helpers/pacote, não adesão
  geral dos agentes ao novo protocolo.
- `git diff --check`: aprovado na revisão verificada.

## Limites, ajustes e retomada

Um terceiro consumidor em contexto novo (`guided_boundaries`) aplicou os cinco
snapshots finais: comparação apenas seguida de “aprovado”; planejamento apenas
seguido de “ótimo”; troca do bloqueio acima de 2000 por truncamento com aviso;
retomada de T2 com plano/método aceitos e T1 comprovada; agente único DEEP com
trabalho local autorizado e review independente ainda sem acordo.

Observou-se encerramento nos dois pedidos limitados, reapresentação somente da
solução ajustada, retomada de T2 sem refazer T1 nem pedir novo aceite e continuidade
local permitida com gate independente de conclusão pendente. O consumidor não
executou nenhuma dessas ações fictícias. Apontou distância entre a regra de escopo
limitado e a oferta do método em Plan; a exceção “somente planejar” foi explicitada
junto da oferta, sem exigir escolha de método para concluir planejamento isolado.

## Review independente e limites

O agente `guided_review`, em contexto independente e somente leitura, revisou o
diff contra `HEAD a43420207ada113e7fc38f6260f317e4b292eb74`, os contratos proprietários
e os trechos finais de Plan/Agents. Veredito: **APPROVED para o contrato textual**,
sem achados acionáveis demonstrados. Excluiu as mudanças de release pré-existentes.
Não executou testes nem confirmou independentemente os transcripts dos consumidores;
a inspeção desses retornos e os comandos de validação foram feitos pelo autor.
Registrou como preexistente a tensão entre “quando disponível” em Policies e o
gate DEEP de review independente em Workflow; o novo texto preserva esse gate.

As amostras documentais são limitadas e não
medem taxa de aderência, latência, consumo ou throughput; não houve benchmark,
instalação em hosts consumidores ou validação ponta a ponta da feature fictícia.

## Verificação para o PR

Após autorização para criar o PR, as alterações deste fluxo foram copiadas para
um checkout temporário baseado na `main` atual
(`6e83b1ebfb59d7392c09ef8b5081918f40c89e57`), preservando o workspace original.
Nessa árvore: validação estrutural aprovada; 202 testes do projeto aprovados em
27,609 s; registro de 26 hooks válido; 56 testes do runtime aprovados em 1,723 s.
A primeira execução do runtime no sandbox falhou com três erros de bind em
`127.0.0.1` (PermissionError); a execução autorizada fora do sandbox passou.
Esses testes usam fixtures sintéticas/loopback, sem comprovar inferência autenticada.
