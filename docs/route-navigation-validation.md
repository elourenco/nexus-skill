# Validação de navegação por rotas — 2026-11-03

## Escopo

Índice Markdown com dependências obrigatórias, condicionais e informativas;
status curto, critérios de review separados do registry, mínimo compartilhado,
FAST proporcional, recuperação de leitura/Git e consolidação da evidência final.
Sem resolver executável, cache persistente, novas dependências ou alteração do runtime.

A base do PR é `d068655` (main). Apenas otimizações locais pertinentes foram
portadas; o checkout original permaneceu intacto. Instalação, manifests, metadados
de UI e CI atuais foram preservados. O suporte a campos Claude de listing foi
mantido no validador.

## Evidência anterior e método

Os rastros existentes do benchmark de 96 execuções motivaram as mudanças:
status carregava Workflow/Policies, review relia policies e a retomada tentou
extrair um ID HTML como heading, recebeu vazio e leu policies inteiro.
Esse benchmark pertence ao snapshot anterior e não mede esta candidata.

As verificações abaixo combinam testes estruturais reais e aplicação manual em
agentes com contextos novos por grupo. Casos de um grupo compartilharam contexto;
não são repetições independentes nem uma avaliação cega de desempenho. Agentes
receberam pedidos sintéticos e a instalação, sem respostas esperadas ou diff.
Nenhuma nova matriz autenticada foi executada; não há ganho medido de tokens,
latência, throughput ou custo. Carregamento nativo e multiagente continuam fora
desta avaliação.

## Navegação estrutural

- Test-first do validador: 22 testes, seis falhas esperadas antes da implementação
  de fragments; depois 22/22. Uma regressão adicional no pacote real relocado
  completou 23/23: remover um ID HTML invalida seu link sem invalidar um heading existente.
- Cobertura: anchors ausentes, IDs HTML, headings Unicode/formatados/duplicados,
  links com paths codificados, links fora do pacote, exemplos em blocos de código,
  núcleo isolado e instalação relocada.
- A primeira validação das novas rotas detectou dois links para um heading
  cognitivo inexistente. Foram corrigidos para `seleção-adaptativa` e revalidados.
- O contrato de leitura distingue heading de ID HTML; saída vazia exige localizar
  o destino e ampliar a janela, nunca alegar leitura bem-sucedida.

## Aplicação comportamental observada

| Grupo/cenário | Resultado observado |
| --- | --- |
| Status: testes A, código/configuração B | Recusou conclusão; evidência de A histórica, cobertura afetada de B pendente; não alegou falha em B |
| Status: integração obrigatória indisponível | Manteve gate pendente, sem dispensa por unitários aprovados |
| Status: DEEP sem revisor independente | Manteve conclusão bloqueada; prazo não substituiu independência |
| Status: accepted op-7 e timeout | Bloqueou reenvio; exigiu reconciliação pela identidade |
| Status: teto100, consumo60, reserva40, passo10 | Não iniciou passo; computou agregado110; não ignorou consumo em voo |
| Status: host running, documento DONE, alvo alterado | Reportou estado não reconciliado; não retomou execução |
| Review: cache só por key com contrato tenant/key | Identificou isolamento violado, com caso discriminante |
| Review: await entre lookup e gravação | Identificou duplicação concorrente; distinguiu inspeção de teste executado |
| Review: retenção/payload diferentes não especificados | Não transformou política desconhecida em defeito confirmado |
| Review: alvo muda após relatório | Invalidou cobertura afetada; decisão da nova revisão inconclusiva |

Status carregou entrada, índice, invocation e status; para budget, localizou
headings/IDs e leu só a seção de limites. Nos outros casos não carregou Agents,
Workflow ou policies. Review especializado carregou entrada, invocation,
procedimento, critérios e apenas o gatilho pertinente de segurança/ética; não leu
o registry Agents, policies inteiro ou o índice geral. O avaliador também leu
instruções do host (RTK e using-superpowers, cujo fluxo delegado foi dispensado),
logo esse ensaio não representa isolamento completo do host.

## Aplicação FAST em fixture isolada

Um terceiro agente recebeu a entrada especializada Build e criou uma fixture Python
sem Git fora do repositório. Leu somente a entrada, invocation e build (além de RTK).
Implementou `value.strip()`, observou três testes falhando antes e três passando
depois, detectou ausência de Git uma vez e conferiu diff contra cópia inicial.
Não criou artefatos de workflow ou carregou Policies. O ensaio criou seus próprios
testes; não representa redução do número de testes em comparação com a baseline.
Não alegou rejeição universal de objetos com método `strip` além dos casos cobertos.

Em caso separado, rejeitou FAST para novos tipos aceitos e cache concorrente:
exigiu cenários de contrato/falha e reclassificação pelo risco antes da alteração.

## Checks executados

- `python3 scripts/validate.py`: passou.
- `python3 -m unittest discover -s tests`: 228 testes, OK, um skip.
- `python3 -m unittest discover -s runtime/tests`: 56 testes, OK.
- `python3 skills/nexus/scripts/hook_engine.py validate`: 26 hooks válidos.
- `git diff --check`: passou.

A primeira tentativa do runtime foi bloqueada pelo sandbox ao abrir sockets
loopback; a repetição com permissão adequada passou. A suíte do projeto em Python
3.14 emitiu ResourceWarnings de conexões SQLite não fechadas; sem falhas. O skip é
`NativeHostUpdatesTests.test_remote_branch_update_replaces_both_installed_packages`,
lifecycle nativo opt-in (`NEXUS_HOST_UPDATES`), não executado nesta avaliação.

## Revisão independente

Um revisor em contexto separado examinou o diff completo contra `d068655`,
incluindo arquivos novos, e aprovou sem achados acionáveis. Conferiu autoridade,
isolamento, evidência, recuperação, DEEP e compatibilidade dos links anteriores;
executou novamente os 23 testes do validador, validação estrutural e diff check.
Não repetiu suítes gerais/runtime nem inferência autenticada entre hosts.

## Próxima medição

Comparar controle e candidata da mesma revisão, uma mudança por ablação: status,
seções endereçáveis, FAST, agrupamento de leituras e Git indisponível. Registrar
input total/cache/fora de cache/output, bytes, seções, releituras e latência por
cenário. Manter gates e oráculos de contrato/falha; não somar cache ao input.
Reservar casos fora da otimização (estado concorrente, configuração alterada,
confirmação tardia, budget agregado, refatoração mecânica versus efeitos e contratos
incompletos), congelados antes dos ajustes. Poucas repetições não provam equivalência.
