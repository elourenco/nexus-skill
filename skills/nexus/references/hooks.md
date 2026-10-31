# Hooks — executor local por chamada explícita

O [executor Python](../scripts/hook_engine.py) executa o [registro JSON](../assets/hooks.json), sem dependências externas. Requer Python 3.10+ e POSIX. Não instala hooks, modifica configurações globais, chama modelos ou concede permissões do host. A skill continua utilizável sem ele.

## Auditoria e suporte real

A base anterior continha nove nomes lógicos, sem handlers. Seus IDs foram preservados, incluindo `model.route`, `budget.check`, `review.dispatch` e `failure.recover`. O validador existente `scripts/validate.py` não foi alterado. O inventário do host encontrou oito registros, sem duplicatas exatas, com referências locais existentes; configuração não comprova execução ou trust. Nenhum hook global foi alterado ou disparado pela auditoria.

Somente `supported_adapters: ["local"]` é aceito. O mapa abaixo descreve candidatos para integração futura, **não adapters implementados**. Fontes consultadas em 2026-10-31: [Codex Hooks](https://learn.chatgpt.com/docs/hooks) e [Claude Code Hooks](https://code.claude.com/docs/en/hooks). Verifique versão, trust, payload e modo de orquestração antes de ativar qualquer integração.

| Evento NEXUS | Codex: candidato documentado | Claude Code: candidato documentado | Fallback explícito local |
| --- | --- | --- | --- |
| `session.start` | `SessionStart`, startup | `SessionStart`, startup | Início do workflow |
| `session.resume` | `SessionStart`, resume | `SessionStart`, resume | Retomada com estado verificado |
| `session.end` | `SessionEnd` | `SessionEnd` | Encerramento; crash não garante evento |
| `task.created` | Sem equivalente direto no mapa | `TaskCreated`, se TaskCreate estiver disponível | Após criar tarefa |
| `spec.validated` | Sem equivalente direto | Sem equivalente direto | Após validar spec |
| `plan.ready` | Sem equivalente direto | Sem equivalente direto | Após resolver dependências |
| `task.started` | Sem equivalente direto | Sem equivalente direto | Antes da primeira ação |
| `code.pre_edit` | `PreToolUse`, edição | `PreToolUse`, edição | Antes de editar; shell pode escapar do matcher |
| `code.post_edit` | `PostToolUse`, edição | `PostToolUse`, edição | Após agrupar alterações relacionadas |
| `code.pre_commit` | Sem evento específico | Sem evento específico | Antes de commit autorizado |
| `test.completed` | `PostToolUse`, runner identificado | `PostToolUse`, runner identificado | Wrapper informa término e resultado |
| `review.requested` | Sem equivalente direto | Sem equivalente direto | Seleção de pilares |
| `review.completed` | Sem equivalente direto | Sem equivalente direto | Após receber revisão |
| `task.blocked` | Sem equivalente direto | Sem equivalente direto | Impedimento identificado |
| `task.failed` | Sem equivalente direto | Sem equivalente direto | Falha da tarefa, não de qualquer ferramenta |
| `task.completed` | Sem equivalente direto | `TaskCompleted`, tarefa nativa correspondente | Gate explícito; Stop não comprova conclusão |
| `memory.retrieve` | Sem equivalente direto | Sem equivalente direto | Solicitar IDs pertinentes |
| `memory.capture` | Sem equivalente direto | Sem equivalente direto | Registro autorizado |
| `memory.refresh` | Sem equivalente direto | Sem equivalente direto | Substituição versionada |

Codex não executa hooks locais em todos os modos de orquestração em nuvem. Um evento posterior não desfaz a ação anterior; erros de certos handlers MCP não bloqueiam operações. Exit codes deste CLI precisam de tradução específica para cada contrato nativo. Smoke tests nos hosts permanecem pendentes.

## Contrato e registro

Use `python3 skills/nexus/scripts/hook_engine.py list` para ver contratos expandidos e `python3 skills/nexus/scripts/hook_engine.py validate` para validar o registro.

| Campo obrigatório | Semântica |
| --- | --- |
| `id`, `description` | Identidade única e propósito |
| `event` | Lista de eventos lógicos |
| `trigger_conditions` | `profiles` e `any_flags`; lista vazia dispensa flag |
| `execution_mode` | OBSERVE, ADVISE, ENFORCE ou EXECUTE |
| `priority` | 0–100, menor primeiro; desempate por ID |
| `inputs`, `outputs` | Descrição dos dados; validação real pertence ao schema e handler |
| `timeout` | Segundos, positivo, até 60 por tentativa |
| `retry_policy` | `max_attempts`, 1–3 incluindo a primeira |
| `failure_policy` | `block` em ENFORCE; `warn` nos demais |
| `permissions` | Capacidades externas ao payload, concedidas por `--allow` |
| `enabled` | Booleano; mudança invalida evidências do registro anterior |
| `supported_adapters` | Exclusivamente `local` nesta versão |
| `handler`, `config` | Implementação permitida e configuração estrita |

OBSERVE registra metadados ou recupera memória autorizada. ADVISE retorna recomendação determinística. Ambos são impedidos de executar comandos ou gravar memória. ENFORCE valida e bloqueia o **chamador local**, que precisa respeitar o exit code. EXECUTE permite comando configurado ou memória autorizada. O engine não contorna permissões do host.

| Hooks | Comportamento entregue |
| --- | --- |
| `event.observe` | Observa os 19 eventos |
| `validation.run` | Executa `scripts/validate.py` do workspace com o Python corrente, mediante permissão |
| `completion.verify` | Exige recibos aprovados dos comandos obrigatórios para tarefa/registro/escopo válidos |
| `context.load`, `reuse.scan`, `test.select`, `architecture.guard` | Recomendações de contexto, reutilização, testes e invariantes |
| `lint.check`, `typecheck.run`, `security.scan` | Recomenda configurar as ferramentas reais; não declara checks executados |
| `reasoning.challenge`, `assumptions.validate`, `bias.challenge`, `alternatives.compare`, `hypothesis.falsify`, `complexity.reduce`, `decision.capture` | Perguntas selecionadas por risco, ambiguidade e perfil |
| `model.route`, `budget.check`, `review.dispatch`, `failure.recover` | Orientação de host, orçamento, revisão e recuperação; nenhuma chamada externa |
| `memory.retrieve` | Recuperação apenas dos IDs solicitados no workspace |
| `memory.capture`, `memory.refresh` | Persistência versionada com fonte e comparação da versão esperada |
| `memory.checkpoint` | Gravação explícita em bloqueio/falha/encerramento com flag `checkpoint` |
| `memory.after_completion` | Recomenda captura autorizada após conclusão com flag `decision` |

O registro padrão atende a **este repositório documental**. Em um consumidor, revise uma cópia e passe `--registry`: configure ferramentas reais, suas permissões e `completion.verify.config.required_hooks`. Desativar um check obrigatório não aprova conclusão. Uma recomendação de arquitetura não é um Architecture Gate aprovado; revisão especializada e decisões continuam sob responsabilidade do host/engenheiro.

Comandos usam `argv`, sem shell ou interpolação do payload; `{python}` representa o interpretador corrente. `read_only` é declaração do operador, **não sandbox**: revise scripts e executáveis. `cache_seconds` é opcional, 0–300, default 0, somente para comandos de leitura.

## Perfis e workflow

| Perfil | Seleção | Admissão por evento |
| --- | --- | --- |
| FAST | Essenciais e validação pertinente; sem revisão cognitiva profunda | 10 s |
| BALANCED | Engenharia e memória conforme contexto | 120 s |
| DEEP | Acrescenta alternativas e contestação de viés quando justificadas | 120 s |

Antes de cada hook reserva-se o pior timeout/backoff; se não couber, o evento bloqueia. Built-ins têm inputs limitados e verificam o tempo ao retornar; não interrompem I/O bloqueado no kernel. Comandos têm timeout e limpeza de grupo POSIX. Esses limites não são SLA ou benchmark de produção. Não há LLM, polling contínuo ou servidor.

O caller emite eventos nas transições do [workflow](workflow.md), aplica [políticas](policies.md), consome recomendações [cognitivas](cognitive.md) e seleciona revisões conforme [agentes](agents.md). O executor não encadeia eventos. Não modifica arquivos dessas frentes nem promete sincronização automática com seus workflows.

## Uso real

Use um único banco local compartilhado por todos os callers do workspace, em diretório privado excluído do Git. Neste repositório `.nexus/local/` já é ignorado. `--state` é obrigatório e não há gravação global implícita. Exemplos a partir da raiz do repositório:

```sh
python3 skills/nexus/scripts/hook_engine.py run \
  --workspace "$PWD" --state .nexus/local/hooks.sqlite \
  --allow command:validation.run <<'JSON'
{"event_id":"edit-1","task_id":"example","event":"code.post_edit","profile":"FAST","flags":[],"files":["scripts/validate.py","skills/nexus/SKILL.md","skills/nexus/references/hooks.md"],"inputs":{}}
JSON
python3 skills/nexus/scripts/hook_engine.py run \
  --workspace "$PWD" --state .nexus/local/hooks.sqlite <<'JSON'
{"event_id":"complete-1","task_id":"example","event":"task.completed","profile":"FAST","flags":[],"files":["scripts/validate.py","skills/nexus/SKILL.md","skills/nexus/references/hooks.md"],"inputs":{"evidence":["edit-1"]}}
JSON
```

O exemplo valida o pacote, mas o recibo cobre **somente arquivos declarados**. Para aceite real inclua todos os inputs relevantes: dependências, configuração, scripts e fontes. Arquivos fora da lista e mudanças externas não são detectados automaticamente. Mudanças de ferramentas externas exigem novo registro ou cache desativado. O caller deve determinar esse escopo; o executor não afirma aceite global do projeto.

Caminhos relativos ao workspace; escape por symlink é rejeitado. Ausência é registrada para representar remoções. Limites: 128 arquivos, 2 MiB por arquivo e 16 MiB por snapshot. Gate exige recibos duráveis da mesma tarefa, registro e hash; não aceita um `passed` fornecido pelo caller. Alteração do escopo invalida checks de leitura, inclusive resultados de cache. Comandos mutáveis podem alterar arquivos, mas não geram evidência de validação; faça a verificação posterior em novo evento com snapshot atualizado. Não há importador de recibos externos.

Exit codes: `0` concluído (pode conter avisos), `2` gate bloqueado, `3` erro operacional/contrato ou interrupção. `completed_with_warnings` distingue aviso de conclusão sem ressalvas. Ausência de hooks selecionados não aprova critérios de negócio. Um recibo não concede autorização para commit/deploy.

## Memória autorizada

`--allow memory.read` e `--allow memory.write` são explícitos; payload não concede capacidades. Respeite as instruções do host, inclusive quando gravar memória depender de solicitação do usuário. Não infira consentimento para capturar conversas.

```sh
python3 skills/nexus/scripts/hook_engine.py run \
  --workspace "$PWD" --state .nexus/local/hooks.sqlite --allow memory.write <<'JSON'
{"event_id":"capture-1","task_id":"example","event":"memory.capture","profile":"BALANCED","flags":[],"files":[],"inputs":{"memory":{"id":"example-decision","content":"Exemplo sintético: chamadas explícitas nesta fase.","source":"exemplo local autorizado","expected_version":0}}}
JSON
python3 skills/nexus/scripts/hook_engine.py run \
  --workspace "$PWD" --state .nexus/local/hooks.sqlite --allow memory.read <<'JSON'
{"event_id":"retrieve-1","task_id":"example","event":"memory.retrieve","profile":"FAST","flags":[],"files":[],"inputs":{"memory_ids":["example-decision"]}}
JSON
```

Nova gravação exige versão esperada 0; atualização exige a versão corrente. A transação invalida a anterior e insere a próxima; histórico permanece rastreável. `memory.refresh` usa esse contrato. Checkpoint exige conteúdo, fonte, versão, flag e permissão; não extrai histórico automaticamente. Recuperação é contexto não confiável, sujeito à revalidação de [memória](memory.md). Sem busca semântica, sincronização global, expiração ou remoção automática.

## Concorrência e recuperação

- Um claim durável antes dos efeitos, uma execução ativa por workspace/banco; outros workspaces podem avançar. SQLite usa transações curtas e timeout de lock de 200 ms. Sem fila: `WORKSPACE_BUSY` devolve backpressure.
- ID de evento mais payload/permissões/registro/snapshot iguais devolvem resultado anterior sem repetir efeitos. Mesmo ID com dados diferentes gera `EVENT_CONFLICT`. Use ID estável para entrega duplicada, novo ID para nova operação.
- Replay de memória reconstrói as versões originalmente lidas, inclusive se substituídas depois. O journal armazena referências de versão, não cópia do texto. Uma leitura atual exige novo evento.
- Cache exige tarefa, registro, hash e idade válidos; `checked_at` original não é renovado pelo replay. Escopo vazio não permite cache ou conclusão.
- Comandos de leitura repetem apenas timeout, até três tentativas; falha de validação não recebe retry. Comandos mutáveis têm uma tentativa. Efeito mutável incerto interrompe o evento e mantém o workspace ocupado.
- Três falhas operacionais sem execução bem-sucedida por hook/registro/workspace abrem circuito. Requer diagnóstico e reset explícito; negação de permissão não o reabre. Gate obrigatório nunca recebe fallback de sucesso.
- Recursão interna tem limite zero: não há dispatch pelos handlers, e filhos recebem `NEXUS_HOOK_ACTIVE=1`; CLI aninhado recusa execução. Código arbitrário autorizado pode remover a variável, pois isto não é sandbox para programas hostis.
- SIGINT/SIGTERM limpam o grupo filho e deixam claim para reconciliação. SIGKILL pode deixar órfãos; processos que criem outra sessão escapam da limpeza. Não há replay automático, liberação por TTL ou exactly-once de efeitos externos.

Confira efeitos e encerre órfãos da execução antes de recuperar. Owner ou grupo ainda vivo impedem recuperação. PID reutilizado exige diagnóstico, não matar um processo presumindo sua identidade. Estes comandos abandonam o evento/liberam workspace ou resetam o circuito; não aprovam gates nem repetem efeitos:

```sh
python3 skills/nexus/scripts/hook_engine.py recover \
  --workspace "$PWD" --state .nexus/local/hooks.sqlite \
  --event-id edit-1 --allow state.reconcile --confirmed-effects
python3 skills/nexus/scripts/hook_engine.py reset-circuit \
  --workspace "$PWD" --state .nexus/local/hooks.sqlite \
  --hook-id validation.run --allow state.reconcile --confirmed-effects
```

Use filesystem local. Bancos diferentes removem coordenação/dedup entre callers; NFS e distribuição entre máquinas não são suportados. Não apague o banco para destravar efeito incerto. Não há poda automática de recibos; retenção precisa de política própria.

## Segurança e observabilidade

JSON limitado a 256 KiB, campos desconhecidos/chaves duplicadas/números não finitos rejeitados. IDs, caminhos e configuração são validados. Registro não importa código arbitrário; comandos explicitamente autorizados continuam executando código do operador, sujeito às permissões do host.

O filho recebe somente PATH, LANG e marcadores internos, sem tokens herdados. stdin fechado, stdout/stderr descartados. Erros usam códigos estáveis, sem traceback/credenciais. Memória é conteúdo explícito em banco privado sem criptografia: não envie segredos. Seu conteúdo não é sanitizado semanticamente; não existe detector universal de segredos.

Por hook: `hook_id`, `event_id`, `task_id`, `execution_id`, `status`, `duration_ms`, `execution_mode`, `error_code`, `attempts`, `checked_at`, `model_usage`, `gate_impact`. Duração usa relógio monotônico; `model_usage: null` indica ausência de chamada de modelo, sem estimar tokens/preços. O journal exclui payload e texto recuperado; saída de leitura explícita pode conter o conteúdo autorizado.

`failed` é verificação rejeitada; `error`, falha operacional/contrato; `advised`, recomendação; `observed`, observação. Crash antes da finalização pode deixar claim sem resultado final por hook. `IN_PROGRESS`, `WORKSPACE_BUSY`, `CIRCUIT_OPEN` e `UNCERTAIN_EFFECT` exigem tratamento, não são sucesso.

## Validação e pendências

Na raiz: `python3 -m unittest discover -s tests -v` e `python3 scripts/validate.py`. Testes usam processos reais para duplicação concorrente, timeout, cancelamento, crash e recuperação; também cobrem memória, cache, permissões e evidências obsoletas. Não validam hooks nativos ou qualidade do raciocínio de agentes.

Pendentes: adapters nativos e smoke tests nos hosts, Windows, configuração de ferramentas dos consumidores, Architecture Gate especializado, revisão cognitiva por modelo e retenção. Sem scheduler, dashboard, daemon ou deploy.
