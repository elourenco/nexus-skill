# Validação da refatoração de templates

Data: 2026-10-31. Base inspecionada: `5684e44`. Escopo: somente este diretório.
Os resultados aqui são verificações do pacote documental; os exemplos são fixtures
sintéticas e não demonstram execução de um produto consumidor.

## Baseline observada

A auditoria independente aplicou os templates antigos a FAST, retomada por outro
agente e review ligada a tarefa. Constatou ausência de consumo acumulável/atribuição
por tentativa, identidade explícita de PLAN, alvo versionado da review e formato
persistente de achados. O fluxo pequeno já era permitido e foi preservado.

Uma checagem local anterior à alteração retornou cinco falhas esperadas: ausência
de `spec_id`/`plan_id` na TASK, `Consumo medido`, REVIEW, EVIDENCE e contrato de
transições. Essa checagem é estrutural; não mede comportamento de agentes.

## Verificações reproduzíveis

Na raiz do checkout:

```sh
python3 scripts/validate.py
git diff --check
```

A primeira verifica metadados/links locais e a segunda erros de whitespace em
arquivos rastreados. Nenhuma valida semântica de artefatos, schema ou gates. A
inspeção complementar confere âncoras Markdown internas e relações dos exemplos.

## Cenários de aceitação

Uma revisão independente, sem editar o conteúdo, aplicou quatro cenários aos
contratos atuais: TASK FAST preenchida; transferência/retomada com A2 sem medição;
conclusão indevida com evidência não executada/review antiga; dois escritores na
mesma revisão. Resultado: comportamentos esperados abaixo, sem achado material
remanescente. Foram corrigidas duas ambiguidades durante o review: revisão inicial
da fixture e distinção entre revisão de registro e identidade imutável de EVIDENCE.

| Critério | Procedimento e resultado observado |
| --- | --- |
| SPEC → PLAN → TASKS | Inspeção da cadeia sintética: SPEC-001 lista PLAN-001 e TASK-001/002; PLAN referencia SPEC @1; ambas TASKS fixam SPEC/PLAN @1. Links e âncoras resolvidos. |
| ID estável | Aplicação de `blocked @4 → ready @5 → running @6`: manteve TASK-001; somente revisão, responsável, estado e novas entradas mudam. |
| Review ligada à tarefa | REV-001 identifica TASK-001, SPEC-001 e alvo base-A. Tentativa de usá-la para uma nova implementação foi rejeitada até reavaliação. |
| Preservação de custo/evidência | Handoff preservou A1, EVD-001 e 120 tokens **sintéticos**. A2 sem medição gerou entrada indisponível; total conhecido continua 120, cobertura parcial, sem custo monetário inferido. |
| Retomada | O revisor reconstruiu a próxima ação a partir de TASK @4 e referências, sem transcrição: conferir estado real, restaurar ambiente, transferir ownership, passar por ready e running, acrescentar A2. |
| FAST enxuto | Fixture pendente tem 19 linhas após o título. O revisor preencheu tarefa concluída em um arquivo, com evidência inline e histórico, sem SPEC/PLAN/ADR separados; budget omitido. |
| Compatibilidade/migração | Conferidos cinco caminhos anteriores, seis estados preservados e mapeamento dos campos renomeados/novos; nenhum ID ou registro consumidor foi migrado automaticamente. |
| Gate negativo | EVD-001 declara teste não executado e REV-001 solicita alterações: conclusão rejeitada; não há evidência suficiente para AC1. |
| Concorrência | Segunda escrita baseada em revisão antiga foi rejeitada; reconciliação e serialização exigidas. Releitura isolada não foi tratada como lock/CAS. |

Verificações locais observadas: `python3 scripts/validate.py` retornou
`OK: skill metadata and local Markdown link destinations`; `git diff --check`
retornou código 0, sem diagnóstico. A inspeção complementar por Python resolveu
28 referências com fragmento e conferiu TASK/review na revisão 4. As cinco
checagens estruturais que falhavam na baseline passaram. Essas checagens pontuais
não são um validador geral de schema e não foram instaladas como hook.

Para repetir os cenários, use [as fixtures](examples.md): preencha uma TASK FAST;
transfira TASK-001 mantendo o ID, A1 e EVD-001; acrescente A2 sem medição; tente
concluir com a evidência não executada; simule uma segunda escrita na revisão
anterior. Compare com os resultados da tabela e com os gates do [contrato](contracts.md).

## Compatibilidade com a base do PR

Antes da publicação, `origin/main` estava em `223e057`, com a atualização de
Policies. A leitura dessa revisão identificou e corrigiu o mapeamento de FAILED:
`running` durante correção autorizada; `blocked` ao aguardar dependência/decisão.
Cancelamento preserva resultados observados. Os nomes persistentes continuam os
mesmos. Esta conferência documental não substitui validação de runtime.

## Limites e integração pendente

Não há parser, validação de schema, locks, UI, executor de hooks, sincronização
ou enforcement automático de budget nesta entrega. A validação prática é de
interpretação documental e fixtures; não é teste end-to-end de um runtime.
As referências atuais de workflow/agents/hooks/policies/memory foram lidas, sem
alterá-las. O enum de estados e os caminhos antigos foram preservados. As outras
frentes devem coordenar qualquer futura mudança desse enum ou adoção por adapter.

## Integração com memória local — 2026-10-31

O conflito com o PR de memória foi resolvido preservando o exemplo JSON completo de `put` e adicionando o formulário Markdown como alternativa documental. Cenários de mesa: JSON mantém campos aceitos pelo helper; revisão do registro JSON continua gerada pelo store; revisão Markdown permanece manual; prazo `expires_at` só é aplicado pelo helper; migração não descarta proveniência. `python3 scripts/validate.py` e 29 testes de memória passaram no checkout integrado. Isso não demonstra aderência de agentes em projetos consumidores.
