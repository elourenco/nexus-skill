# Nomes dos comandos por host — 2026-11-04

O Claude Code expõe `/nexus:start`, `/nexus:brainstorm`, `/nexus:plan`,
`/nexus:build`, `/nexus:debug` e `/nexus:review`. O Codex preserva os nomes
`nexus` e `nexus-*`, com `nexus-brainstorm` substituindo `nexus-brainstorming`,
e apresenta títulos **NEXUS · Ação** pelos metadados das skills. O cliente Codex
validado acrescenta o namespace do plugin aos identificadores técnicos, como
`nexus:nexus-plan`; a instalação standalone usa `$nexus-plan`.

## Empacotamento

Claude sempre soma a descoberta de `skills/` da raiz aos caminhos declarados no
manifesto. Apontar o manifesto para seis wrappers adicionais manteria a lista
antiga. Por isso, o catálogo Claude publicado aponta para `build/claude/`, gerado por
[package_claude.py](../scripts/package_claude.py) a partir das fontes portáteis.
Não há uma segunda cópia editável dos procedimentos. O build só adapta nomes e
links da entrada principal; referências, scripts e assets ficam no núcleo irmão
`skills/nexus/`, sem um `SKILL.md` adicional que crie outra entrada.

O build local precede instalação/atualização. A distribuição de release gera o
mesmo pacote a partir do SHA imutável, atribui a versão ao manifesto gerado e
reutiliza os blobs dos assets binários. A reconciliação de releases no formato
anterior continua reproduzindo suas árvores originais. A promoção remota mantém
a atualização existente sem force; nenhum processo é adicionado às invocações.

O catálogo de desenvolvimento encaminha o Claude ao canal `plugins` com
[`git-subdir`](https://code.claude.com/docs/en/plugins/marketplace-reference#git-subdir-plugin-source)
e `path: build/claude`; uma origem Git na raiz continuaria expondo os nomes
portáteis. O catálogo distribuído usa caminho local, preservando instalações
fixadas. A presença do gerador no SHA de origem distingue o novo formato dos
snapshots anteriores, inclusive daqueles com catálogos remotos.

## Cenários observados

| Cenário | Resultado |
| --- | --- |
| Pacote gerado em caminho temporário com espaços | Exatamente seis entradas curtas; metadata e links válidos |
| Helpers chamados a partir de consumidor separado | Template e registro de hooks lidos; consumidor sem novos arquivos |
| Helper executado sem `-B`, seguido de rebuild | Regressão reproduzida e corrigida: bytecode de fontes gerenciadas é removido; rebuild passa |
| Rebuild com arquivo gerado obsoleto | Arquivo removido; conteúdo desconhecido continua bloqueando alteração |
| Fonte obrigatória ausente | Renderização recusa pacote incompleto |
| Release com checkout modificado após o commit | Pacote usa o commit, sem incorporar a edição local |
| Distribuição antiga seguida de nova | Proveniência anterior reconciliada; novo pacote recebe a versão correta |
| Descoberta nativa Claude | Seis entradas: brainstorm, build, debug, plan, review, start |
| Descoberta nativa Codex | Seis entradas habilitadas; novos títulos presentes na interface retornada |
| Migração nativa `0.3.0` → `0.3.1` | Instalação pelo catálogo da main com layout e nomes antigos; atualização nos dois hosts termina com os seis nomes atuais; versão fixada permanece em `0.3.0`; estado sintético preservado |

Clientes: Claude Code `2.1.308` e Codex CLI `0.166.0-alpha.5.1` do app. O wrapper
`codex` do Homebrew estava sem seu executável vendor; os testes usaram o binário
funcional do app. Perfis, repositórios Git e consumidores foram temporários;
nenhuma credencial foi copiada, inferência executada ou release remota publicada.

## Verificações

```sh
python3 scripts/package_claude.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s runtime/tests -q
python3 skills/nexus/scripts/hook_engine.py validate
python3 scripts/verify_hosts.py --codex /caminho/do/codex --output /tmp/descoberta.json
NEXUS_HOST_UPDATES=1 python3 -m unittest tests.test_release.NativeHostUpdatesTests -q
git diff --check
```

Suíte do projeto sobre a base atualizada: 242 testes, com um cenário nativo opt-in pulado e executado
separadamente com sucesso. Runtime: 56 testes aprovados; fixtures HTTP precisaram
de permissão de loopback fora do sandbox. Registro de hooks: 26 válidos. A suíte
existente em Python 3.14 emitiu warnings de conexões SQLite não fechadas.

O manifesto Claude gerado passou a validação estrita sem erros ou warnings de
manifesto. A avaliação separada de submissão ao diretório continua apontando
ausência de licença, preexistente e fora deste incremento. Inventários nativos
e testes de pacote não comprovam autocomplete visual em todas as superfícies,
seleção implícita pelo modelo ou ganhos de tokens/latência.
