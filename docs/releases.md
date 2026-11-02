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
  automático de bump. A versão da release identifica o snapshot do repositório;
  a versão dos manifestos do plugin continua sendo mantida explicitamente.
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
de serviço, publicação em marketplace ou pacote adicional neste fluxo.

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
2. Em Actions → Release, reexecute a execução mais antiga que falhou.
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
uma release já publicada é um no-op, inclusive se versões mais novas existirem.
Nenhuma tag é movida, e uma falha HTTP diferente de 404 não é tratada como ausência
de release. Escritas de resultado incerto não são repetidas automaticamente.
Drafts, prereleases, histórico divergente e múltiplas tags no mesmo SHA exigem
resolução explícita. Force pushes são rejeitados.

## Ativação e validação

Integre os arquivos deste incremento na branch principal com Actions habilitado.
O primeiro push que adiciona `.github/workflows/release.yml` inicia a linha de
releases. Se o workflow estava desabilitado, use a recuperação manual para
publicar o snapshot atual. Não é necessário PAT: a publicação usa o `GITHUB_TOKEN` temporário.
Rulesets que bloqueiem tags devem permitir a criação por esse token.

Os testes em `tests/test_release.py` usam repositórios Git temporários reais e
uma API simulada para validar bootstrap, patch, intervalo das notas, idempotência,
falha entre tag/release, pushes fora de ordem, recuperação explícita após CI
reprovado e rejeição de histórico divergente. Os testes HTTP distinguem ausência
de release de falhas de permissão/transporte e verificam ausência de retries de escrita.
Não publicam releases de teste nem demonstram permissões reais do GitHub Actions.

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
