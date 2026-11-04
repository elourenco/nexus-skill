# CI/CD e releases

O workflow `Validate foundation` valida PRs e pushes em branches de trabalho.
Na principal, `Release` reutiliza exatamente os mesmos checks e só publica se
todos passarem: validação estrutural, testes do runtime, registro de hooks e
suíte de helpers. O job de validação tem apenas leitura; somente o job de
publicação recebe `contents: write` e `pull-requests: read`.

## Gatilho e versões

- Push em `main` ou `master`; somente a branch padrão do repositório publica.
  Hoje ela é `main`. A configuração continua funcionando se for renomeada para
  `master` e definida como padrão.
- Merge tradicional, squash e rebase disparam o mesmo fluxo por `push`.
  Push direto também publica; um único push contendo vários merges gera uma
  release com todos eles. Para uma release por PR, integre cada PR separadamente.
- Sem tags anteriores, a versão vem do manifesto Claude no commit integrado:
  atualmente `v0.3.0`. Depois, o patch aumenta: `v0.3.1`, `v0.3.2`, etc.
- A tag aponta exatamente para `github.sha`, o commit validado. Não há commit
  automático de bump em `main`. A distribuição derivada na branch `plugins`
  recebe a versão da release nos dois manifestos, mesmo quando os manifestos de
  desenvolvimento ainda mantêm a versão inicial.
- Tags estáveis `vX.Y.Z` ficam reservadas para este fluxo. Não criar, mover ou
  apagar essas tags manualmente. A política automática é de patch; mudanças na
  política para minor/major devem ser implementadas explicitamente.

## Notas da versão

O GitHub gera as notas usando o SHA exato e `previous_tag_name` explícito. A
configuração `.github/release.yml` inclui todos os PRs, sem excluir labels ou
autores, com títulos e links. A primeira versão inclui o histórico disponível;
as seguintes incluem o intervalo desde a versão anterior. Isso cobre PRs
integrados por squash/rebase sem depender do texto da mensagem do commit.

As notas são uma lista de PRs reconhecidos pelo GitHub, não um inventário de
commits sem PR. O GitHub fornece os arquivos-fonte ZIP/tar da tag; não há deploy
de serviço nem submissão aos diretórios públicos dos hosts neste fluxo.

## Distribuição para os hosts

Depois de publicar a release estável, `scripts/release.py` gera um snapshot para
`refs/heads/plugins`. Apenas os dois `manifest.version` e `.nexus-release.json`
diferem da árvore de origem. O arquivo de proveniência registra a versão da tag e
o SHA validado. O CI calcula a árvore Git esperada localmente e confere o hash
retornado pela API antes de promover o pacote.

Cada promoção acrescenta um commit cujo pai é o tip anterior da branch de
distribuição. A atualização usa `force: false`: uma alteração concorrente fora
da cadeia é rejeitada. A primeira publicação cria a branch a partir do commit de
origem. A branch `plugins` é reservada à automação; não integre essa branch em
`main`, não edite seu conteúdo nem apague sua proveniência.

Objetos intermediários não ficam visíveis no marketplace até a atualização
atômica da referência. Se a release existe e a promoção falhou, a reexecução
reconcilia a distribuição. A próxima release também reconcilia a predecessora
antes de publicar. Se a resposta da promoção se perdeu, a próxima execução
confere a proveniência e o hash da árvore antes de considerar concluído.
Reexecuções antigas preservam distribuições posteriores. Uma branch sem
proveniência, com conteúdo divergente ou histórico incompatível exige resolução
explícita; o workflow não a sobrescreve.

O catálogo continua `nexus-local` para preservar a identidade instalada, mas
agora pode ser registrado pela URL Git remota na branch `plugins`. Fontes
relativas nos catálogos apontam para a raiz do clone dessa branch. Não registre
uma URL avulsa do JSON: ela não inclui o pacote. O
[guia de instalação](../skills/nexus/references/installation.md) contém comandos,
migração de checkouts locais e opt-in de auto-update no Claude. O refresh de
marketplaces Git no Codex é explícito; não prometemos polling automático.

Os arquivos-fonte da tag representam o commit de origem e podem ter uma versão
inicial nos manifestos. Para instalar a versão com manifests atualizados, use a
branch `plugins`; não confunda a versão de origem com o pacote distribuído.
Não se instala scheduler, hook ou processo no projeto consumidor. O caminho
crítico acrescenta leitura de proveniência, criação de objetos Git e uma promoção
serial por release; não há benchmark de latência ou throughput desse fluxo.

## Concorrência e recuperação

A sequência inteira de validação e publicação compartilha um grupo exclusivo
com `cancel-in-progress: false` e `queue: max`. Isso serializa versões e mantém
até 100 execuções pendentes, conforme os
[limites de concorrência do GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
A ordem de chegada à fila pode diferir da ordem dos commits: o helper exige que
o commit anterior ao push já tenha sua release publicada. Eventos fora de ordem
falham antes de escrever; reexecute-os após os predecessores. Fila cheia pode
cancelar execuções adicionais: reexecute-as em ordem cronológica.

Se uma execução falhar:

1. Corrija a causa operacional, como indisponibilidade da API ou permissão do token.
2. Em Actions → Release, reexecute a execução mais antiga que falhou. Uma release
   já publicada também recupera a promoção da branch `plugins`.
3. Reexecute as posteriores que ficaram bloqueadas, em ordem.

Se o CI falhou por defeito no código, a reexecução do mesmo SHA não corrige o
snapshot. Integre a correção e use Actions → Release → Run workflow, selecionando
a branch padrão e preenchendo `previous_tag` com a última tag publicada, ou
`initial` se ainda não existir nenhuma tag. Essa ação autoriza explicitamente
publicar o snapshot corrigido, acumulando nas notas todos os PRs desde a última
release. O workflow revalida o SHA selecionado antes de publicar e recusa uma
base que tenha mudado enquanto aguardava na fila. O SHA reprovado não recebe
release. Uma tag anterior sem release deve primeiro ser recuperada por reexecução.
Configure o check de validação como requisito de merge nas regras da branch;
a proteção da branch não é alterada por estes arquivos.

Uma tag criada antes de uma falha de publicação é reutilizada na reexecução;
uma release já publicada reconcilia a distribuição sem recriar a release,
inclusive se versões mais novas existirem.
Nenhuma tag é movida, e uma falha HTTP diferente de 404 não é tratada como ausência
de release. Escritas de resultado incerto não são repetidas automaticamente.
Drafts, prereleases, histórico divergente e múltiplas tags no mesmo SHA exigem
resolução explícita. Force pushes são rejeitados.

## Ativação e validação

Integre os arquivos deste incremento na branch principal com Actions habilitado.
O primeiro push que adiciona `.github/workflows/release.yml` inicia a linha de
releases. Se o workflow estava desabilitado, use a recuperação manual para
publicar o snapshot atual. Não é necessário PAT: a publicação usa o `GITHUB_TOKEN` temporário.
Rulesets que bloqueiem tags ou a branch `plugins` devem permitir a escrita pelo
token desse workflow. Não é necessário conceder escrita em `main`.

Os testes em `tests/test_release.py` usam repositórios Git temporários reais e
uma API simulada para validar bootstrap, patch, intervalo das notas, idempotência,
falha entre tag/release, pushes fora de ordem, recuperação explícita após CI
reprovado e rejeição de histórico divergente. Os testes HTTP distinguem ausência
de release de falhas de permissão/transporte e verificam ausência de retries de escrita.
Não publicam releases de teste nem demonstram permissões reais do GitHub Actions.
Os cenários de distribuição e os testes nativos de instalação/atualização estão
registrados em [validação de atualizações](plugin-updates-validation.md).

```sh
python3 scripts/validate.py
python3 skills/nexus/scripts/hook_engine.py validate
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s runtime/tests -v
```

O contrato da API é o de
[geração e publicação de releases do GitHub](https://docs.github.com/en/rest/releases/releases).
O primeiro merge após a ativação é a verificação ponta a ponta pendente: deve
mostrar CI verde, tag no SHA integrado e release com os PRs esperados.

Validação local em 2026-11-02: 202 testes do projeto (15 de releases) e 56 do
runtime passaram, assim como validação estrutural, registro de hooks e
`git diff --check`. O runtime exigiu permissão para seus servidores de teste em
loopback. A suíte existente em Python 3.14 emitiu warnings de conexões SQLite
não fechadas, sem falhas. O actionlint 1.7.12 passou ignorando apenas
`unexpected key "queue" for "concurrency" section`: a ferramenta ainda não
reconhece `queue: max`, suportado pela documentação oficial vinculada acima.
Nenhuma release ou tag remota foi criada durante esses testes.
