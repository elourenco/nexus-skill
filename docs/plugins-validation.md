# Validação do empacotamento NEXUS — 2026-11-02

Escopo: primeiro incremento local, skill compartilhada e helpers explícitos. Sem publicação, licença escolhida, configuração global alterada, inferência ou credenciais de providers. Base do desenvolvimento: `0d85604f1beb44f9e475e9b777bb8ec10d9cce53`.

## Cenários executados

| Cenário | Resultado observado |
| --- | --- |
| Ausência de manifesto/catálogo, JSON inválido, divergência de versões ou caminhos | Testes falharam antes de estender o validador e passaram após a implementação |
| Componente automático declarado ou descoberto em diretório padrão | Validador recusa sair do escopo de plugin de skills |
| Pacote copiado para diretório somente leitura, com espaços no caminho | Workflow exportou template e inicializou/leu estado externo; memória inicializou/leu store externo; hooks validaram registro |
| Segunda cópia do pacote usando o mesmo workspace consumidor | Estado do workflow preservado; store de memória continua legível; conteúdo das duas cópias permaneceu intacto |
| Codex: catálogo local → instalação → listagem | `nexus@nexus-local`, versão `0.1.0`, instalado e habilitado |
| Codex app-server: `initialize` → `skills/list` em consumidor separado | Uma skill `nexus:nexus`, habilitada, com `pluginId=nexus@nexus-local` e caminho dentro do cache instalado |
| Claude Code: validação → catálogo local → instalação → listagem | Manifestos aceitos; `nexus@nexus-local`, versão `0.1.0`, habilitado |
| Claude Code e Codex: instalar 0.1.0 → atualizar cópia sintética para 0.1.1 → remover plugin e catálogo | Ambos atualizaram a versão listada e removeram a instalação; bytes do estado do consumidor preservados |

Os hosts foram executados com `CODEX_HOME` e `CLAUDE_CONFIG_DIR` apontando para diretórios temporários de teste, sem copiar credenciais. Esses valores foram fornecidos somente ao ambiente dos subprocessos. Nenhum plugin foi instalado no perfil habitual do usuário. O app-server não iniciou thread nem turno de inferência.

## Comandos de regressão

```sh
python3 scripts/validate.py
python3 -B skills/nexus/scripts/hook_engine.py validate
python3 -B -m unittest discover -s tests -p test_plugins.py -v
python3 -B -m unittest discover -s tests -q
python3 -B -m unittest discover -s runtime/tests -q
git diff --check
```

Resultados finais: **112 testes dos helpers/pacote e 56 do runtime aprovados (168 no total)**. Os 7 testes novos de plugins também passaram isoladamente. Metadados, links, manifestos/catálogos, registro dos 26 hooks e `git diff --check` aprovados. A suíte do runtime usa HTTP em loopback e foi executada com a permissão necessária para abrir essas portas, sem serviços externos.

`claude plugin validate` passou com `--strict --json` tanto para o manifesto do plugin quanto para o catálogo: sem erros ou avisos de manifesto. As observações de diretório público sobre licença ausente e ícone são uma avaliação separada; não houve submissão.

Revisão independente somente leitura: nenhum defeito reproduzível identificado no diff; o revisor repetiu os 7 testes de plugins e a checagem de whitespace. Estes resultados são locais; o estado da CI deve ser consultado no PR. Commit, push e abertura do PR foram autorizados posteriormente pelo usuário.

## Ambiente e limites

- macOS; Python 3.14.6; Claude Code 2.1.308; Codex CLI 0.166.0-alpha.5.1.
- O teste Python de substituição verifica compatibilidade do mesmo conteúdo em outro caminho; não demonstra migração entre schemas ou versões futuras.
- O teste nativo de atualização alterou apenas a versão dos manifestos em uma cópia temporária, para 0.1.1. A versão entregue no worktree continua 0.1.0; não foi validada migração de dados ou evolução futura dos helpers.
- A instalação/discovery não comprova aderência de um modelo ao workflow, seleção implícita ou qualidade das análises. Invocação conversacional nos dois hosts permanece avaliação separada.
- O validador local verifica o contrato restrito do NEXUS, não implementa todos os schemas upstream. Claude Code também informa que a submissão ao diretório público precisa de licença; sua validação local sem o perfil `directory` é distinta desse aceite.
- O catálogo aponta para a raiz do checkout completo. O host pode copiar arquivos de suporte junto com a skill; a presença de `runtime/` não o ativa. Não colocar dados privados no diretório distribuído.
- O baseline dos helpers já emite `ResourceWarning` de conexões SQLite não fechadas em testes. A janela de crash de subprocesso identificada na revisão anterior e adapters nativos de hooks permanecem fora deste incremento.

## Ícone núcleo conectado (2026-11-03)

O PNG aprovado pelo usuário é compartilhado pelos dois manifestos e por
`skills/nexus/agents/openai.yaml`, sem duplicar a imagem. O arquivo original foi
copiado sem alteração de pixels: 1254 × 1254, sRGB, 1.153.168 bytes.

- Codex: `interface.logo` e `interface.composerIcon` usam caminhos relativos à
  raiz do plugin; `icon_small` e `icon_large` são relativos à skill principal.
  O formato e as dimensões seguem os [requisitos de imagens do Codex](https://developers.openai.com/plugins/deploy/submission#icons-and-screenshots).
- Claude: `icon` no manifesto aponta para a mesma imagem. Conforme a
  [referência do manifesto](https://code.claude.com/docs/en/plugins/manifest-reference#directory-listing-fields),
  esse campo atende ao diretório da Anthropic e é ignorado pelo Claude Code
  durante a execução; não promete um ícone na interface de terminal.
- `python3 scripts/validate.py`: aprovado. A suíte completa `tests/` passou
  com 202 testes, incluindo os sete testes existentes de pacote e relocação.
  O validador local passou a aceitar `icon` somente no manifesto Claude.
- YAML lido com o parser do Ruby; as cinco referências de branding resolveram
  para o mesmo SHA-256, inclusive após copiar `skills/` para um diretório
  temporário. `magick identify` confirmou formato PNG, dimensões e espaço sRGB.
- `claude plugin validate .claude-plugin/plugin.json --strict --json` e a
  validação estrita do catálogo: sem erros ou avisos de manifesto no Claude Code
  2.1.308. A pendência anterior de licença para submissão pública permanece.
- Exibição visual no Codex não verificada: o executável `codex` instalado no
  PATH falhou com `ENOENT` para seu binário nativo. O `quick_validate.py` da
  skill-creator também não pôde executar porque o Python global não tem PyYAML;
  a validação do projeto foi executada normalmente.

A validação não instala o plugin no perfil do usuário nem modifica caches.
Instalações já existentes precisam receber o pacote atualizado antes de exibir
o novo ícone.
