# Integração de design e refatoração — 2026-11-03

## Entrega

Integração nativa de software-design-principles local 2.0.0, codebase-design,
senior-architect e architecture-patterns, complementada por diagnóstico de
refatoração e transformações do catálogo de Fowler. São sínteses contextuais,
não instalação ou execução das skills upstream. A
[proveniência](../skills/nexus/references/design-sources.md) registra contribuições,
adaptações e identidade das fontes consultadas.

- [Design arquitetural](../skills/nexus/references/architecture-design.md): fluxo
  real, dependências, interfaces, sistemas/soluções e padrões condicionais.
- [Refatoração](../skills/nexus/references/refactoring.md): caracterização,
  transformações e preservação de comportamento, efeitos e concorrência.
- [Modelagem](../skills/nexus/references/domain-design.md): princípios contextuais
  de responsabilidade, tipos, falhas, mutabilidade e linguagem.
- Roteamento em SKILL.md, policies e procedimentos de Brainstorming, Plan, Build e
  Review. Entradas especializadas chegam diretamente aos procedimentos; não
  precisam recarregar o roteador nem instalar outra skill.

Runtime, helpers, modelos e formatos de estado não foram alterados por esta entrega.
A avaliação inicial abaixo ocorreu antes da preparação do PR, em um workspace que
já continha alterações locais; sua base de comparação é o snapshot anterior deste
incremento, não HEAD. Alterações concorrentes nos manifests foram preservadas.
O PR foi preparado depois, por autorização explícita, em worktree isolada sobre
`main` (`76e63313a748b641019536516700a6d1bf396bac`), aplicando somente o delta
desta integração. O roteamento foi adaptado à tabela de módulos dessa base.

## Protocolo da avaliação inicial

A [suíte](../evals/design-refactoring-suite.json) contém nove solicitações sintéticas
com rubricas, compatíveis com o harness existente. Prompts idênticos foram enviados
a dois agentes `tests` em contextos novos (`gpt-6.1-sol`, `medium`), um com a versão
anterior e outro com a candidata. Cada executor recebeu somente o snapshot local,
o nome da entrada e os prompts, sem rubricas, respostas esperadas ou outra versão.

Cada agente respondeu os nove cenários em um único lote; portanto há **um contexto
novo por versão, não por cenário**. Leituras foram reutilizadas dentro do lote.
Os campos reference_reads são relatos de fontes aplicadas/reutilizadas; não são
telemetria independente de I/O por caso. As ações dos cenários não foram executadas:
é um smoke de aplicação das instruções e recuperação de orientação explícita.

O agente principal julgou todas as respostas. Um revisor independente (`review`,
`gpt-6.1-sol`, `high`) examinou diff, consumidores, fontes upstream pelos blobs e
as respostas de ambas as versões. Review é não
cego. Baseline e candidata executaram nessa ordem; não houve amostragem aleatória.

## Resultados observados

| Cenário | Aceite central | Anterior | Candidata |
| --- | --- | --- | --- |
| Simplificação aprovada | Entrega inline mínima; sem nova arquitetura ou aprovação | pass | pass |
| Fornecedor único e wrappers | Fronteira útil por responsabilidade; retry/erros coerentes | pass | pass |
| Thresholds e auditoria | Drivers reais; auditoria não implica event sourcing | pass | pass |
| Extração de transação | Atomicidade perdida, identidade e recuperação explícitas | pass | pass |
| Await → Promise.all | Distinguir ordem de resultados, início e efeitos; rejeitar equivalência | pass | pass |
| Legado sem testes | Caracterização e separação de refatoração/correção | pass | pass |
| Ciclo de dependências | Caminho exato e corte mínimo preservando export/contrato | pass | pass |
| Map versus Redis | Fake não prova exclusão distribuída, lease ou exactly-once | pass | pass |
| Retomada aprovada | Preservar REF-42/plano; patch proposto e validação final pendente | pass | pass |

O julgamento foi confirmado pelo revisor independente: **30/30 rubricas por versão,
9/9 cenários, sem achados materiais**. As respostas completas, rubricas,
hashes dos pacotes, textos anteriores consultados e conclusão do review ficam no
[recibo sintético](../evals/results/design-refactoring-2026-11-03.json).

O baseline já atendeu aos nove cenários. A recuperação documental mostrou que
critérios explícitos de interface e seleção de refatorações estavam ausentes;
caracterização e preservação de contratos já existiam. Na candidata, os três
grupos de orientação foram localizados explicitamente em architecture-design.md
e refactoring.md. Isso demonstra disponibilidade da orientação e aplicação nesta
amostra, sem sustentar superioridade geral sobre a versão anterior.

Na tarefa mecânica, ambos os executores declararam somente entrada, contrato de
invocação e Build como referências aplicadas. Nos casos pertinentes, a candidata
usou as novas referências a partir das entradas especializadas. O lote não comprova
que um host sempre carregará apenas essas fontes, nem mede economia de contexto.

## Verificações e tamanho na avaliação inicial

- `python3 scripts/validate.py`: metadados, links locais e pacote válidos.
- `python3 skills/nexus/scripts/hook_engine.py validate`: 26 hooks válidos.
- `python3 -m unittest discover -s tests -q`: 219 testes, OK. Foram observados
  ResourceWarnings de conexões SQLite não fechadas durante a suíte, sem falhas.
  Não houve alteração dos helpers/testes responsáveis neste incremento.
- `scripts.evaluate.validate_suite` e `prepare` com a suíte nova: nove cenários
  aceitos, snapshots/prompts pareados gerados. Preparar não executa inferência.
- `git diff --check`: sem erros de whitespace.

| Documento | Palavras anteriores | Palavras candidatas |
| --- | ---: | ---: |
| SKILL.md | 591 | 626 |
| domain-design.md | 485 | 738 |
| architecture-design.md | 0 | 995 |
| refactoring.md | 0 | 900 |

Contagem dos snapshots iniciais por `len(text.split())`, incluindo Markdown.
Na base isolada do PR, SKILL.md passa de 1.314 para 1.386 palavras; a otimização
do roteador presente no workspace inicial não faz parte desta integração. Os dois guias novos são
consultados por gatilho/seção; fonte de proveniência não é leitura operacional.
Esses números são tamanho textual, não tokens faturados ou latência observada.

## Validação na branch isolada do PR

Base: `76e63313a748b641019536516700a6d1bf396bac`. O diff contém somente os
15 arquivos desta integração. O roteador usa a tabela de módulos da main;
as otimizações locais anteriores não foram transportadas.

- 202 testes do projeto e 56 testes do runtime passaram; 26 hooks e pacote válidos.
  A suíte do projeto emitiu ResourceWarnings de conexões SQLite, sem falhas.
- A suíte de nove cenários foi aceita pelo harness e os pares preparados;
  preparação não executa inferência.
- Um novo agente `tests` (`gpt-6.1-sol`, `medium`) respondeu os nove prompts usando
  a árvore isolada, sem rubricas ou respostas anteriores. Um único contexto foi
  reutilizado no lote; as fontes foram lidas em lote e aplicadas por cenário.
- O julgamento das respostas resultou em 9/9 cenários e 30/30 rubricas. Os efeitos
  dos cenários não foram executados, e o baseline não foi repetido nessa base.
- Revisão independente aprovou instruções, escopo e evidências, confirmou as
  30 rubricas e os hashes do pacote isolado, sem achados materiais.

Respostas, hashes do pacote isolado, julgamento por rubrica e verificações estão
em `publication_validation` no recibo. Não se infere melhoria comparativa ou
carregamento mínimo pelo host a partir desse smoke.

## Limites e reprodução

Uma amostra por versão/cenário não prova ausência de regressões, ganho de qualidade
ou melhora de latência/throughput. Não houve cinco réplicas por variante. Não foram
executados serviços, Redis, PostgreSQL ou providers dos exemplos. As recomendações
de testes nessas respostas permanecem propostas, não garantias verificadas.
Não houve instalação global nem validação de descoberta nativa nos hosts.

Os hashes e textos anteriores do recibo identificam os snapshots da avaliação
inicial, que incluem alterações preexistentes e não representam a base isolada
do PR. O recibo conserva o conteúdo anterior consultado e inclui
prompts/respostas para inspeção. Para nova comparação, forneça o pacote anterior
completo em um diretório isolado e use o harness existente:

```sh
python3 scripts/evaluate.py prepare --suite evals/design-refactoring-suite.json \
  --previous-skills /tmp/nexus-previous/skills \
  --output /tmp/nexus-design-evaluation --run-id design-refactoring --samples 1
```

Os diretórios são alvos explícitos do operador; a preparação exige que a saída ainda
não exista. Execute cada cenário/contexto conforme o protocolo escolhido e registre
observações reais. Este smoke em lote não preenche células do harness como se
tivessem sido executadas em contextos independentes.
