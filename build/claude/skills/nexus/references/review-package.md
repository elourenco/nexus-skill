# Coleta de um pacote de review

O [helper](../scripts/review_package.py) coleta insumos; não realiza review, executa
testes ou autentica evidências. Use somente quando entregar o diff e seus contratos
por arquivo reduzir releituras/omissões. O protocolo de [review](review.md) continua
sendo a autoridade; não há dependência do runtime textual nem conversão automática
para o Council.

No checkout do NEXUS:

```sh
python3 skills/nexus/scripts/review_package.py \
  --workspace /caminho/consumidor --base main \
  --output /tmp/review-nexus-001 \
  --brief /caminho/plano-sanitizado.md \
  --evidence /caminho/resultado-sanitizado.txt \
  --gap 'Integração externa ainda não exercitada'
```

Em uma instalação, resolva o script a partir do `SKILL.md`; confira os
[caminhos](installation.md). A saída deve ser nova e ficar fora do workspace
revisado. O pai já deve existir. O helper não substitui arquivos.

- Sem `--head`, compara a base com o worktree: alterações staged e unstaged são
  capturadas juntas. Não exige commit. Untracked são listados como omitidos;
  `--include-untracked` inclui os não ignorados após inspecionar seu conteúdo.
- Com `--head REV`, compara dois commits resolvidos; mudanças locais posteriores
  não entram. A base deve ser ancestral do alvo. Não combina esse modo com untracked.
- `manifest.json` identifica base/alvo, modo, hash do diff, anexos, lacunas e
  `artifact_id`; `changes.diff` contém o diff. Anexos são cópias com hash, sem nomes
  originais ou caminhos absolutos no manifesto. Manifesto presente é o marcador
  de coleta completa; não é prova de aceite ou teste passando.
- Dois captures detectam mudanças observadas durante coleta; isso não é snapshot
  transacional. Pare escritores e testes que alterem arquivos antes da captura.
  Alteração após a coleta exige novo pacote/review das partes afetadas.
- Limites: 2 MiB por anexo/untracked, 16 MiB para diff/anexos; comando Git tem
  timeout de 30 s. Arquivos ignorados e conteúdo interno de submodules não entram;
  binários rastreados usam a indicação do Git, binários untracked têm digest.

O coletor desabilita `core.fsmonitor`, diff externo e textconv. Em modo worktree,
recusa arquivos rastreados com atributo `filter`: filtros clean/process podem
executar comandos e esconder alterações. Revise um commit explícito nesse caso;
o helper não cria esse commit nem altera a configuração Git.

Compartilhe apenas os arquivos necessários com o revisor autorizado. O helper
não remove segredos de código ou anexos: inspecione/sanitize antes de coletar e
não versione pacotes de projetos consumidores. O hash identifica conteúdo, sem
autenticar autor, execução dos checks ou independência do revisor.
