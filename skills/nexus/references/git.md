# Git na execução de plans e tasks

Contrato operacional para trabalho em repositórios Git. Não instala executor,
hooks ou gerenciador de branches; o agente usa as ferramentas reais do host.
Fora de um repositório, declare Git não aplicável e continue no escopo autorizado.

## Autoridade

Instruções do host/projeto e escolhas explícitas do usuário prevalecem sobre estes
defaults. Reuse autorização válida por ação, alvo e escopo. Distingua:

- Implementar, testar e revisar arquivos localmente.
- Criar branches/worktrees e realizar commits locais incrementais.
- Integrar branches de tasks na branch do plan.
- Publicar, abrir PR, integrar no destino, fazer deploy ou remover recursos.

O aceite de um plan autoriza somente os efeitos apresentados e permitidos pelo
host; não inclua commit ou merge implicitamente. Apresente os efeitos pertinentes
juntos para um aceite, quando necessário; não peça confirmação por task/commit
já autorizado. Sem autorização de commit, entregue diff e evidências locais.

## Preparação e isolamento

Antes de editar, confira repositório, branch ou detached HEAD, worktree atual,
destino e SHA da base, alterações staged/unstaged/untracked e operações pendentes
de merge, rebase ou cherry-pick. Identifique ownership; não infira base pelo nome
`main`. Registre o mínimo na fonte existente, sem novo store ou formulário.

Atualize referências remotas quando permitido e disponível, antes de escolher a
base; fetch não significa pull ou troca de branch. Sem rede, use a base conhecida
se suficiente e declare a defasagem. Reconcilie operação em andamento antes de
iniciar outra; não continue nem aborte operação alheia automaticamente.

| Execução | Default |
| --- | --- |
| Plan com várias tasks sequenciais | Uma branch do plan e um worktree dedicado; tasks avançam nessa mesma linha |
| Tasks realmente independentes em paralelo | Branch e worktree por unidade independente, com integração central na branch do plan |
| Alteração pequena e isolada | Pode usar branch de trabalho existente, com destino, ownership e estado seguros |
| Branch/worktree já preparados para a execução | Reutilizar após conferir base, arquivos e responsáveis; não criar isolamento duplicado |

Siga convenções do projeto/usuário para nomes e diretórios; não fixe prefixo
global. Prefira ferramenta nativa do host para worktree quando disponível. No
fallback Git autorizado, confira caminho livre e exclusão do versionamento se
dentro do repositório. Não sobrescreva branch/worktree existente. Um worktree
vinculado ou detached HEAD não comprova sozinho isolamento de outros executores.

Se o host gerencia detached HEAD ou impede criar branch/worktree, preserve seus
controles. Continue localmente apenas se ownership e preservação forem seguros;
senão suspenda a escrita afetada e informe a necessidade de isolamento. Não
contorne uma negativa de permissão. Declare o fallback e limite da entrega.

## Workspace sujo

| Estado observado | Ação |
| --- | --- |
| Alterações independentes do plan | Preserve o checkout; prefira outro worktree para executar |
| Alterações da execução atual | Reconcilie diff e checkpoints e continue; sujeira esperada não exige reinício |
| Dependência de alterações não commitadas | Identifique arquivos/hunks e origem; transporte somente conteúdo necessário e autorizado, preservando o original |
| Ownership incerto ou hunks inseparáveis | Esclareça antes de editar/comitar o trecho dependente; continue trabalho independente seguro |

Novo worktree não herda alterações não commitadas. Não valide sobre uma base que
omita dependências necessárias. Se não for possível separar os hunks, proponha
inclusão autorizada da dependência ou sequência compatível; staging parcial não
torna uma mudança semanticamente independente.

Não use stash, descarte, `reset --hard`, `clean` ou troca forçada de branch para
limpar automaticamente. Preserve também o index alheio. Havendo staging alheio,
isole a preparação do commit em workspace/index próprio, quando permitido e
seguro, ou suspenda somente o commit; não faça unstage do trabalho de outro owner.

## Commits por incremento

Quando commits locais estiverem autorizados, comite cada incremento coerente e
verificável ao atingir seu ponto de conclusão. Plans com entregas separáveis
devem produzir múltiplos commits durante a execução, evitando acumular tudo para
um commit final. Não imponha contagem artificial: uma task pode render vários
commits; tasks pequenas inseparáveis podem compartilhar um. Respeite uma escolha
explícita diferente do usuário/projeto e registre a exceção na fonte existente.

Cada commit tem propósito identificável, referência à task quando houver ID,
somente arquivos/hunks autorizados e checks pertinentes. Confira o diff staged e
o conteúdo efetivo do commit; testes do working tree podem incluir dependências
não staged e não comprovam o conteúdo commitado. Prefira commits utilizáveis;
TDD pode observar falha antes da implementação sem publicar um commit quebrado.
Não divida mecanicamente todos os testes, toda a implementação e correções finais.

Checkpoint WIP é excepcional, identificado como incompleto e autorizado; não
satisfaz aceite nem pode ser promovido como incremento validado. Amend, rebase e
squash exigem autorização compatível; não reescreva histórico compartilhado como
limpeza automática. Preserve commits úteis; regras obrigatórias do projeto para
histórico/squash prevalecem, sem eliminar checks incrementais.

## Checkpoint e retomada

Ao concluir incremento, transferir execução ou interromper trabalho relevante,
registre branch/worktree, base e SHA atual, tasks/commits concluídos, alterações
restantes, checks e revisão coberta, bloqueios e próxima ação. Sem persistência,
declare o limite de retomada do chat; não grave diffs privados em memória global.
Commit não comprova aceite; checkpoint textual não cria snapshot Git.

Após timeout ou resultado incerto, inspecione HEAD, histórico/reflog disponível,
index, arquivos e operação pendente antes de repetir. Confira conteúdo e origem:
SHA diferente pode resultar de reescrita, sem provar perda ou duplicação. Não
repita commit, integração, continue/abort de rebase ou push sem reconciliar o
resultado e ownership. Registre o que ocorreu e retome só a pendência autorizada.
Cancelamento não desfaz commits, arquivos ou efeitos remotos.

## Integração e entrega

Um integrador controla a branch do plan; serialize mutações de seu checkout,
index e referências. Workers entregam base, SHA/diff, ownership e evidências e
não disputam a branch de integração. Tasks dependentes partem da revisão que
já contém seus pré-requisitos; não as despache sobre base incompleta. Worktrees
não isolam bancos, portas, serviços ou diretórios de build compartilhados.

1. **Tasks → plan:** confira autorização, base e resultado de cada entrega.
   Integre em ordem de dependência, preferindo fast-forward quando possível.
   Para divergências, siga a estratégia acordada de merge, rebase ou cherry-pick;
   não misture mecanismos sem motivo. Rebase somente de histórico próprio não
   compartilhado e autorizado. Confira o resultado antes de liberar dependentes.
2. **Plan → destino:** atualize a visão da base, resolva conflitos semanticamente
   e valide o resultado integrado e as fronteiras afetadas. Checks individuais
   das tasks não comprovam a composição. Mudança de base, resolução de conflito
   ou edição posterior exige renovar a cobertura afetada; confira a revisão
   efetiva antes da promoção. Sem autorização para atualizar o destino, entregue
   branch/diff e evidências, deixando integração/publicação explicitamente pendentes.

Não resolva conflitos em massa por ours/theirs. Preserve proteções, PRs e checks
do projeto; aprovação local não autoriza merge remoto ou force-push. Em branch
compartilhada publicada, preserve histórico conforme a estratégia do projeto.
Resultado incerto de publicação exige consultar o remoto antes de repetir.

Remova branches/worktrees somente com autorização e após confirmar integração
ou preservação confiável do trabalho, sem mudanças locais ou owners ativos.
Não use remoção forçada nem squash como encerramento automático. Informe estado
final, commits, validações, exceções e integrações/publicações pendentes.

Setup de worktrees e dependências tem custo de disco e latência; reutilize
isolamento válido e paralelize apenas trabalho independente com recursos
reservados. Um único integrador limita contenção e conflitos, sem prometer ganho
de throughput. Não faça fetch, reinstalação ou suíte completa por todo commit
sem necessidade; execute checks proporcionais e os gates finais exigidos.
