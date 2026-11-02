# Contrato executável do Todo — versão 1

Leia somente ao adotar, operar ou integrar o executor opt-in do [workflow](workflow.md); execução direta e acompanhamento nativo não exigem esta CLI. Requer Python 3.10+ e filesystem local POSIX com `flock`, `fsync` e rename atômico; o store não usa dependências externas, servidor ou banco. A integração opt-in de recibos lê o journal SQLite local dos hooks. Este componente não contém scheduler, SDK de provider ou adapter nativo de Todo. O executor opcional de hooks e o runtime textual de agentes são componentes separados, sem acionamento automático pelo workflow.

## Profundidade no executor

A escolha documental entre execução direta e rastreada não cria enum, campo ou estado no store. Ao adotar esta CLI, o contrato existente continua obrigatório: BALANCED exige discovery, SPEC e PLAN; DEEP acrescenta alternativas, decisão e Architecture Gate. FAST continua restrito ao baixo risco; não o selecione para evitar gates de BALANCED/DEEP. `mode` registra mudança justificada em checkpoint sem worker ativo, sem reduzir `risk=critical` nem remover review solicitado; revalide gates antes de continuar.

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

## Contratos e decomposição

- **SPEC** define resultado, invariantes e critérios de aceite; nunca é executada como código.
- **PLAN** define sequência, dependências, estratégia e recuperação, vinculadas à revisão e ao hash da SPEC.
- **TASKS** são unidades executáveis com ID estável, objetivo, ownership, dependências e aceite observável. Complexidade é opcional; evite fragmentar mudanças triviais.
- **REVIEW** avalia o resultado; **EVIDENCE** atribui comando/observação, resultado, fonte e data à geração atual da tarefa.

Use os templates existentes: [spec](../assets/templates/spec.md), [plano](../assets/templates/plan.md), [tarefa](../assets/templates/task.md), [ADR](../assets/templates/adr.md). A CLI `template` os exporta sem modificar os originais. No consumidor, mantenha artefatos compartilháveis em `docs/nexus/specs/`, `plans/`, `tasks/` e `decisions/`, criando somente diretórios usados. Estado e recibos privados ficam em `.nexus/local/`, excluído do Git antes do uso.

Registre SPEC/PLAN como `artifact` após a aceitação necessária no host. O executor detecta conteúdo alterado fora do registro. Uma mudança material invalida tarefas e provas anteriores; atualize PLAN para a nova SPEC e execute `reconcile` nas tarefas afetadas. `amend` exige motivo para alterar aceite, responsável, arquivos ou estratégia. Histórico preserva as versões; não reescreva critérios silenciosamente.

## Execução, Todo e paralelismo

Com executor opt-in, estados: `pending`, `ready`, `running`, `validating`, `blocked`, `done`, `cancelled`. `validating` acrescenta uma fronteira explícita para testes/review aos estados anteriores. Cada operação aceita produz snapshot e histórico na mesma transação.

`ready` exige dependências `done`, contratos atuais, autorização atribuída e gates anteriores à execução. `start`/`dispatch` também verificam budget conhecido, tentativas, concorrência e recursos. Dependência inexistente ou cíclica falha sem mutação. Cancelar predecessor não satisfaz dependências.

Declare arquivos/diretórios, bancos, portas e recursos compartilhados com nomes comuns entre agentes. Execute em paralelo apenas tarefas independentes e com recursos disjuntos. Reservas duram pela implementação **e validação**. Worktrees não isolam bancos, portas ou serviços externos. O executor coordena um único estado local; não detecta outros workflows, checkouts ou ferramentas que ignorem esse contrato.

Ao usar o executor opt-in, a fonte de verdade é o store JSON. A alternativa documental rastreada segue o [contrato dos templates](../assets/templates/contracts.md), com seis estados e serialização manual; a validação fica dentro de `running`. Execução direta não adota esse contrato. Não há migração ou sincronização automática entre esses modos. `show` projeta o Todo em Markdown; `show --format json` permite outro adapter. Pela CLI é possível criar, atualizar, reatribuir, bloquear, adicionar dependências, vincular arquivos, solicitar review, retomar, concluir e consultar histórico. Markdown é uma projeção atualizável, sem botões ou sincronização bidirecional. Um Todo nativo, quando realmente disponível, deve traduzir ações para o mesmo contrato; não manter segundo estado independente.

## Testes adaptativos e gates

No executor, registre `strategy.kind` e `strategy.reason` na task, seguindo [políticas](policies.md#policy-testing).

| Situação | Estratégia | Evidência |
| --- | --- | --- |
| Domínio, invariantes, algoritmo crítico ou regressão definida | `tdd` | Falha esperada observada antes de start; teste passando após implementação |
| Feature convencional ou visual de baixo risco | `test-after` | Verificação proporcional após implementação |
| Legado pouco documentado | `characterization` | Caracterização antes de mudar e comparação posterior |
| API, persistência ou fronteira externa | `integration-contract` | Contratos, falhas relevantes e recuperação testados |
| Texto ou ajuste reversível sem lógica | `inspection` | Inspeção/validação estrutural ou visual pertinente, registrada como verificação |

Para DEEP ou task crítica, registre Architecture Gate: boundaries, contratos, alternativas, riscos, reversibilidade e ADR quando necessário. O executor exige recibo; o agente/revisor avalia seu conteúdo. Para review, selecione pilares conforme [agentes](agents.md), solicite-os com `request_review` e registre retornos com `review`. Review Council não exige um agente por pilar. Declare quando a independência não existir.

`complete` exige resultado de implementação reconciliado, última verificação aprovada, todos os aceites evidenciados, reviews solicitados respondidos e nenhum achado critical/high aberto. IDs de achados são únicos na task; use prefixos por revisor. Alterar implementação após review exige `rework`, nova validação e resolução com fonte; provas de gerações antigas não fecham a nova tarefa. Evidência declarada ou recibo já válido não exige repetir o comando só por mudar de etapa: confirme mesmos inputs, revisão, configuração, run, geração e ambiente aplicáveis. Isso não muda importação, cache, validade nem revalidação dos gates. `deliver` revalida todas as tasks e contratos e registra decisão de memória. Falha nunca vira sucesso aparente.

## Dispatch e execução persistente

1. Identifique capacidades e consulte ferramentas/agentes realmente disponíveis no host.
2. Registre disponibilidade e proveniência com `register`; selecione provider/modelo/esforço conforme política do usuário. Dados desconhecidos ficam null.
3. `dispatch` prepara Context Pack mínimo e run.id, reservando recursos. Isso ainda não aciona agente.
4. Use a ferramenta real do host para despachar. Inclua objetivo, contratos, ownership, restrições e instrução de preservar trabalho alheio. `ack` grava handle/recibo retornado.
5. Colete resultado com `result`; execute testes, solicite review pertinente, registre evidências e conclua.

Se provider falhar antes do dispatch, registre `block` e próxima ação. Se o resultado da chamada for incerto, mantenha reserva e reconcilie com o host; não redispare por timeout. Fallback exige disponibilidade verificada e roteamento autorizado, nunca simulação de troca de modelo.

Em Autonomous, continue apenas enquanto houver próxima ação autorizada, insumos suficientes e progresso verificável. Pare no limite de tentativas, budget conhecido esgotado, duas falhas sem progresso, ausência de autorização, operação externa incerta ou risco que invalide o plano. Corrija ambiente/contexto antes de escalar. Continue tarefas independentes quando seguro; não faça polling infinito nem invente orçamento.

## Checkpoint, cancelamento e retomada

Ao retomar, leia estado, histórico, fontes atuais e status real do host. `checkpoint` registra próxima ação e fonte; não prova efeito externo concluído. Repetir **o mesmo payload com o mesmo operation_id** é idempotente no store; não torna idempotente a operação externa.

`interrupt` mantém reserva de run incerto. `reconcile_run` exige fonte que confirme stopped ou completed. Só então retome a etapa pendente ou valide trabalho já feito. Recibos de runs antigos são rejeitados. Após duas falhas, `recover` exige diagnóstico, hipóteses descartadas, evidência e próxima ação; não zera o limite total de tentativas.

`cancel` de run ativo é solicitação: pare-o pelas ferramentas do host e confirme via `reconcile_run`. Cancelamento não desfaz arquivos, processos ou efeitos remotos. Workflow com tasks canceladas não recebe delivered; reporte escopo incompleto e, se autorizado, inicie outro workflow com escopo revisado.

Registre memória duradoura apenas quando autorizada e útil, seguindo [memória](memory.md). memory=not-needed ou not-authorized fecha essa decisão sem gravar memória global. Métricas derivam de timestamps/recibos; medido e estimado permanecem separados. Medição indisponível é null, nunca zero fictício.

## Demonstração executável

Execute em um **novo** diretório; a demonstração recusa sobrescrita:

```sh
python3 skills/nexus/scripts/workflow.py demo --output-dir /tmp/nexus-workflow-demo
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
```

O demo BALANCED produz discovery/SPEC/PLAN, cria task TDD, executa testes reais que falham, implementa função sintética, executa testes que passam e persiste evidências, review declarado como autoinspeção, entrega e decisão de memória. Salva report.json, todo.md, logs sanitizados e estado local. Não chama LLM/provider e não demonstra review independente. Veja [demo.py](../scripts/nexus_workflow/demo.py); cenários e limites observados estão na documentação de validação do repositório.
