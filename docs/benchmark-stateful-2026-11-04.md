# Benchmark com código e estado persistido — 3–4/11/2026

NEXUS e baseline aprovaram **8/8 entregas funcionais**, com a mesma descoberta observada de requisitos, perguntas materiais e continuidade. NEXUS consumiu **3.626.395 tokens**, contra **1.762.824** da baseline: **105,7% a mais**. A soma da latência dos processos foi **38,8% maior**. Não foi observado ganho de qualidade que compense esse custo neste protocolo.

Foram concluídas **32 entregas, 48 processos reais, quatro condições e duas repetições por cenário**, sequenciais, com contexto e recursos de fixture separados. O aceite funcional após adjudicação foi 8/8 para as quatro condições. Os gates brutos foram baseline 8/8, NEXUS 7/8, Superpowers 6/8 e Matt 6/8; as cinco reprovações foram falsos positivos do mesmo oracle, preservados e explicados abaixo. Há ainda um desvio literal de workspace em uma execução do NEXUS, sem consumo de fonte externa; ele é informado separadamente.

[Recibos e métricas completos](../evals/results/stateful-four-arm-v2-2026-11-04.json) · [Bundle reproduzível](../evals/results/stateful-four-arm-v2-2026-11-04.tar.gz) · [Estudo anterior](benchmark-2026-11-03.md)

**Resultado agregado.** Cada condição tem oito entregas e 12 processos. Cache já está em input; total = input + output. Custo por aceite inclui todas as tentativas, inclusive as cinco rejeições brutas, sem reexecutar os agentes após avaliação.

| Condição | Gate bruto | Aceite funcional | Input | Cache input (subconjunto) | Output | Total tokens | Tokens/aceite funcional | Σ latência CLI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 8/8 | 8/8 | 1.701.801 | 1.446.016 | 61.023 | 1.762.824 | 220.353,0 | 1.425,06 s |
| NEXUS | 7/8 | 8/8 | 3.541.990 | 3.160.576 | 84.405 | 3.626.395 | 453.299,4 | 1.977,81 s |
| Superpowers | 6/8 | 8/8 | 5.471.724 | 4.978.432 | 90.048 | 5.561.772 | 695.221,5 | 2.151,35 s |
| Matt Pocock | 6/8 | 8/8 | 6.487.642 | 6.077.440 | 96.069 | 6.583.711 | 822.963,9 | 2.386,14 s |

O adicional observado do NEXUS foi 1.863.571 tokens e 552,75 s de processos, para zero entregas funcionais adicionais. A mediana global por entrega foi 213,43 s contra 141,52 s (+50,8%). Essa mediana mistura quatro tarefas com números de sessões diferentes; a tabela por cenário é a comparação mais útil. Não são preços, economias financeiras nem estimativas causais.

**Por cenário.** Duas entregas por linha; latência ponta a ponta em segundos, mediana (mínimo–máximo). Tokens são a soma das duas entregas; o intervalo mostra consumo por entrega. Os recibos detalham input/cache/output e cada uma das 48 sessões.

| Cenário | Condição | Bruto → funcional | Tokens totais | Tokens/entrega mín–máx | Latência mediana (mín–máx), s |
| --- | --- | ---: | ---: | ---: | ---: |
| Requisitos incompletos | Baseline | 2/2 → 2/2 | 680.116 | 324.357–355.759 | 311,30 (272,29–350,32) |
| Requisitos incompletos | NEXUS | 2/2 → 2/2 | 1.135.959 | 522.521–613.438 | 366,57 (335,18–397,96) |
| Requisitos incompletos | Superpowers | 2/2 → 2/2 | 1.743.379 | 864.595–878.784 | 382,13 (326,63–437,62) |
| Requisitos incompletos | Matt Pocock | 2/2 → 2/2 | 2.096.386 | 1.041.765–1.054.621 | 455,63 (448,53–462,74) |
| Sincronização offline | Baseline | 2/2 → 2/2 | 308.044 | 141.880–166.164 | 136,87 (123,85–149,90) |
| Sincronização offline | NEXUS | 1/2 → 2/2 | 797.021 | 391.363–405.658 | 201,87 (188,80–214,94) |
| Sincronização offline | Superpowers | 0/2 → 2/2 | 1.339.877 | 617.301–722.576 | 222,24 (196,95–247,54) |
| Sincronização offline | Matt Pocock | 0/2 → 2/2 | 1.769.268 | 838.818–930.450 | 259,89 (236,04–283,75) |
| Migração | Baseline | 2/2 → 2/2 | 243.392 | 108.401–134.991 | 122,90 (120,88–124,93) |
| Migração | NEXUS | 2/2 → 2/2 | 643.242 | 288.413–354.829 | 200,28 (188,64–211,92) |
| Migração | Superpowers | 2/2 → 2/2 | 920.778 | 450.879–469.899 | 200,67 (192,11–209,23) |
| Migração | Matt Pocock | 2/2 → 2/2 | 1.183.230 | 388.245–794.985 | 228,19 (162,84–293,54) |
| Retomada entre sessões | Baseline | 2/2 → 2/2 | 531.272 | 245.199–286.073 | 141,52 (140,55–142,49) |
| Retomada entre sessões | NEXUS | 2/2 → 2/2 | 1.050.173 | 427.384–622.789 | 220,27 (201,89–238,65) |
| Retomada entre sessões | Superpowers | 2/2 → 2/2 | 1.557.738 | 713.728–844.010 | 270,73 (259,22–282,23) |
| Retomada entre sessões | Matt Pocock | 2/2 → 2/2 | 1.534.827 | 763.925–770.902 | 249,44 (246,77–252,10) |

**Etapas da comparação principal.** Valores por sessão: mediana e intervalo em segundos. Tokens somam as duas sessões daquele tipo.

| Etapa | Baseline: s mediana (mín–máx) | NEXUS: s mediana (mín–máx) | Baseline tokens | NEXUS tokens |
| --- | ---: | ---: | ---: | ---: |
| Descoberta antes das respostas | 110,60 (86,81–134,38) | 116,62 (96,76–136,48) | 303.396 | 393.813 |
| Implementação após respostas | 200,68 (185,45–215,92) | 249,92 (238,39–261,45) | 376.720 | 742.146 |
| Sincronização offline | 136,87 (123,84–149,89) | 201,86 (188,79–214,93) | 308.044 | 797.021 |
| Migração | 122,90 (120,87–124,92) | 200,27 (188,62–211,91) | 243.392 | 643.242 |
| Primeira sessão / handoff | 73,75 (71,73–75,77) | 117,66 (102,62–132,69) | 281.930 | 556.503 |
| Novo processo / retomada | 67,74 (66,68–68,79) | 102,58 (99,23–105,93) | 249.342 | 493.670 |

**Qualidade observada.** As fontes de cada cenário foram iguais para todos. Os executores receberam briefing, legado e testes públicos; soluções de referência, rubricas e testes ocultos ficaram fora de seus workspaces.

| Dimensão | Baseline | NEXUS | Superpowers | Matt |
| --- | ---: | ---: | ---: | ---: |
| Descoberta: dimensões com suporte em fonte (5 × 2) | 10/10 | 10/10 | 10/10 | 10/10 |
| Decisões de produto efetivamente perguntadas (2 × 2) | 4/4 | 4/4 | 4/4 | 4/4 |
| Requisitos afirmados sem suporte, na descoberta | 0 | 0 | 0 | 0 |
| Migração: payloads em lotes limitados, review de código | 2/2 | 2/2 | 2/2 | 2/2 |
| Retomada: decisão NDJSON preservada em artefato próprio | 2/2 | 2/2 | 2/2 | 2/2 |
| Retomada: trabalho realmente pendente e concluído na sessão 2 | 2/2 | 2/2 | 2/2 | 2/2 |
| Retomada: validação B observada e um único aceite remoto | 2/2 | 2/2 | 2/2 | 2/2 |

A descoberta foi pontuada antes de fornecer respostas: identidades opacas/tenant, elegibilidade ativa, capacidade por visita única e no-op, preview consultivo/revalidação, e reconhecimento das duas políticas de produto em aberto. Todos receberam depois o mesmo pacote — lote atômico e replay/rejeição de conteúdo divergente — mesmo quando a pergunta já estava coberta. Não houve prêmio por quantidade de perguntas. Implementação após a resposta não foi contada como descoberta.

Offline exercitou estado local e outbox em arquivos, duplicatas, entrega invertida, conflitos por relógio lógico, tombstones, recriação, falha parcial, aceite remoto antes da confirmação local e barreiras de edição/sync. Migração usou SQLite real, duas versões de produtores, falha por trigger, rollback de lote, interrupção depois do commit, reabertura, reparo/retry e preservação dos bytes legados. Os testes verificaram efeitos e recuperação, não apenas schemas ou relatos.

Na retomada, o primeiro processo terminou de verdade. O segundo foi um novo exec efêmero, com outro thread ID, sem prompt, resposta ou transcrição anterior; recebeu apenas workspace e novo pedido. A decisão NDJSON só estava no primeiro pedido e teve de sobreviver por artefatos do executor. O import local não idempotente teve uma aceitação e nenhuma repetição nas oito entregas. A configuração mudou de A para B; quatro retomadas observaram o teste B falhar antes da correção. Nas demais, B já era suportado, mas ainda exigia evidência atual. A mudança não foi apresentada como regressão garantida.

**Adjudicação dos oracles.** O gate congelado exigia `opId` diferente entre tenants. Cinco soluções usaram identidade composta por tenant e `opId`, com deduplicação e arquivos devidamente separados. O contrato público não exigia unicidade global desse campo. Um revisor em contexto novo, sem rótulos/métricas, reproduziu as cinco falhas e executou probes de efeitos, feeds, retry, autoridade e reabertura; concluiu falso positivo, sem defeito funcional demonstrado.

Depois da coleta, uma cópia do teste removeu somente essa comparação de representação. Ela foi aplicada uniformemente às oito soluções offline: 11/11 testes passaram em todas. Oracle original, hash, falhas, segunda reprodução, probes independentes e versão derivada permanecem no bundle. Não houve reparo nem nova execução dos agentes. Os gates brutos 27/32 e o aceite funcional 32/32 são resultados distintos e ambos estão preservados. Não foi observado defeito crítico nos invariantes exercitados; isso não prova ausência de outros defeitos.

O piloto teve duas entregas/quatro processos, fora da matriz. Ele revelou outra asserção indevida: exigir rejeição de ID de visita vazio sem uma regra pública de não vazio. Uma segunda avaliação confirmou o problema; a asserção foi retirada antes do congelamento confirmatório, mantendo oracle e reprovação originais. O piloto corrigido aprovou as duas entregas sem reexecutar os agentes.

**Desvio e sensibilidade de escopo.** NEXUS/offline/amostra 2 escreveu e leu uma cópia de seu próprio fonte em `/tmp/field-notes-sync-before.ts`, fora do workspace. A auditoria identificou origem própria e nenhuma leitura de outra célula ou fonte externa. O resultado funcional foi mantido, sem tratar localização de artefato como defeito de sincronização. O desvio literal permanece explícito: uma contagem estrita de workspace daria NEXUS 7/8, contra 8/8 para os demais; seus tokens por entrega estritamente conforme seriam 518.056,4. A conclusão de ausência de ganho funcional sobre baseline não melhora sob essa leitura. O experimento não atesta isolamento físico do host.

**Custos e falhas intermediárias.** Os executores confirmatórios consumiram 17.534.702 tokens e somaram 7.940,363 s de processos. O piloto consumiu 565.283 tokens em quatro sessões; preflight autenticado, 16.911 tokens (latência não capturada). O julgamento independente consumiu 1.326.782 tokens em 230,589 s, solicitado Sol/high. Preparação das fixtures, controlador, auditorias por subagentes e redação têm consumo não exposto pelo host: desconhecido e separado dos executores. Não foi alegado custo monetário ou custo global completo.

A auditoria independente recontou os 48 streams: um turn.started/completed por processo, 48 contextos únicos, nenhuma falha de turno ou erro fatal de CLI. Houve 48 avisos de feature experimental, 1.093 WARNs de fallback do estado de rollouts e dois avisos de remoção de shell snapshot. Entre 653 comandos shell, 112 retornaram status não zero. Isso inclui TDD vermelho, reproduções e consultas sem resultado; não equivale a 112 defeitos. Comandos compostos também podem terminar com falha de `tsc`/diff depois de testes verdes, ou retornar zero após exibir testes vermelhos. Logs e proxies ficam disponíveis; tempo/tokens exatos de retrabalho não são separáveis dos contadores de turno e já entram no consumo total. Não houve intervenção de resgate nem reparo de solução após avaliação.

**Versão, protocolo e limites.** A árvore compartilhada estava suja na branch `elourenco/nexus-readme-illustration`, HEAD `a027f4e`. Ela foi preservada. A captura inicial local `46bf2267…` foi retida; após o pedido de atualizar do remoto, fetch confirmou e a avaliação usou **exatamente `origin/main` `29ff9ac224ce94571320b1fbb3220e9ba078173c`**, inventário SHA-256 `36f691a7fa141f668fad50eac04c4b4d1b7a80c93ac166b98352f1e8fc4df389`, 70 arquivos. O snapshot anterior `409b0c95` não foi reutilizado. Nenhuma alteração foi feita na skill para favorecer resultados.

Superpowers: `22f0b463e7a5e579904dd6211a520321035526f7`; Matt: `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`. Arquivos preservados conferidos byte a byte contra arquivos públicos endereçados por revisão; omissões de imagens binárias e do alias AGENTS symlink do Matt são documentadas. Entradas gerais explícitas: NEXUS `nexus/SKILL.md`, Superpowers `using-superpowers/SKILL.md`, Matt `engineering/ask-matt/SKILL.md`; baseline sem coleção adicional. Snapshots dos comparadores no bundle são evidência isolada com licenças originais, não código incorporado ao núcleo portátil.

Protocolo SHA-256 `a860530063d2e69097794915c093a2de7bce740000bd9d8a6986d7771068356d`, congelado antes da primeira célula. Verdade, decisões do dono, respostas, critérios, fixtures e oracles estavam identificados; o empacotador de julgamento/relatório foi implementado durante a coleta, sem alterar esses inputs. Ordem de condições rotativa; duas repetições; processos de executor sequenciais. Julgamento por inferência só depois da coleta. Revisão independente e hashes conferiram todas as entradas ao término.

CLI identificado `0.166.0-alpha.5.1`, Bun `1.4.2`. Modelo/esforço solicitados `gpt-6.1-sol/medium`; efetivos não emitidos e mantidos desconhecidos. User config, descoberta externa de skills, plugins, hooks, apps, memórias e multiagente foram desabilitados por flags aceitas; `project_doc_max_bytes=0` foi solicitado e documentos públicos lidos explicitamente. Isso não atesta todo o prompt interno do host. Não foram observadas invocações de inferência aninhada, delegação, serviços externos ou leitura de outras skills/memórias. Autenticação usada no lugar, sem copiar credenciais ou alterar instalações globais.

Latência por entrega inclui CLI/ferramentas e instrumentação/handoff local; criação da fixture e julgamento ficam fora. A latência de cada ferramenta não é emitida separadamente. O host e o serviço eram compartilhados; cache remoto, carga e modelo efetivo não foram controlados. Os deltas são descritivos, não efeitos causais. Leituras e escrita foram isoladas por diretórios/sandbox/protocolo, com a exceção de backup descrita; não houve container ou isolamento físico.

A investigação foi explicitamente solicitada e as fontes curtas continham os contratos inferíveis. Isso mede qualidade da descoberta sob pedido, não propensão espontânea a perguntar nem legado sem documentação. O corpus é sintético, autoral e pequeno; duas repetições não estabelecem equivalência estatística. Rótulos e métricas foram ocultados do julgador, mas estilo e artefatos podem revelar o método: o cegamento é limitado. Contexto independente não atesta modelos ou provedores diferentes. Reabertura de handles/failpoints não prova recuperação de power loss/fsync ou escritores simultâneos no mesmo arquivo. O estudo é de invocação explícita em agente único; instalação nativa, descoberta natural, contexto amortizado e fluxos completos multiagente/DEEP não foram medidos. Gates internos de review indisponível não foram transformados em defeitos funcionais.

**Relação com o estudo anterior.** O [benchmark de 96 execuções](benchmark-2026-11-03.md) encontrou baseline e NEXUS 24/24, sem ganho de aceite, com NEXUS a 2,10× tokens. O novo corpus acrescenta código persistido, falhas reais determinísticas e retomada entre processos, mas continua sem ganho observado nos endpoints funcionais, de descoberta e continuidade: NEXUS ficou a 2,06× tokens e 1,39× a soma de latência. A conclusão anterior não mudou neste recorte. Corpus, fases e configuração diferem; não houve A/B isolando a atualização `409b0c95` → `29ff9ac`, e os dois estudos não foram agregados. Os dados não justificam substituir a baseline por NEXUS por expectativa de qualidade superior nessas tarefas; também não demonstram ausência de benefício em outros contextos.
