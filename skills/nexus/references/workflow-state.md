# Contrato executável do Todo — versão 1

Leia ao operar ou integrar o [workflow](workflow.md). Requer Python 3.10+ e filesystem local POSIX com `flock`, `fsync` e rename atômico; o store não usa dependências externas, servidor ou banco. A integração opt-in de recibos lê o journal SQLite local dos hooks. Este componente não contém scheduler, SDK de provider ou adapter nativo de Todo. O executor opcional de hooks e o runtime textual de agentes são componentes separados, sem acionamento automático pelo workflow.

## Camadas

| Componente | Fonte | Responsabilidade |
| --- | --- | --- |
| Task State Store | [store.py](../scripts/nexus_workflow/store.py) | Lock limitado, leitura, snapshot atômico e durabilidade |
| Task Orchestrator | [orchestrator.py](../scripts/nexus_workflow/orchestrator.py) | DAG, transições, autorização atribuída, reservas, gates e histórico |
| Task Presentation Adapter | [cli.py](../scripts/nexus_workflow/cli.py), [presentation.py](../scripts/nexus_workflow/presentation.py) | Comandos JSON, projeção Markdown, métricas e exportação de templates |

O store nunca executa shell fornecido em requests. Os campos source, autorização e evidências são recibos atribuídos pelo operador/host, não provas criptográficas nem um sistema de ACL. A importação opcional verifica consistência com o journal local; quem controla o journal ainda pode adulterá-lo. As regras de autorização efetiva continuam no host.

## Usar no projeto consumidor

Mantenha o pacote `skills/nexus/` completo. Os comandos abaixo partem da raiz que contém o pacote; no consumidor, use o caminho real da skill. Exclua `.nexus/local/` do Git antes de gravar dados privados. A CLI não modifica `.gitignore` nem configurações globais automaticamente.

```sh
python3 skills/nexus/scripts/workflow.py init --workspace . --mode FAST
python3 skills/nexus/scripts/workflow.py apply --request - <<'JSON'
{
  "operation_id": "create-T1",
  "expected_revision": 0,
  "action": "create",
  "task_id": "T1",
  "title": "Corrigir normalização do rótulo",
  "goal": "Remover espaços periféricos do rótulo",
  "criteria": ["Entrada com espaços produz rótulo normalizado"],
  "owner": "main",
  "role": "implementer",
  "resources": ["file:src/label.py"],
  "files": ["src/label.py"],
  "authorization": "Pedido do usuário no chat atual",
  "strategy": {"kind": "test-after", "reason": "Ajuste pequeno com regressão direta"}
}
JSON
python3 skills/nexus/scripts/workflow.py show
python3 skills/nexus/scripts/workflow.py show --format json
python3 skills/nexus/scripts/workflow.py history --task T1
python3 skills/nexus/scripts/workflow.py metrics
python3 skills/nexus/scripts/workflow.py template task
```

`--state CAMINHO` é opção global, antes do subcomando; padrão `.nexus/local/workflow.json` relativo ao diretório atual. `--workspace` define a raiz de artefatos/recursos. O JSON registra raiz absoluta; copiar estado para outro projeto não é migração suportada. `init` rejeita sobrescrita. Limites locais iniciais: `--max-running 1` task reservada e `--max-attempts 3` por task; ajuste explicitamente na inicialização. Budget monetário/tokens não é presumido.

Cada alteração usa operation_id único e expected_revision lido do estado. Em conflito, releia e reavalie a intenção antes de usar nova revisão. Replay idêntico do mesmo ID não acrescenta histórico nem incrementa revisão; reutilizar ID com payload diferente é erro. Resposta ao replay contém a revisão **atual**, não uma cópia antiga. ID tem até 128 caracteres alfanuméricos, `_`, `.`, `:`, `-`, começando por alfanumérico.

Sucesso usa JSON/exit 0. Erros usam stderr/exit 2. Requests inválidos são rejeitados sem mutação; falhas reais do trabalho devem ser registradas por `result(failure)` ou `block`, não inferidas de comando inválido.

## Envelope e operações

Todas as operações aceitam operation_id, expected_revision, action; campos desconhecidos são rejeitados. task_id identifica task existente, exceto em create. source é proveniência concreta; reason explica a decisão, sem transcrições privadas.

| action | Campos específicos | Efeito / condições |
| --- | --- | --- |
| `create` | task_id,title,goal,criteria,owner,role,resources,authorization,strategy; opcionais priority,depends_on,files,risk,review_required,complexity,evidence_policy | Cria pending; priority 0–3 (0 mais alta), risk low/normal/critical; sem heurística opaca de atribuição |
| `amend` | task_id,reason; um ou mais de title,goal,criteria,owner,role,priority,resources,files,strategy,authorization,evidence_policy | Reatribui/vincula/edita, invalida provas e retorna a pending; exige run encerrado |
| `depend` | task_id,dependency | Adiciona aresta; rejeita ID ausente, duplicata e ciclo |
| `artifact` | kind,path,revision,source,reason | kind discovery/spec/plan/alternatives/decision/delivery/memory; caminho confinado ao workspace, SHA-256; PLAN vincula SPEC atual |
| `reconcile` | task_id,reason | Aceita revisões de contratos após inspeção; invalida provas anteriores |
| `mode` | mode,reason | FAST/BALANCED/DEEP; não troca com run ativo |
| `ready` | task_id | Valida dependências, contratos e gates anteriores à execução |
| `start` | task_id | Reserva e inicia tentativa executada pelo agente principal no host |
| `register` | agent_id,capabilities,available,source; opcionais provider,model,effort | Snapshot de capacidades verificadas no host; não instala nem descobre providers sozinho |
| `dispatch` | task_id,agent_id,capabilities,route_source | Prepara handoff, Context Pack e run; não chama provider |
| `ack` | task_id,run_id,handle,source | Confirma recibo real do host; ainda não confirma resultado |
| `result` | task_id,run_id,outcome,source,summary | success → validating com reserva; failure → blocked com erro registrado e reserva liberada |
| `evidence` | task_id,kind,outcome,source,detail; criteria para aceite | kind architecture/red/test/acceptance; outcome passed/failed; criteria são índices base zero; data automática e geração atual |
| `import_receipt` | task_id,event_id,source | Apenas validating com policy hook_receipts; lê evento exato do journal e acrescenta evidência test passed com identidade/snapshot verificados |
| `request_review` | task_id,reviewer,pillars,source | Registra pedido por pilar; o host aciona o revisor; reserva continua |
| `review` | task_id,reviewer,source,findings; request_id para pedido existente; reviewer_handle opcional ou obrigatório pela policy | findings lista de objetos id,severity,detail, podendo ser vazia; severity critical/high/medium/low |
| `resolve` | task_id,finding_id,source | Resolução explícita com evidência; não sobrescreve finding por colisão de ID |
| `complete` | task_id | Só de validating; verifica aceite, testes, contratos, gates e achados; libera reserva |
| `rework` | task_id,reason | Invalida tarefa e dependentes transitivos, inclusive done; rejeita se algum tiver run ativo |
| `block` | task_id,reason,next_action | Bloqueio sem run ativo; durante validação mantém reserva |
| `resume` | task_id,reason | blocked → pending; resultado externo já precisa estar reconciliado |
| `recover` | task_id,diagnosis,discarded,source,next_action | Recupera blocked com diagnóstico; discarded é lista não vazia; mantém total de tentativas |
| `interrupt` | task_id,reason | Bloqueia run incerto, conservando reserva |
| `reconcile_run` | task_id,run_id,outcome,source,next_action | outcome stopped/completed confirmado no host; completed → validating, salvo cancelamento solicitado |
| `cancel` | task_id,reason | Sem run ativo → cancelled; com run ativo solicita parada e mantém reserva |
| `checkpoint` | task_id,next_action,source | Próxima ação sem presumir efeito externo concluído |
| `budget` | limit,unit,source | Limite explicitamente autorizado; alteração somente sem run ativo |
| `meter` | kind,value,unit,source | Totais acumulados actual/estimate separados; actual não pode diminuir |
| `deliver` | source,memory,reason | Todas tasks done e gates atuais; memory captured/not-needed/not-authorized; captured exige artifact memory |

O snapshot inclui schema_version, ID do workflow, revisão, workspace, modo, limites, artefatos, tasks, registry, budget, medições, histórico e entrega. Task contém status, prioridade, dependências, owner/papel, run/agente/modelo, reserva, critérios, estratégia, geração de evidências, bloqueio, próxima ação e timestamps. run.id muda por tentativa; não use task_id como ID de execução externa.

resources usa namespaces: `file:src/a.py`, `dir:src`, `port:8080`, `db:integration`. Arquivos/diretórios resolvem symlinks dentro do workspace e conflitam por ancestralidade, incluindo `dir:.`; comparação de case é conservadora. Recursos não-arquivo conflitam por nome exato. A reserva não é sandbox de filesystem e não intercepta ferramentas externas. files vincula referências ao Context Pack; não substitui declarar recursos exclusivos.

## Integração opt-in de recibos e revisão independente

Sem `evidence_policy`, o contrato anterior de evidências declaradas permanece válido, inclusive para snapshots schema_version 1 já existentes. Não é necessário migrá-los. `evidence_policy` aceita somente `hook_receipts` e `independent_review`; ambos são opcionais. `{}` desativa essas exigências por decisão explícita. Alterar a policy com `amend` invalida a geração, assim como alterar critérios ou arquivos.

Exemplo completo de policy aplicada a uma task existente, antes de iniciar nova tentativa. Substitua `expected_revision` pela revisão atual em cada operação:

```json
{
  "operation_id": "require-checks-T1",
  "expected_revision": 1,
  "action": "amend",
  "task_id": "T1",
  "reason": "Exigir checks locais verificáveis e revisão declarada independente",
  "files": ["src/label.py", "tests/test_label.py"],
  "evidence_policy": {
    "hook_receipts": {
      "journal": ".nexus/local/hooks.sqlite",
      "registry": ".nexus/hooks.json",
      "event": "test.completed",
      "required_hooks": ["tests"]
    },
    "independent_review": true
  }
}
```

Os caminhos `journal` e `registry` são normalizados, relativos e confinados ao workspace; não aceitam caminhos absolutos, `..`, symlink final ou resolução para fora da raiz. O registry deve obedecer ao contrato dos [hooks](hooks.md). Cada ID exigido deve identificar hook habilitado, `handler: command`, `config.read_only: true` e evento compatível. O workflow não executa esses comandos nem confirma a declaração `read_only` por sandbox. Execute os hooks explicitamente no host, durante a tentativa atual, com mesmo task_id, workspace, registry e lista **exata** de task.files. `files` precisa conter 1–128 entradas; inclua código, testes e demais inputs relevantes, pois arquivos omitidos não participam da prova. A semântica de snapshot dos hooks inclui bytes, bits executáveis e marcador para arquivos ausentes, com limites de 2 MiB por arquivo e 16 MiB totais.

Após `result(success)`, importe o evento exato pelo mesmo comando `apply --request` usado para as outras operações:

```json
{
  "operation_id": "import-checks-T1",
  "expected_revision": 5,
  "action": "import_receipt",
  "task_id": "T1",
  "event_id": "checks-T1-attempt-1",
  "source": "Execução explícita dos hooks locais nesta tentativa"
}
```

A importação consulta somente a linha `(workspace,event_id)` em journal existente, aberto `mode=ro` e `query_only`, sem criar banco ou recuperar logs. Exige evento finalizado com gate pass, task/event corretos, digest do registry atual, snapshot atual não vazio e todos os hooks exigidos com status passed, identidade de execução e `checked_at` igual ou posterior ao início do run atual. Checks em cache anteriores à tentativa são rejeitados mesmo quando reutilizados em novo evento. O recibo é vinculado à geração e ao run; um evento anterior ao rework não valida outra tentativa. Os timestamps dependem do relógio e journal locais, sem autenticação externa.

`complete` e `deliver` releem o evento e revalidam identidade, registry e arquivos. O último teste da geração precisa ser um recibo importado; acrescentar `evidence(test,passed)` declarado não contorna a policy. Aceite por critério continua explícito via `evidence(acceptance,...)`, pois saída zero de um comando não demonstra todos os critérios. Após mudança de arquivos, registry ou remoção do journal, execute checks e importe novo recibo. Se a task já estiver done, use `rework` antes de repetir. Replay idêntico do mesmo operation_id mantém a semântica idempotente e não relê fontes; os gates finais sempre as revalidam.

`independent_review: true` exige pelo menos um review da geração atual, com `reviewer`, `reviewer_handle` e `source` não vazios. Exemplo após validação:

```json
{
  "operation_id": "review-T1",
  "expected_revision": 7,
  "action": "review",
  "task_id": "T1",
  "reviewer": "quality-reviewer",
  "reviewer_handle": "host-review-run-123",
  "source": "Recibo do revisor retornado pelo host",
  "findings": []
}
```

O helper rejeita reviewer ou handle iguais ao owner, ID de agente implementador ou handle do run, ignorando caixa e espaços periféricos. Essa comparação verifica identidades **declaradas**: não autentica pessoas/agentes nem detecta aliases. Não exige diferença de provider ou modelo; o host continua responsável por obter revisão independente real e por autorizar seu acionamento.

O bridge limita o JSON importado a 256 KiB, hooks a 64, espera de lock SQLite a 200 ms e consulta com orçamento cooperativo de 250 ms; falhas, journal ocupado/corrompido e recibos inválidos não alteram o estado. Não copia outputs de hooks ou conteúdo de memória. O lock do workflow conserva CAS/idempotência; não há transação distribuída com o journal ou editores externos. A revalidação detecta alterações observáveis até a leitura final, sem impedir alterações concorrentes posteriores. Preserve exclusividade dos inputs durante validação e entrega no host.

## Durabilidade e recuperação

O lock é arquivo estável separado do snapshot, com espera máxima de 2 s. A transação lê revisão, aplica operação, valida DAG e grava estado+histórico em temporário no mesmo diretório; executa fsync, rename atômico e fsync do diretório. Falha anterior ao rename preserva snapshot antigo. Falha posterior ao rename é **resultado incerto**: consulte histórico pelo operation_id antes de repetir. Lock de processo é liberado pelo SO ao encerrar; nunca apague o arquivo de lock para “desbloquear”.

Estado ilegível ou versão incompatível falha fechado. Não há reset automático, importação de Markdown, migração de schema, backup automático ou replay de efeitos externos. Preserve snapshot para diagnóstico; restauração precisa de cópia confiável e reconciliação com o host. Histórico não é inviolável: quem pode editar o JSON pode adulterá-lo.

Não suporte NFS, sincronização por cloud drive, hosts distribuídos ou Windows com este store. Um estado possui um workspace; múltiplos estados não compartilham locks de recursos. Para agentes em worktrees distintos que alteram recurso lógico comum, use coordenador e nomes comuns de recurso, verificando isolamento efetivo no host.

## Custo, latência e limites

Operações não dependem de rede/modelo. Validação do DAG é O(tasks + arestas); detecção de conflitos compara reservas ativas. Cada mutação reescreve snapshot e histórico integralmente sob lock, com fsync. Isso privilegia auditabilidade e recuperação para workflows locais pequenos, não throughput de fila de jobs. Não há benchmark de capacidade nem garantia de latência; não use como scheduler de alto volume.

Budget interrompe novos starts quando o último total medido atinge limite; sem medição real da unidade, não inicia. Estimativas não substituem medições. Este gate **não garante teto financeiro**: consumo entre medições, chamada em andamento, cancelamento do provider e autorização de gastos dependem do host. Não repita chamadas só para descobrir consumo. Timestamps/usage exibem origem; dados desconhecidos ficam null.

metrics fornece conclusão por quantidade de tasks, lead/cycle em segundos, falhas registradas, tentativas adicionais, reworks explícitos, recibos de testes/review e totais actual/estimate por unidade. Cycle inclui espera e retrabalho; não é CPU time. Evidência de teste é recibo, não contagem de assertions nem medição de cobertura.

## Demonstração executável

Execute em um **novo** diretório; a demonstração recusa sobrescrita:

```sh
python3 skills/nexus/scripts/workflow.py demo --output-dir /tmp/nexus-workflow-demo
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
```

O demo BALANCED produz discovery/SPEC/PLAN, cria task TDD, executa testes reais que falham, implementa função sintética, executa testes que passam e persiste evidências, review declarado como autoinspeção, entrega e decisão de memória. Salva report.json, todo.md, logs sanitizados e estado local. Não chama LLM/provider e não demonstra review independente. Veja [demo.py](../scripts/nexus_workflow/demo.py); cenários e limites observados estão na documentação de validação do repositório.
