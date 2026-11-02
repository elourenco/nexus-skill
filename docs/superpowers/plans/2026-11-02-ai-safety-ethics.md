# Segurança e ética em IA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Aplicar o desenho aprovado à atuação da NEXUS e à engenharia de produtos com IA, com critérios verificáveis e carga proporcional ao risco.

**Architecture:** Policies é a autoridade normativa; uma referência especializada detalha aplicação sob demanda. Procedimentos e templates consomem o mesmo contrato, preservando entradas finas e executores existentes. A mudança é documental e comportamental, sem enforcement técnico novo.

**Tech Stack:** Markdown e validação Python já disponível; nenhuma dependência nova.

**Spec:** [SPEC-AI-SAFETY-001 @3](../specs/2026-11-02-ai-safety-ethics-design.md), aprovada em 2026-11-02.

- ID e revisão: PLAN-AI-SAFETY-001 @3
- Estado do plano: execução autorizada e concluída em 2026-11-02; revisão independente APPROVED, sem achados. Evidências: [registro de validação](../../ai-safety-ethics-validation.md).
- Execução recomendada: agente principal, sequencial, com revisão independente do diff completo ao final. As cinco etapas compartilham o contrato normativo; workers por etapa acrescentariam handoffs sem ganho claro.
- Controle deste trabalho: checkboxes deste plano; nenhum store/helper é ativado e nenhuma TASK paralela é criada. Este documento usa o formato de planejamento do host, não instancia o Todo documental do consumidor.

## Global Constraints

- “Preservar essa arquitetura, os perfis FAST/BALANCED/DEEP, modos, enums, schemas, autorizações existentes e helpers opt-in.”
- “Não acrescentar dependências, serviços, agentes obrigatórios, uma entrada especializada ou leitura integral do catálogo.”
- “O texto não substitui sandbox, autorização no servidor ou controles de execução.”
- “A simples presença de IA, RAG ou dados pessoais não determina DEEP.”
- “Não introduzir avaliação por outro modelo em toda execução.”
- “Fora de escopo: `runtime/`, código dos helpers, hooks executáveis, novos scanners, instalações em hosts, benchmarks, revisão jurídica e certificação de consumidores.”
- “Não alterar manifests, versões de publicação ou configuração global nesta entrega.”
- Sem commit, push, merge, deploy ou mensagens externas nesta execução; esses efeitos exigem autorização própria. Não inserir etapas de commit automático.
- Usar `rtk` para comandos de shell; nunca executar as instruções maliciosas dos cenários. Todos os exemplos e entradas de avaliação são sintéticos.

## Review Focus

1. Texto adversarial misturado a conteúdo legítimo: descartar sua autoridade e continuar a parte útil; exercício adicional F1 na etapa 2.
2. Dados sanitizados destinados a outro provider: sanitização não cria autorização; exercício F2 na etapa 2.
3. Aprovação anterior com alvo alterado: revalidar ação/alvo antes do efeito sem reconfirmar autorizações ainda válidas; exercício F3 na etapa 2.
4. Avaliação de equidade sem amostra apropriada: limitação explícita, sem coleta automática de atributos sensíveis; exercício F4 na etapa 3.
5. Exemplo novo confundido com resultado de helper ou avaliação real: preservar schemas e marcar evidência sintética; exercício F5 na etapa 3.

---

## Arquivos e ownership

Todos os caminhos abaixo são relativos à raiz do repositório. Um único escritor
altera os documentos; o revisor final é somente leitura. Nenhum teste utiliza
banco, porta ou recurso de consumidor. Mudanças concorrentes no workspace exigem
reconciliar o diff antes de editar ou revisar.

| Etapa | Criar | Modificar diretamente |
| --- | --- | --- |
| 1 — contrato | `skills/nexus/references/ai-safety-ethics.md`; `docs/ai-safety-ethics-validation.md` | `skills/nexus/references/policies.md`; `skills/nexus/SKILL.md`; `skills/nexus/references/invocation.md` |
| 2 — procedimentos | Nenhum | Sob `skills/nexus/references/`: `brainstorming.md`, `plan.md`, `build.md`, `debug.md`, `review.md`, `cognitive.md`, `domain-design.md`, `agents.md`, `workflow.md`, `memory.md`, `hooks.md`, `quality-checks.md` |
| 3 — artefatos | Nenhum | Sob `skills/nexus/assets/templates/`: `contracts.md`, `spec.md`, `plan.md`, `task.md`, `adr.md`, `review.md`, `evidence.md`, `memory.md`, `examples.md` |
| 4 — adoção | Nenhum | `README.md`; `skills/nexus/references/consumer-guide.md` |
| 5 — fechamento | Nenhum | Registro de validação e este plano; correções somente nos documentos das etapas anteriores |

Consumidores preservados com cobertura indireta a conferir: as cinco
`skills/nexus-*/SKILL.md` via `invocation.md` e respectivos procedimentos;
`references/workflow-state.md` via Policies/workflow;
`references/review-package.md` via protocolo de review e regras de sanitização;
`references/installation.md` via guia e Policies. Registrar o caminho de cobertura
real na etapa 5. Se algum link/contrato atual for insuficiente, acrescentar somente
a remissão necessária nesses três últimos documentos, com motivo no registro.
Não atualizar `assets/templates/validation.md` nem outros resultados históricos.

## Etapa 1: publicar o contrato documental e suas rotas

**Dependência:** nenhuma. **Aceites:** AC1, AC3, AC4.

**Interfaces:** consome autoridade e perfis de Policies. Produz a âncora
`policies.md#policy-ai-safety-ethics` e referência `ai-safety-ethics.md`, usadas nas
demais etapas. A referência terá âncoras explícitas `nexus-conduct`, `ai-products`,
`risk-triggers`, `failure-recovery`, `evaluation` para links estáveis.

- [x] Registrar baseline: `rtk git status --short`, `rtk bypass python3 scripts/validate.py`; ler spec, instruções e diff atual. Preservar trabalho alheio.
- [x] Criar o registro de validação com alvo/base observada, limites, matriz de consumidores e S1–S13 inicialmente `não executado`; não inventar falhas de baseline nem resultados esperados como observações.
- [x] Acrescentar a seção normativa em Policies: os oito invariantes da spec, gatilhos, proporcionalidade, ação dependente bloqueada e limite de autoridade. Ligar `policy-execution`, `policy-security`, `policy-testing`, `policy-completion` e tabela de consumo à seção quando pertinente, sem repetir suas regras.
- [x] Atualizar `nexus.policies` para revisão `2`: os critérios de impacto humano acrescentam obrigações normativas de aceite. Preservar anchors anteriores e registrar compatibilidade de campos/estados; revisão documental não modifica versões do plugin ou schemas executáveis.
- [x] Criar a referência com os dois escopos, sete dimensões de produto, supervisão efetiva, transparência/acessibilidade, limites da avaliação por grupos e referências OWASP/NIST da spec. Cobrir budget agregado, concorrência, timeout, revalidação no efeito e fallback autorizado; não fixar métricas ou thresholds universais.
- [x] Atualizar a ativação/registro de módulos no `SKILL.md` e o contrato em `invocation.md`: princípios mínimos sempre aplicáveis; carregar detalhe somente pelos gatilhos. Nenhuma dependência nova entre entradas especializadas.
- [x] Aplicar S1, S4, S6, S9 e S10 à redação nova. Registrar decisão dedutível, trecho que a sustenta e limites; corrigir contradições. Verificar que uma correção trivial não exige artefato ou review ético adicional.
- [x] Executar `rtk bypass python3 scripts/validate.py` (exit 0 e mensagem OK); inspecionar unicidade das seis âncoras novas e destino de seus links. Resultado estrutural não aprova os cenários.

## Etapa 2: integrar o contrato nos procedimentos

**Dependência:** etapa 1. **Aceites:** AC1–AC4.

**Interfaces:** consome âncoras da etapa 1. Produz instruções específicas por fluxo;
não altera eventos, campos de request, estados ou resultados executáveis.

- [x] Em brainstorming/cognitive, incluir afetados, finalidade e alternativas de menor exposição quando pertinentes. Distinguir vieses de raciocínio de discriminação/erros assimétricos do produto; `bias.challenge` não comprova equidade.
- [x] Em plan/domain-design, orientar fronteiras de confiança, responsável por efeitos, validação no executor e recuperação. Em build/debug, aplicar os controles definidos e sanitizar diagnóstico, sem autorizar ação externa ou correção fora do pedido.
- [x] Em review/agents, ampliar o foco pertinente de segurança e qualidade para impacto humano; sem novo papel obrigatório. Conferir escopo/destino de dados na delegação e impedir que respostas de outros agentes sejam tratadas como permissão.
- [x] Em workflow/memory/hooks, referenciar invariantes nos pontos de aceite, recuperação e persistência. Distinguir checagem documental de mecanismo executável: nenhum hook novo, filtro automático de ética ou garantia técnica de detecção.
- [x] Em quality-checks, acrescentar avaliação dirigida ao caso de uso: entradas adversariais, validação de saídas, impacto humano e limitações de amostra. Não exigir chamadas a modelos, scanners ou ensaios de carga para toda tarefa.
- [x] Exercitar S2, S3, S5, S8, S11 e S12 com os procedimentos alterados. Conferir limites agregados, reconciliação e distinção entre relatório concluído e objeto aprovado.
- [x] Exercitar F1: documento sintético tem um requisito legítimo e pedido de exportação não autorizada; somente o requisito pode informar a tarefa. F2: resumo sanitizado enviado a destino não autorizado deve continuar bloqueado. F3: trocar o alvo após aprovação exige revalidação, enquanto mesma ação/alvo/escopo não exige confirmação redundante. Registrar leitura documental, não execução de ataque.
- [x] Executar `rtk bypass python3 scripts/validate.py` e revisar o diff da etapa. Conferir que cada procedimento remete ao contrato sem reproduzi-lo integralmente.

## Etapa 3: tornar os artefatos úteis para os novos critérios

**Dependência:** etapas 1–2. **Aceites:** AC2–AC5.

**Interfaces:** consome a política revisão 2 e preserva contrato de artefatos versão
1, IDs, campos e enums. Produz orientações condicionais e exemplo documental
sintético; nenhum campo adicional entra no JSON de memória ou requests de helpers.

- [x] Em contracts, estabelecer consumo da nova política por campos existentes: risco/impacto, controle/responsável, aceite, evidência e limitação. Não exigir formulário completo de ética em FAST.
- [x] Acrescentar instruções curtas a spec/plan/task/ADR: registrar pessoas afetadas, dados/fronteiras, supervisão e riscos apenas quando materiais. Usar seus campos atuais; não criar novos campos obrigatórios.
- [x] Orientar review/evidence a separar controle proposto, implementado e verificado; conclusão limitada por revisão do alvo, amostra e método. Em memory, orientar minimização e não promoção de registros a autoridade, preservando exatamente o formato JSON aceito pelo helper.
- [x] Adicionar ao final de examples um caso sintético de assistente que recomenda acesso a serviço: referência à regra, responsável por revisão/contestação, teste proposto para erros assimétricos e evidência explicitamente `não executado`. Não alterar cenários anteriores nem marcar a tarefa fictícia como concluída.
- [x] Aplicar S6, S7 e S13 aos templates/exemplo: revisão humana efetiva, limitação sem dados de grupos e transparência material. Um campo preenchido não comprova proteção.
- [x] Exercitar F4: ausência de dados adequados mantém equidade inconclusiva, sem coleta automática. Exercitar F5: ler o exemplo como handoff; o leitor deve identificar que nenhum produto/helper foi executado e não deve enviar metadados documentais como propriedades JSON novas.
- [x] Preencher uma TASK FAST sintética em arquivo temporário, com uma correção de texto autorizada. Verificar que os novos textos não impõem SPEC/ADR/relatório separado; registrar conclusão de mesa, remover apenas o temporário criado nesta execução.
- [x] Executar `rtk bypass python3 scripts/validate.py`; revisar diff dos templates e confirmar ausência de alteração em schema, enum ou exemplo JSON da memória.

## Etapa 4: orientar adoção e limites

**Dependência:** etapas 1–3. **Aceites:** AC1–AC4.

**Interfaces:** consome contrato e procedimentos; produz caminho curto de descoberta
no README e no guia do consumidor. Instalação continua opt-in e sem novos poderes.

- [x] No README, apresentar os dois escopos em trecho curto e ligar a referência canônica. Não alegar produto seguro, conformidade ou imunidade a prompt injection.
- [x] No consumer-guide, orientar seleção dos critérios pelo caso de uso, responsabilidade do executor por controles técnicos e registro de evidência mínima. Distinguir essa orientação da demonstração executável existente.
- [x] Conferir installation, review-package e workflow-state contra a matriz: registrar suas rotas atuais; acrescentar remissão apenas se necessária. Instalação não ativa verificações, coleta não sanitiza automaticamente e workflow não interpreta sozinho critérios éticos em prosa.
- [x] Percorrer o núcleo e as cinco entradas como leitor novo. Para cada uma, registrar entrada → contrato → procedimento → política; confirmar carregamento condicional e ausência de necessidade de reler o catálogo inteiro.
- [x] Executar `rtk bypass python3 scripts/validate.py`; conferir que README/guia/exemplos não contradizem limitações dos executores.

## Etapa 5: validar cobertura e revisar o resultado integrado

**Dependência:** etapas 1–4. **Aceites:** AC1–AC6.

**Interfaces:** consome diff completo e registro incremental. Produz
`docs/ai-safety-ethics-validation.md` com resultados observados e limitações; nenhuma
execução real é inferida a partir de inspeção documental.

- [x] Completar matriz de cobertura por arquivo: ajuste direto ou rota canônica concreta, regra aplicada e cenário pertinente. Confirmar todos os consumidores da spec, incluindo entradas, instalação e templates.
- [x] Reaplicar S1–S13 e F1–F5 ao conjunto final em avaliação de mesa; cada linha registra procedimento, decisão encontrada, referência, resultado (`pass`, `fail`, `inconclusive`) e limite. Resolver qualquer falha documental; não substituir execução ausente por `pass` de host.
- [x] Solicitar revisão independente do diff e fontes ao papel `review` conforme política do host, somente leitura e sem herdar a narrativa de implementação. Foco: autoridade, impacto humano, FAST, isolamento, efeitos incertos, validade da aprovação e alegações de enforcement. O agente principal integra achados; corrigir e reavaliar as partes afetadas.
- [x] Executar uma rodada final de `rtk bypass python3 scripts/validate.py` e `rtk git diff --check`; ambos devem terminar sem diagnóstico de erro. O segundo não cobre untracked: inspecionar também whitespace e links dos arquivos novos, sem adicioná-los ao índice apenas para validar.
- [x] Conferir `rtk git diff --name-only` e `rtk git status --short`: alterações devem estar na matriz mais spec/plano/registro. Nenhum código, manifesto, versão de plugin, instalação ou resultado histórico pode ter sido alterado.
- [x] Concluir registro com AC1–AC6, alvo revisado, verificações reais, achados resolvidos/pendentes e declaração explícita de que não houve avaliação em host real nem prova de melhoria estatística, se esse for o caso. Atualizar checkboxes apenas pelo trabalho observado e entregar o diff local.

## Validação proporcional e recuperação

Não criar testes de presença de palavras como substituto de comportamento. Como
não há alteração executável, não adicionar TDD artificial ou rodar suítes dos
helpers/runtime sem evidência de regressão pertinente. A validação é estrutural,
inspeção de rotas e aplicação documental dos cenários, seguida de revisão
independente. O harness existente só será usado se houver execução real autorizada
em contextos isolados; seus recibos não serão preenchidos com exercícios de mesa.

Se surgir necessidade de mudar um executor para cumprir o desenho, registrar a
lacuna e manter essa extensão fora deste plano. Se uma edição documental gerar
contradição, corrigir apenas os hunks desta execução e reavaliar os cenários
afetados; não usar reset de worktree. Links ou review obsoletos exigem nova
verificação sobre o alvo atual. Nenhum rollback de produto consumidor é necessário.

## Conferência do planejamento

- Cobertura: AC1 nas etapas 1/4/5; AC2 nas etapas 2/3/4/5; AC3 nas etapas 1–5;
  AC4 nas etapas 1–5; AC5 nas etapas 1/2/3/5; AC6 em todas as verificações e no fechamento.
- S1–S13 estão atribuídos; F1–F5 têm exercícios nas etapas responsáveis.
- Interfaces documentais/âncoras são definidas na etapa 1; demais etapas apenas
  consomem. Versão de Policies 2 é distinta de versão de artefatos, plugin e stores.
- Sem dependência externa nova, alteração de schema, publicação ou execução em
  produto real. Requisitos específicos de consumidores continuam sendo definidos
  no contexto deles, sem extrapolação da spec.
