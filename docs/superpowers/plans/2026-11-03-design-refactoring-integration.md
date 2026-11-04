# Integração de design e refatoração no NEXUS

> **For agentic workers:** Use superpowers:executing-plans para execução contínua;
> cenários e review podem ser delegados com ownership isolado. A autorização de
> implementação já foi dada pelo usuário; não repetir o aceite.

**Goal:** Incorporar software-design-principles, codebase-design, senior-architect,
architecture-patterns e padrões de refatoração ao pacote portátil do NEXUS.

**Architecture:** Consolidar princípios em domain-design.md e policies.md; criar
architecture-design.md e refactoring.md, consultados por gatilho nas etapas atuais.
Registrar proveniência separadamente, sem dependência de skills externas.

**Tech Stack:** Markdown e cenários JSON no harness Python existente; sem dependências.

**Spec:** Proposta aprovada nesta conversa: síntese contextual das quatro skills,
uma referência arquitetural com diagnóstico/módulos/sistemas e uma de refatoração
segura; autorizações, fronteiras do runtime e alterações existentes preservadas.

## Global Constraints

- Fonte de verdade em skills/nexus/; núcleo curto, referências sob demanda.
- Sem alteração de runtime, helpers, instalação global, manifests ou modelos.
- A implementação inicial não incluiu commit ou publicação. Posteriormente, o
  usuário autorizou commit e PR somente desta integração; merge permanece fora
  do escopo.
- Sem impor camadas, bibliotecas, artefatos, relatórios HTML ou novos aceites.
- Evidências de cenário são avaliação de respostas; não são testes de produção.
- Trabalhar sobre o conteúdo atual, com snapshot anterior para comparação e review.

## Review Focus

- Entrada especializada deve alcançar as referências sem depender do roteador principal.
- Refatoração local simples deve preservar o caminho curto e decisões aprovadas.
- Interfaces pequenas devem conservar erros, cancelamento, efeitos e custos observáveis.
- Troca de await sequencial, transação ou storage exige verificar semântica concorrente.
- Adoção de padrões depende de drivers; nomes de diretórios e contagens não comprovam arquitetura.

## Task 1 — Cenários e baseline

**Files:** evals/design-refactoring-suite.json; snapshot temporário das skills atuais.
**Interface:** schema_version 1 aceito por scripts.evaluate.validate_suite; prompts
sem respostas/rubricas para o executor; saídas com leituras e decisões observadas.

- [x] Congelar pacote e arquivos preexistentes; validar estrutura da base.
- [x] Criar cenários sintéticos e rubricas antes de alterar instruções.
- [x] Executar baseline em contexto novo e registrar falhas ou capacidades já presentes.

## Task 2 — Conteúdo e roteamento

**Files:** skills/nexus/references/{architecture-design,refactoring,design-sources}.md;
domain-design.md, policies.md, brainstorming.md, plan.md, build.md, review.md;
skills/nexus/SKILL.md; README.md.
**Interface:** referências locais condicionais; contratos e estados existentes intactos.

- [x] Incorporar contratos de módulos, escolha arquitetural e padrões condicionais.
- [x] Consolidar princípios contextuais e transformações de refatoração verificáveis.
- [x] Conectar modos diretamente, sem recarregar decisões ou impor leitura a tarefas mecânicas.
- [x] Registrar fontes e adaptações; documentar descoberta no README.

## Task 3 — Aplicação, revisão e evidências

**Files:** docs/design-refactoring-validation.md;
evals/results/design-refactoring-2026-11-03.json.
**Interface:** recibo com prompts, respostas, hashes, rubricas e limites observados.

- [x] Executar os mesmos cenários com candidata em contexto novo; conferir cada saída.
- [x] Revisar diff e contratos independentemente e corrigir achados materiais.
- [x] Executar python3 scripts/validate.py e testes pertinentes de pacote/avaliação.
- [x] Conferir diff --check, arquivos preservados e hashes do pacote avaliado.
- [x] Registrar resultados reais, limites e tamanho textual sem inferir economia de tokens.

## Decisões de execução

A integração é documental; o agente principal mantém as referências e roteamento.
Um agente de testes possui somente a suíte sintética. Baseline, candidata e review
usam contextos separados. Os testes não executam efeitos externos dos cenários.
O snapshot inclui mudanças locais anteriores: comparar apenas contra HEAD atribuiria
trabalho alheio a esta entrega. Não há necessidade de modificar o harness existente.

Baseline: os nove cenários atendidos; lacunas de recuperação explícita para design
de interfaces e catálogo de refatoração. A avaliação não demonstrou falha funcional
da base, portanto a integração não é apresentada como correção de uma falha observada.
Os executores anteriores/candidatos usam snapshots isolados, mesmo durante edições
no workspace. Manifests de plugins receberam alteração concorrente fora desta
entrega e foram excluídos do patch de review.

Conclusão: 219 testes do projeto passaram; 26 hooks e estrutura válidos. Review
independente sem achados materiais; 30/30 rubricas em cada versão (nove cenários
por versão, contexto compartilhado no lote). A candidata tornou a orientação
explícita sem regressão observada nesse smoke; não foi demonstrado ganho geral de
qualidade/performance. [Evidências e limites](../../design-refactoring-validation.md).

## Preparação do PR

Aplicar somente o delta desta integração em worktree isolada sobre a main
`76e63313a748b641019536516700a6d1bf396bac`; adaptar o registro de módulos à tabela
vigente, preservando o restante da base. Revalidar essa árvore e manter separadas
as evidências iniciais e as verificações da branch do PR.
