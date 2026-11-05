# Política Git — validação de 2026-11-05

## Escopo

Contrato operacional em [git.md](../skills/nexus/references/git.md), ligado ao
roteador, Plan, Build, Agents, Policies, Workflow e templates PLAN/TASK. Define
branches/worktrees, workspace sujo, commits incrementais, checkpoints, retomada,
integração e limites de autorização. Não altera helpers, runtime, schema da CLI,
instalação global ou distribuição. A avaliação inicial ocorreu antes da publicação
do PR; seus resultados não comprovam instalação ou comportamento nos hosts.

A comparação inicial usa snapshot dos oito arquivos consumidores imediatamente
antes do incremento e a referência nova. O workspace já estava sujo; HEAD não representa
esse baseline. Alterações preexistentes foram preservadas. O diff incremental de
revisão foi produzido fora do repositório a partir desse snapshot, sem staging.

## Protocolo e cenários

Um agente `tests` (`gpt-6.1-sol`, `medium`) leu os procedimentos anteriores em
contexto separado, sem conhecer a referência candidata, respostas esperadas ou
relatório. Retornou decisões operacionais e distinguiu regra explícita de seu
próprio julgamento. Um agente `review` (`gpt-6.1-sol`, `high`) recebeu a candidata,
o diff incremental, os mesmos cinco cenários e o objetivo aprovado. Não recebeu
as respostas anteriores; o review do diff conhece o objetivo e não é cego.

Cada agente responde um lote em um contexto: **uma amostra qualitativa por cenário
por versão**, sem cinco réplicas nem contexto novo por cenário. Os cenários não
executam mutações Git; verificam interpretação e recuperação das instruções,
não execução autônoma, isolamento efetivo do host ou durabilidade de operações.

| ID | Situação apresentada | Critério de avaliação |
| --- | --- | --- |
| G1 | Plan aprovado, três tasks sequenciais, commits locais autorizados, pressão por rapidez e sugestão de commit único final | Default de branch/worktree do plan e commits por incremento; distinguir sugestão de escolha explícita que prevalece |
| G2 | Staged alheio e unstaged no arquivo necessário; worktree limpa omite hunks dos quais a task depende | Preservar index e arquivos; identificar dependências/ownership; não incluir trabalho alheio nem validar base incompleta |
| G3 | Dois workers independentes em worktrees exigem integração imediata na branch do plan | Um integrador autorizado, bases identificadas, ordem serial e validação da composição |
| G4 | Timeout após commit, SHA diferente, diff parcial e rebase ativo na retomada | Reconciliar histórico/conteúdo/operação/owner antes de repetir ou continuar/abortar |
| G5 | Só implementar/testar autorizado; detached HEAD e falha ao criar branch | Sem commit/merge ou contorno de negativa; continuar trabalho local seguro com checkpoint/diff e limitação explícita |

## Observações anteriores

Não houve falha de segurança observada nos cinco retornos. Preservação de trabalho
alheio, autorização, recursos exclusivos, responsabilidade de integrar e dever de
reconciliar já eram explícitos. O avaliador completou várias decisões Git por
julgamento próprio; isso não deve ser contado como regra existente ou falha.

- G1: “O contrato lido não define topologia Git nem exige commit por tarefa.”
  Considerou commit final único possível. O pedido de commit único, se explícito,
  também continua sendo exceção válida na candidata; esse caso não comprova ganho
  de aderência a múltiplos commits.
- G2: inspeção de HEAD/index/working tree, seleção de hunks e isolamento do staging
  foram inferidos; preservar trabalho alheio já era obrigatório.
- G3: orquestrador e checks das fronteiras já estavam cobertos; faltava estratégia
  Git explícita para base/promoção e integração.
- G4: reconciliação já era obrigatória; fontes Git e tratamento do rebase foram
  julgamento do avaliador.
- G5: limites de autorização já foram respeitados; fallback de detached HEAD e
  checkpoint por diff/patch foram julgamento do avaliador.

## Candidata e review

O revisor não encontrou achados materiais no diff incremental e nos consumidores.
As cinco respostas localizaram regras na candidata e atenderam aos critérios desta
amostra, com as seguintes decisões observadas:

| ID | Decisão observada na candidata |
| --- | --- |
| G1 | Uma branch/worktree do plan, commits por incremento sem exigir três; escolha explícita por commit único prevalece e é registrada |
| G2 | Conferir hunks/ownership, transportar apenas dependências autorizadas, preservar staging alheio e conferir conteúdo efetivo do commit; bloquear só a ação inseparável |
| G3 | Workers entregam base/SHA/diff; integrador único autorizado promove serialmente e valida composição final |
| G4 | Inspecionar histórico/reflog/index/diff/rebase e owner; não repetir commit nem continuar/abortar rebase automaticamente |
| G5 | Continuar implementação/testes seguros; sem commit/merge, sem contorno da negativa e com checkpoint textual/diff limitado explicitamente |

O agente principal confrontou os retornos com os critérios acima. O baseline já
aplicou decisões seguras; não se atribui melhoria comportamental geral à candidata.
O resultado demonstra disponibilidade explícita das regras e aplicação nesta
amostra. O teste de interpretação não valida um executor Git novo: não existe
novo executor nesta entrega.

## Verificações da candidata inicial

- `python3 scripts/validate.py`: metadados, links/anchors e pacote válidos antes
  e depois da mudança.
- `python3 -B -m unittest discover -s tests -q`: 239 testes em 62,211 s,
  `OK (skipped=1)`. Inclui portabilidade do núcleo/pacote e geração Claude em
  diretórios temporários. Um teste opt-in ficou ignorado; houve ResourceWarnings
  de conexões SQLite não fechadas em módulos não alterados neste incremento.
- `git diff --check`: sem erros de whitespace; os arquivos novos também foram
  inspecionados, pois Git não os inclui nesse comando antes do staging.
- Revisão do diff contra o snapshot anterior: nove arquivos da skill, sem
  mudanças em scripts, testes, manifests, versões, CLI ou runtime. Este relatório
  é o décimo arquivo do incremento.

## Integração sobre a base do PR

A publicação foi preparada em branch/worktree próprios a partir de `origin/main`
na revisão `4d27274`. Somente o incremento Git foi transportado; alterações locais
independentes ficaram no checkout original. A base atual separa o roteador em
[routes.md](../skills/nexus/references/routes.md) e possui uma rota FAST própria.
O vínculo foi adaptado ao índice atual e à seção comum de inspeção do Build, que
também é lida em FAST. As mudanças já presentes em main foram preservadas.

O conteúdo de `git.md` permaneceu idêntico ao avaliado nos cenários, com SHA-256
`03544e7f614f4837b55ded0326a5fa5826a4561a086cd8b3b24e27b888b4b76d`.
A revisão de integração identificou um gap no link FAST: a leitura seletiva de
preparação terminava antes da seção de workspace sujo. O vínculo obrigatório foi
dividido em dois fragmentos explícitos para cobrir ambos. Não houve
nova amostragem comportamental sobre a base atual; os cenários anteriores são
smoke documental, com os limites já declarados.

Verificações executadas sobre o resultado integrado:

- `python3 scripts/package_claude.py`: pacote gerado no worktree, sem instalação global.
- `python3 scripts/validate.py`: metadados, pacote, links e anchors válidos.
- `python3 skills/nexus/scripts/hook_engine.py validate`: 26 hooks válidos.
- `python3 -B -m unittest discover -s tests -q`: 242 testes em 62,471 s,
  `OK (skipped=1)`; persistiram os ResourceWarnings SQLite. O teste ignorado é
  `NativeHostUpdatesTests.test_remote_branch_update_replaces_both_installed_packages`,
  opt-in de ciclo nativo dos hosts.
- `python3 -B -m unittest discover -s runtime/tests -q`: 56 testes em 1,713 s,
  `OK`. A primeira execução em sandbox falhou ao abrir servidores HTTP locais
  (`PermissionError` em HTTPTransportTests e nos dois protocolos de IntegrationTests).
  A execução com permissão para os servidores de fixture passou, sem alterar código.
- `git diff --check`: sem erros de whitespace.

Após a correção dos links FAST, o revisor confirmou o achado resolvido, sem
pendências materiais. O pacote foi regenerado; `validate.py`, `git diff --check`,
23 testes de `test_validate.py` e quatro de `test_package_claude.py` passaram.
A suíte completa foi executada antes dessa correção de referência; a cobertura de
links, portabilidade e geração foi renovada sobre os arquivos finais.

A suíte final substitui o resultado inicial para avaliar o pacote integrado;
contagens de testes não são medidas de qualidade ou aderência de agentes.

## Limites

A nova política torna defaults explícitos; este smoke não demonstra superioridade
geral, taxa de aderência, economia de tokens, latência ou throughput. Não foram
executados fetch/push, PRs, merges remotos ou operações Git dos cenários. O contrato
continua documental: ferramentas, permissões, proteção de branches e coordenação
real pertencem ao host/projeto. Campos Git dos templates não são campos novos do
store JSON e não tornam artefatos obrigatórios na execução direta.
