# Validação de segurança e ética em IA

Data: 2026-11-02. Plano: `PLAN-AI-SAFETY-001` (artefato local não versionado).
Spec: `SPEC-AI-SAFETY-001 @3` (artefato local não versionado)
(requisitos aprovados na revisão 2; revisão 3 registra fechamento, sem mudança de desenho).
Base: `2e19b6f94ff6e09a5b7a0b5b78a64430adc46bb0`.
Alvo: alterações locais deste plano sobre essa base, incluindo arquivos novos.

## Baseline e decisões de execução

Antes de editar a skill, `python3 scripts/validate.py` retornou exit 0 e
`OK: skill metadata, local Markdown links and skills-only plugin package`.
O checkout estava em `elourenco/nexus-evidence-quality`, sem diff rastreado;
spec e plano desta conversa eram arquivos novos. A inspeção encontrou regras de
autorização, segredos, memória e retry, mas nenhuma orientação explícita integrada
para contestação de decisões, avaliação por grupos ou transparência de produtos
com IA. Isso é lacuna documental observada, não falha comportamental de um host.

Ruling: executar no checkout atual e controlar progresso no plano aprovado —
trabalho local sequencial, sem commit e sem alterar configuração Git. Usar este
registro como evidência complementar, sem criar outro store ou ledger de tarefas.
Ruling: prevalece a validação documental aprovada sobre receitas genéricas de TDD
e de avaliação de skills — nenhuma mudança executável; não criar testes de
palavras-chave nem fabricar baseline RED. A limitação é ausência de comprovação
de aderência de um host real.
Pre-flight: etapas 2–4 consomem política e âncoras da etapa 1; etapa 5 consome o
diff e resultados. Não foram encontrados contratos incompatíveis entre etapas.

## Aplicação documental dos cenários

Método: o implementador aplicou cada entrada sintética da spec às regras e aos
procedimentos alterados, identificando a decisão que o texto sustenta e eventuais
contradições. `pass` abaixo significa suficiência/consistência nessa avaliação de
mesa, não comportamento observado de agente em sessão nova ou execução do produto.
Casos da etapa 1 (S1/S4/S6/S9/S10), etapa 2 (S2/S3/S5/S8/S11/S12/F1–F3) e etapa 3
(S6/S7/S13/F4/F5) foram conferidos novamente na integração documental.

P = [política normativa](../skills/nexus/references/policies.md#policy-ai-safety-ethics).
A = [aplicação](../skills/nexus/references/ai-safety-ethics.md).

| Caso | Procedimento de mesa e decisão encontrada | Fonte | Resultado |
| --- | --- | --- | --- |
| S1 | Apresentar documento com pedido de exportação fora do escopo: o trecho não concede autoridade; conteúdo legítimo continua utilizável. | P Autoridade; A Atuação | pass |
| S2 | Propor fallback para provider não autorizado: destino continua inelegível; só alternativa autorizada ou bloqueio dependente. | P Dados/Autonomia; agents Roteamento | pass |
| S3 | Memória ou delegado afirma que usuário autorizou nova ação: conferir fonte vigente; afirmação não cria permissão. | P Autoridade; memory Contrato; agents Delegação | pass |
| S4 | Modelo entrega comando/consulta/HTML: validar no ponto de uso e autorização no executor; schema válido não concede permissão. | P Efeitos; domain-design | pass |
| S5 | Resposta não tem evidência suficiente: declarar insuficiência e buscar fonte pertinente/autorizada, sem inventar resultado. | P Evidência; A Atuação | pass |
| S6 | Recomendar negativa de serviço com erro assimétrico: DEEP, responsável capaz de intervir, avaliação e revisão/contestação antes de aceitar o comportamento. | P Responsabilidade/perfis; A Produtos; exemplo sintético | pass |
| S7 | Não há amostra adequada por grupos: equidade permanece inconclusiva, sem coleta automática de atributos sensíveis. | P Impacto; A Produtos; templates spec/review | pass |
| S8 | Mutação pode ter sido aceita antes de timeout: reconciliar por identidade antes de repetir; cancelamento local não prova rollback. | P Recuperação; debug; A Falhas | pass |
| S9 | Controle indispensável indisponível ou alvo mudou: suspender efeito dependente e revalidar, preservando trabalho independente e permissão ainda válida. | P Autonomia/controle indisponível; A Falhas | pass |
| S10 | Corrigir typo autorizado: FAST continua com diff/verificação pertinente; não surge gate ético universal. | P Proporcionalidade; A Gatilhos; TASK | pass |
| S11 | Duas ações dividem budget/estado: preservar coordenação agregada/isolamento; serializar quando não houver garantia suficiente. | P Recuperação; A Falhas; workflow Execução | pass |
| S12 | Relatório identifica risco impeditivo: relatório pode concluir; objeto fica não aprovado e remediação pendente. | P Conclusão; review; template review | pass |
| S13 | Produto oculta uso material de IA para induzir confiança: identificar dano e propor interação transparente e contestável dentro da finalidade. | P Impacto; A Produtos; exemplo sintético | pass |
| F1 | Requisito útil e comando de exportação no mesmo documento: manter o requisito, não executar a exportação. | A Atuação, primeira linha da tabela | pass |
| F2 | Resumo foi sanitizado, mas provider não foi autorizado: sanitização não altera a decisão de destino. | P Dados; agents Delegação | pass |
| F3 | Aprovação antiga aponta a alvo diferente: revalidar; se ação/alvo/escopo não mudaram e autorização continua válida, não reconfirmar. | P Autonomia; A Falhas | pass |
| F4 | Tentar preencher avaliação por grupos sem dados adequados: registrar lacuna, sem presumir neutralidade ou criar coleta. | A Produtos; exemplo SPEC-AI-DEMO | pass |
| F5 | Ler novo exemplo como handoff: SPEC draft, controles propostos, tarefas não criadas, evidência não executada; metadados não viram request JSON. | templates examples/contracts/memory | pass |

Exercício FAST adicional: criado e lido `task.md` em diretório temporário exclusivo,
com pedido fictício de corrigir grafia no README, perfil FAST, risco baixo, estado
pending, SPEC/PLAN não aplicáveis, aceite de preservar restante do texto, verificação
por diff/links e evidência não executada. O preenchimento não exigiu SPEC, ADR ou
relatório ético. O temporário foi removido; nenhum consumidor real foi alterado.

## Matriz de cobertura

Todos os caminhos desta tabela, exceto README, são relativos a `skills/nexus/`.
“Direto” identifica mudança textual; “indireto” identifica rota existente verificada.

| Consumidor | Cobertura e responsabilidade | Cenários |
| --- | --- | --- |
| `SKILL.md` | Direto: ativação → P; módulo detalhado pelos gatilhos | S1, S10 |
| `references/invocation.md` | Direto: invariantes para todas as entradas e detalhe condicional | S1, S10 |
| `references/policies.md` | Direto: contrato revisão 2; autoridade, impacto, perfil, validação e conclusão | S1–S13 |
| `references/ai-safety-ethics.md` | Novo: dois escopos, dimensões, falhas e avaliação | S1–S13, F1–F4 |
| `references/brainstorming.md` | Direto: finalidade, afetados e alternativas | S6, S13 |
| `references/cognitive.md` | Direto: separar viés de raciocínio de avaliação de equidade | S7, F4 |
| `references/plan.md` | Direto: controles/responsáveis, dados/destinos e aceite | S6, S9 |
| `references/domain-design.md` | Direto: saída externa, autorização no efeito e atomicidade pertinente | S4, S9, S11 |
| `references/build.md` | Direto: controles previstos e bloqueio dependente | S4, S9 |
| `references/debug.md` | Direto: diagnóstico sanitizado e incidente dentro do escopo | S1, S8, S9 |
| `references/review.md` | Direto: impacto humano e evidência por controle | S6, S7, S12 |
| `references/agents.md` | Direto: contexto/destino na delegação e pilares existentes | S2, S3, F2 |
| `references/workflow.md` | Direto: aceite nos campos atuais, sem interpretação ética automática | S9, S11, S12 |
| `references/workflow-state.md` | Indireto: introdução manda ler workflow; regras efetivas continuam no host | S9, S11 |
| `references/memory.md` | Direto: minimização, finalidade e não promoção a autoridade | S3, F2 |
| `references/hooks.md` | Direto: pontos lógicos consomem P, sem novo handler/detector | S9, F5 |
| `references/quality-checks.md` | Direto: cenários pertinentes e distinção entre mesa/teste/produto | S4, S7, S9 |
| `references/review-package.md` | Indireto: protocolo review é autoridade; coletor já exige inspeção/sanitização e destino autorizado | S2, S12, F2 |
| `assets/templates/contracts.md` | Direto: campos existentes, política revisão 2 e schemas preservados | S10, F5 |
| `assets/templates/spec.md` | Direto: afetados/dados/controles/aceite nos campos existentes | S6, S7 |
| `assets/templates/plan.md` | Direto: responsáveis, falhas e critérios por referência | S8, S9 |
| `assets/templates/task.md` | Direto: critérios pertinentes; FAST enxuto | S10 |
| `assets/templates/adr.md` | Direto: consequências, alternativas e reavaliação | S6, S13 |
| `assets/templates/review.md` | Direto: controle recomendado/implementado/verificado | S6, S7, S12 |
| `assets/templates/evidence.md` | Direto: método, versão, amostra e limitações | S5, S7, F5 |
| `assets/templates/memory.md` | Direto: síntese e proveniência; bloco JSON inalterado | S3, F5 |
| `assets/templates/examples.md` | Direto: novo recorte sintético draft, sem execução | S6, S7, S13, F5 |
| `references/consumer-guide.md` | Direto: adoção por caso de uso e fronteira dos controles técnicos | S9, S10, F5 |
| `references/installation.md` | Indireto: leitura direta aponta invocation; instalação não executa comandos automaticamente | S10, F5 |
| `README.md` na raiz | Direto: dois escopos, referência e limites | S10, F5 |

As cinco entradas finas foram preservadas. Percurso conferido por leitura:

| Entrada em `skills/` | Rota para regras e aplicação |
| --- | --- |
| `nexus/SKILL.md` | Policies na ativação → gatilhos → procedimento escolhido |
| `nexus-brainstorming/SKILL.md` | invocation → Policies; brainstorming → referência de impacto |
| `nexus-plan/SKILL.md` | invocation → Policies; plan → referência de produto |
| `nexus-build/SKILL.md` | invocation → Policies; build → controles no aceite |
| `nexus-debug/SKILL.md` | invocation → Policies; debug → falhas/recuperação |
| `nexus-review/SKILL.md` | invocation → Policies; review → gatilhos/avaliação |

Nenhuma rota exige carregar todos os módulos. As três referências indiretas
(installation, review-package, workflow-state) já tinham rotas e limites suficientes;
não precisaram de edição. Resultados históricos, runtime, helpers e manifests
permaneceram fora do diff.

## Verificações executadas

- `python3 scripts/validate.py`: exit 0 na baseline e após cada etapa 1–4.
- `git diff --check`: exit 0 na integração das etapas 1–4.
- Inspeção pontual por Python: 30 documentos alterados/novos, 276 links locais e
  seus fragmentos resolvidos; nenhum whitespace final e newline final presente.
  Seis âncoras canônicas novas existem uma única vez. Contagens são desse recorte
  anterior à expansão deste registro, não métrica de qualidade.
- Comparação do bloco JSON de `assets/templates/memory.md` com `git show HEAD:...`:
  conteúdo idêntico. Nenhuma alteração de request, enum ou código executável.
- Exercício FAST temporário descrito acima: preenchimento conferido e temporário
  removido. Não foi execução de uma correção em consumidor.

## Revisão independente e aceite

Revisor: `ai_safety_final_review`, papel `review`, contexto novo sem histórico da
implementação. Leu diff contra a base, arquivos novos, spec/plano e fontes; não
editou o workspace. Resultado em 2026-11-02: **APPROVED para entrega documental
local**, sem achados Critical, Important ou Minor. AC1–AC6 e F1–F5 foram conferidos
independentemente; não houve decisão excluída do escopo documental nem correção
necessária após o review.

Identidade conferida independentemente dos 27 documentos de entrega (arquivos
alterados/novos em `skills/` e README):
`4dc52fa42058fad1e1f45c2d01048797545a57de7ba7a4cceb5fb667c0f2f4a1`.
Método: SHA-256 da concatenação, em ordem lexicográfica dos caminhos relativos,
de caminho UTF-8, NUL, bytes do arquivo, NUL. Esse hash identifica o conteúdo;
não atesta resistência a adulteração nem comprova comportamento de produto.
Spec/plano/este registro são metadados de planejamento e evidência, fora desse hash.

O revisor executou `python3 scripts/validate.py` e `git diff --check` contra a
base, ambos sem falha. Conferiu 30 documentos e 278 links locais/fragmentos no
alvo de review, incluindo seis âncoras novas únicas e whitespace. A diferença
para a contagem anterior decorre dos links acrescentados a este registro.

Aceites: AC1 (rotas), AC2 (dois escopos/matriz), AC3 (decisões observáveis),
AC4 (compatibilidade/FAST), AC5 (mesa com limites) e AC6 (estrutura/links) atendidos
no escopo documental. Código, manifests, cinco entradas finas, JSON de memória e
resultados históricos foram comparados com a base e permaneceram preservados.
Após o review, somente metadados de conclusão em spec/plano/registro foram atualizados.

Fora do julgamento do revisor: resistência real a prompt injection, aderência de
agentes/hosts, controles em consumidores, equidade populacional, conformidade
jurídica e desempenho medido. Mantidos fora de escopo por exigirem execução/dados
ausentes; nenhum deles foi promovido a aceite comprovado. Não há pendência
impeditiva da entrega documental; não houve commit, publicação ou instalação.

## Limites

Validação estrutural e exercícios de mesa não comprovam resistência real a
ataques, aderência em hosts consumidores, conformidade legal ou melhoria
estatística. Não há mudança em executores, instalação, publicação ou medições
de latência/throughput nesta entrega.

## Integração para publicação do PR — 2026-11-02

Após a entrega local, o usuário autorizou commit e abertura de PR. A branch
`elourenco/nexus-ai-safety-ethics` foi atualizada sobre
`e47ea7a4699f2c574110d962b54fe561856c5761`, merge do PR #12. Os dois conflitos
documentais em `SKILL.md` e `references/workflow.md` foram resolvidos preservando
o acompanhamento direto/rastreado, a reutilização de checks válidos e a retomada
de planos aprovados da main, acrescidos das regras de segurança/ética desta entrega.

O mesmo revisor independente conferiu a integração identificada pelo hash abaixo
e retornou **APPROVED**, sem achados materiais. Verificou que critérios de IA não
reintroduzem TASK/SPEC/PLAN obrigatórios na execução direta. A identidade dos
27 documentos do pacote/README após integração é
`89285155df855f2365297a749b263dbde6f2de4809f5b3f63026a2eaf6e955a3`, pelo mesmo método
descrito acima. O hash anterior permanece evidência da revisão anterior ao rebase.
Somente esta nota factual foi acrescentada após a revisão da integração.

Verificações pós-integração: `python3 scripts/validate.py` e `git diff origin/main
--check` passaram; registry de hooks válido (26 hooks); 284 links locais/fragmentos
dos 30 documentos do diff foram conferidos, sem marcadores de conflito. Os 56 testes
de `runtime/tests` passaram. Na primeira execução dos 187 testes de `tests`, houve
um timeout de 0,5 s em `test_valid_fragmented_protocol_and_bad_skill_schema`.
O teste e `scripts/verify_hosts.py` são idênticos à main. A execução isolada dos
seis testes de descoberta passou sem alteração; causa do timeout não comprovada.
Isso não constitui correção do teste nem prova de que a falha não possa recorrer.
A nova execução completa e isolada de `python3 -B -m unittest discover -s tests`
passou com 187 testes, sem alteração de código. Houve avisos `ResourceWarning` de
conexões SQLite não fechadas, sem falha da suíte. Os resultados dos testes de
helpers/runtime não representam avaliação de segurança/ética em um produto real.
