# Instalação e atualização como plugin

O plugin `nexus` é exposto pelo catálogo `nexus-local`. A fonte de verdade é
`skills/`, com procedimentos e políticas em `skills/nexus/`. O Codex usa essas
skills diretamente. Para o Claude Code, `scripts/package_claude.py` gera um pacote
em `build/claude/` com nomes curtos; o catálogo Claude distribuído aponta para esse pacote.
O build não usa inferência nem altera os procedimentos mantidos no núcleo.

| Ação | Plugin Claude Code | Codex standalone |
| --- | --- | --- |
| Iniciar, consultar estado ou retomar | `/nexus:start` | `$nexus` |
| Explorar opções e definir direção | `/nexus:brainstorm` | `$nexus-brainstorm` |
| Planejar etapas verificáveis | `/nexus:plan` | `$nexus-plan` |
| Executar uma mudança com validação | `/nexus:build` | `$nexus-build` |
| Reproduzir, diagnosticar e corrigir | `/nexus:debug` | `$nexus-debug` |
| Avaliar diff e riscos | `/nexus:review` | `$nexus-review` |

O Codex pode acrescentar o namespace do plugin: `$nexus:nexus-plan`, por exemplo.
Use o nome oferecido pelo seletor. Os metadados `agents/openai.yaml` apresentam
**NEXUS · Plan**, **NEXUS · Build** etc. no app; o nome técnico preserva a identidade
`nexus-*`. A entrada principal é **NEXUS**. Por leitura direta, use o
[contrato de invocação](invocation.md) e o procedimento correspondente.

### Migração dos nomes

No plugin Claude, `/nexus:nexus` passa a `/nexus:start` e as ações perdem o segundo
prefixo: `/nexus:nexus-plan` passa a `/nexus:plan`. Brainstorm usa `/nexus:brainstorm`.
Não são expostos aliases antigos no menu. Atualize prompts e atalhos que gravaram
os nomes anteriores. O catálogo e a identidade `nexus@nexus-local` são preservados.

No conjunto standalone/Codex, `nexus-brainstorming` passa a `nexus-brainstorm`.
Ao copiar skills manualmente, confira alterações locais, substitua o conjunto pela
mesma revisão e remova a pasta antiga `nexus-brainstorming/` da instalação para
não manter duas entradas. Não apague estado ou memória do consumidor.

## Instalar versões publicadas

A branch remota `plugins` recebe o snapshot de cada release aprovada pelo CI.
Os dois manifestos distribuídos recebem a versão da tag; `.nexus-release.json`
identifica a tag e o SHA de origem. A tag continua apontando para o commit de
origem validado. O nome `nexus-local` é uma identidade histórica do catálogo,
não uma restrição de origem.

Os catálogos de `main` encaminham o plugin para `plugins`, mesmo se o marketplace
for adicionado sem escolher uma branch. Isso evita usar a versão inicial dos
manifestos de desenvolvimento. O pacote distribuído contém catálogos locais,
sem redirecionamento, e não consulta outra versão durante sua instalação.

Para fixar uma versão, substitua `plugins` por `plugin-vX.Y.Z` nos comandos de
instalação. Essa tag de pacote tem manifestos corretos e permanece na mesma
árvore após novas releases. As tags `vX.Y.Z` continuam identificando o código-fonte;
não use essas tags para fixar uma instalação. Tags de pacote são produzidas pelo
novo fluxo; use somente referências existentes. Não há criação em massa de tags
de pacote para versões antigas.

Os comandos abaixo exigem a primeira publicação da branch `plugins`. Se ela ainda
não existir, use a instalação local da próxima seção. Uma tag/release sem essa
branch não conclui a distribuição. O repositório de desenvolvimento descreve o
pipeline em `docs/releases.md`; esse documento não é uma dependência da skill.

Claude Code:

```sh
claude plugin marketplace add https://github.com/elourenco/nexus-skill.git#plugins
claude plugin install nexus@nexus-local
claude plugin list --json
```

Habilite `/plugin` → **Marketplaces** → **nexus-local** → **Enable auto-update**.
Marketplaces de terceiros não habilitam essa opção por padrão. O host verifica
atualizações em segundo plano depois de iniciar a sessão; aplique-as com
`/reload-plugins` ou abra uma nova sessão. Esse opt-in pertence ao usuário, não
ao pacote. Para atualizar imediatamente:

```sh
claude plugin marketplace update nexus-local
claude plugin update nexus@nexus-local
```

O refresh explícito do catálogo evita usar sua cópia ainda antiga: no cliente
validado, apenas `plugin update` imediatamente após uma release manteve a versão
anterior quando o catálogo ainda não havia sido atualizado.

Codex:

```sh
codex plugin marketplace add https://github.com/elourenco/nexus-skill.git --ref plugins
codex plugin add nexus@nexus-local
codex plugin list --json
```

Para receber uma nova versão explicitamente:

```sh
codex plugin marketplace upgrade nexus-local
codex plugin add nexus@nexus-local
codex plugin list --json
```

Reabra a sessão e confira a versão efetivamente instalada e a origem das skills.
Não há garantia documentada de polling automático para marketplaces Git/locais
do Codex. O canal remoto remove a dependência de atualizar um checkout pessoal;
o agendamento do refresh continua sendo responsabilidade do host.

### Corrigir uma instalação registrada em main

Após a publicação desta correção, atualize o catálogo e reinstale/atualize o
plugin com a sequência do seu host acima. Antes dessa publicação, ou se o
marketplace continuar em uma revisão antiga, remova o plugin e o catálogo com os
comandos em **Atualizar e remover** e registre novamente usando `#plugins` no
Claude ou `--ref plugins` no Codex. Confira `plugin list --json`; no Codex,
confira também a versão do manifesto na origem das skills efetivamente carregadas.
Não edite o cache nem apague o estado do consumidor.

### Migrar uma instalação local existente

Inspecione `plugin marketplace list` e `plugin list --json` no host escolhido.
Se `nexus-local` aponta para um diretório local e você quer acompanhar releases,
remova essa instalação e catálogo usando os comandos em **Atualizar e remover**,
depois execute os comandos remotos acima. A identidade do plugin é preservada,
mas habilitação, escopo e opt-in de auto-update precisam ser conferidos novamente.
Não remova o checkout de desenvolvimento nem `.nexus/local/` do consumidor.

## Instalar e verificar um checkout local

O catálogo da raiz de desenvolvimento segue a release publicada. Para testar
o conteúdo de um checkout, gere uma cópia explícita com catálogos locais:

```sh
NEXUS_DEV_ROOT="$(mktemp -d)/nexus"
python3 scripts/verify_hosts.py --prepare-local "$NEXUS_DEV_ROOT"
```

O destino deve ser novo; o comando recusa sobrescrevê-lo. A cópia mantém os bytes
das skills e manifestos do checkout, gera o pacote Claude com nomes curtos e
configura catálogos locais. O catálogo Claude aponta para `build/claude/` dessa cópia.
Ela mostra a versão de desenvolvimento, sem afirmar que é uma release publicada.
Os comandos abaixo registram essa cópia e habilitam o plugin no perfil escolhido.
Não são executados automaticamente pela skill.

Claude Code:

```sh
claude plugin validate "$NEXUS_DEV_ROOT/build/claude/.claude-plugin/plugin.json"
claude plugin validate "$NEXUS_DEV_ROOT/.claude-plugin/marketplace.json"
claude plugin marketplace add "$NEXUS_DEV_ROOT"
claude plugin install nexus@nexus-local
claude plugin list --json
```

Abra uma nova sessão no projeto consumidor e invoque `/nexus:start` com seu objetivo. Para experimentar uma pasta apenas na sessão, Claude Code também aceita `claude --plugin-dir "$PWD/build/claude"`; execute no checkout depois do build ou forneça o caminho absoluto do pacote gerado ao iniciar no consumidor. Não mantenha uma cópia standalone da mesma skill ativa junto com o plugin sem resolver a duplicação.

Codex:

```sh
codex plugin marketplace add "$NEXUS_DEV_ROOT"
codex plugin add nexus@nexus-local
codex plugin list --json
```

Abra uma nova sessão no consumidor, selecione a skill `nexus:nexus` no seletor ou use `$nexus:nexus` no prompt. Confirme a origem no plugin `nexus@nexus-local`. Se o CLI instalado não tiver `plugin`, verifique a versão/caminho do executável antes de alterar configurações. Não confunda o catálogo disponível com plugin instalado/habilitado.

Validação local observada em Claude Code `2.1.308` e Codex CLI `0.166.0-alpha.5.1`, em macOS/Python `3.14.6`. Estas são versões testadas, não uma promessa de versão mínima ou suporte a todas as superfícies. Os helpers exigem Python 3.10+ e POSIX; a skill textual pode ser usada sem Python. Windows nativo, cloud, Claude.ai e Cowork não foram validados.

## Caminhos e estado do consumidor

Resolva os links a partir do `SKILL.md` descoberto pelo host. No Claude, as seis entradas apontam para o núcleo compartilhado na pasta irmã `nexus/`; seus helpers, referências e assets ficam nessa pasta. Não assuma um cache global fixo, nem use o CWD do consumidor para procurar `skills/nexus/scripts`. O host pode mover ou substituir a instalação ao atualizar.

Para os exemplos abaixo, defina `NEXUS_PLUGIN_ROOT` com a raiz absoluta da instalação verificada no host e execute no projeto consumidor. A raiz tem `.claude-plugin/plugin.json` ou `.codex-plugin/plugin.json`, além de `skills/nexus/scripts/`; não é a pasta da skill em si. No pacote Claude, a entrada principal está em `skills/start/SKILL.md`. Definir essa variável não é uma configuração persistente ou um requisito de descoberta do host.

```sh
: "${NEXUS_PLUGIN_ROOT:?Defina a raiz absoluta do plugin instalado}"
python3 "$NEXUS_PLUGIN_ROOT/skills/nexus/scripts/workflow.py" template task
python3 "$NEXUS_PLUGIN_ROOT/skills/nexus/scripts/hook_engine.py" validate
```

Essas duas chamadas apenas leem o pacote. Para adotar o workflow, confirme autorização de persistência e exclusão de `.nexus/local/` do Git do consumidor antes de executar:

```sh
python3 "$NEXUS_PLUGIN_ROOT/skills/nexus/scripts/workflow.py" \
  --state "$PWD/.nexus/local/workflow.json" init --workspace "$PWD"
python3 "$NEXUS_PLUGIN_ROOT/skills/nexus/scripts/workflow.py" \
  --state "$PWD/.nexus/local/workflow.json" show
```

`init` recusa sobrescrever estado existente; em retomada use `show` e reconcilie. Para memória, escolha raiz e scope conforme [Memory](memory.md); para hooks, informe `--workspace`, `--state` e um registro do consumidor conforme [Hooks](hooks.md). O registro padrão chama `scripts/validate.py` do workspace: ele valida o projeto NEXUS, não é um check universal. Não o conecte automaticamente a eventos do host.

Nunca grave estado no cache do plugin. Se Claude e Codex atuarem no mesmo consumidor, configure os mesmos caminhos absolutos para a mesma fonte de estado; bancos distintos não compartilham locks ou deduplicação. Prefira uma única fonte persistente conforme [Workflows](workflow-state.md). A memória JSON e a memória SQLite dos hooks continuam independentes, sem sincronização automática.

O plugin não inicia processos residentes, não chama modelos adicionais, não registra hooks nativos nem despacha agentes. Os helpers e o runtime textual opcional continuam sujeitos a chamada e autorização explícitas. Isso evita adicionar execução de comandos a cada edição; não há benchmark de latência ou throughput do plugin.

## Atualizar e remover

Para pacotes locais de desenvolvimento, gere uma nova cópia após alterar o
checkout e registre sua origem novamente; mantenha a versão igual nos dois
manifestos. Para instalações remotas,
o CI atribui a versão da release aos dois manifestos na branch `plugins`;
não é necessário um bump manual em cada merge. Os manifestos da branch de
desenvolvimento definem a versão inicial da primeira release. Não edite arquivos
dentro do cache instalado.

`plugins` acompanha releases; `plugin-vX.Y.Z` permanece fixada mesmo após refresh.

No Claude Code, após atualizar o catálogo local:

```sh
claude plugin update nexus@nexus-local
```

No Codex, após atualizar o catálogo local, instale novamente e confira a versão retornada:

```sh
codex plugin add nexus@nexus-local
codex plugin list --json
```

Reabra a sessão depois da atualização. Se o cliente mantiver uma cópia antiga, confira a origem/versão e reinstale usando os comandos abaixo, preservando o estado externo do consumidor. Não apague `.nexus/local/` para resolver um problema de descoberta.

```sh
claude plugin uninstall nexus@nexus-local
claude plugin marketplace remove nexus-local
```

```sh
codex plugin remove nexus@nexus-local
codex plugin marketplace remove nexus-local
```

A remoção do pacote não é uma instrução para apagar memória, workflow ou journal do consumidor. A instalação por catálogo local é para uso autorizado; licença e publicação continuam pendentes. Nenhum comando acima concede autorização para commit, push, merge ou deploy.

## Fontes dos formatos

Consultadas em 2026-11-03: [empacotamento OpenAI](https://developers.openai.com/plugins/build/plugins), [atualizações Claude Code](https://code.claude.com/docs/en/discover-plugins#keep-plugins-updated) e [hospedagem e refs de marketplaces Claude](https://code.claude.com/docs/en/plugins/host-marketplace). A disponibilidade de hooks varia entre hosts e superfícies; adapters nativos não fazem parte deste incremento.
