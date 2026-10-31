# Workflow adaptativo e retomável

Conduza DISCOVERY → SPEC → PLAN → TASKS → EXECUTION → TESTING → REVIEW → DELIVERY → MEMORY proporcionalmente ao trabalho. O [executor local](../scripts/workflow.py) persiste tarefas e aplica gates; o agente e as ferramentas do host realizam implementação, testes e dispatch. Para comandos e garantias, leia o [contrato do Todo](workflow-state.md).

## Modos de profundidade

| Modo | Aplicação | Caminho e gates |
| --- | --- | --- |
| FAST | Correção pequena, reversível, com aceite claro | Objetivo → task enxuta → implementar → verificar → entregar; sem SPEC/PLAN extensos |
| BALANCED | Feature ou refatoração usual | Discovery → SPEC compacta → PLAN incremental → tasks → execução → testes adaptativos → review seletivo → entrega |
| DEEP | Arquitetura, contrato crítico ou baixa reversibilidade | Discovery → SPEC → alternativas → Architecture Gate → PLAN/DAG → execução coordenada → testes aprofundados → Review Council pertinente → entrega e decisão de memória |

Escolha por risco e incerteza reais. Uma mudança pequena com invariante crítica ainda exige gates críticos. `mode` registra mudança de profundidade com justificativa em checkpoint sem worker ativo. Não permite reduzir `risk=critical` nem remover review já solicitado. Revalide os novos gates antes de continuar.

Explore, Plan, Build e Review continuam sendo intenções: Explore cobre discovery; Plan produz SPEC/PLAN/TASKS; Build cobre execução e testes; Review avalia implementação e evidências. **Autonomous é política de continuidade**, combinável com qualquer profundidade; não é permissão adicional nem scheduler instalado.

## Contratos e decomposição

- **SPEC** define resultado, invariantes e critérios de aceite; nunca é executada como código.
- **PLAN** define sequência, dependências, estratégia e recuperação, vinculadas à revisão e ao hash da SPEC.
- **TASKS** são unidades executáveis com ID estável, objetivo, ownership, dependências e aceite observável. Complexidade é opcional; evite fragmentar mudanças triviais.
- **REVIEW** avalia o resultado; **EVIDENCE** atribui comando/observação, resultado, fonte e data à geração atual da tarefa.

Use os templates existentes: [spec](../assets/templates/spec.md), [plano](../assets/templates/plan.md), [tarefa](../assets/templates/task.md), [ADR](../assets/templates/adr.md). A CLI `template` os exporta sem modificar os originais. No consumidor, mantenha artefatos compartilháveis em `docs/nexus/specs/`, `plans/`, `tasks/` e `decisions/`, criando somente diretórios usados. Estado e recibos privados ficam em `.nexus/local/`, excluído do Git antes do uso.

Registre SPEC/PLAN como `artifact` após a aceitação necessária no host. O executor detecta conteúdo alterado fora do registro. Uma mudança material invalida tarefas e provas anteriores; atualize PLAN para a nova SPEC e execute `reconcile` nas tarefas afetadas. `amend` exige motivo para alterar aceite, responsável, arquivos ou estratégia. Histórico preserva as versões; não reescreva critérios silenciosamente.

## Execução, Todo e paralelismo

Estados: `pending`, `ready`, `running`, `validating`, `blocked`, `done`, `cancelled`. `validating` acrescenta uma fronteira explícita para testes/review aos estados anteriores. Cada operação aceita produz snapshot e histórico na mesma transação.

`ready` exige dependências `done`, contratos atuais, autorização atribuída e gates anteriores à execução. `start`/`dispatch` também verificam budget conhecido, tentativas, concorrência e recursos. Dependência inexistente ou cíclica falha sem mutação. Cancelar predecessor não satisfaz dependências.

Declare arquivos/diretórios, bancos, portas e recursos compartilhados com nomes comuns entre agentes. Execute em paralelo apenas tarefas independentes e com recursos disjuntos. Reservas duram pela implementação **e validação**. Worktrees não isolam bancos, portas ou serviços externos. O executor coordena um único estado local; não detecta outros workflows, checkouts ou ferramentas que ignorem esse contrato.

A fonte de verdade é o store JSON. `show` projeta o Todo em Markdown; `show --format json` permite outro adapter. Pela CLI é possível criar, atualizar, reatribuir, bloquear, adicionar dependências, vincular arquivos, solicitar review, retomar, concluir e consultar histórico. Markdown é uma projeção atualizável, sem botões ou sincronização bidirecional. Um Todo nativo, quando realmente disponível, deve traduzir ações para o mesmo contrato; não manter segundo estado independente.

## Testes adaptativos e gates

Registre `strategy.kind` e `strategy.reason` na task, seguindo [políticas](policies.md).

| Situação | Estratégia | Evidência |
| --- | --- | --- |
| Domínio, invariantes, algoritmo crítico ou regressão definida | `tdd` | Falha esperada observada antes de start; teste passando após implementação |
| Feature convencional ou visual de baixo risco | `test-after` | Verificação proporcional após implementação |
| Legado pouco documentado | `characterization` | Caracterização antes de mudar e comparação posterior |
| API, persistência ou fronteira externa | `integration-contract` | Contratos, falhas relevantes e recuperação testados |
| Texto ou ajuste reversível sem lógica | `inspection` | Inspeção/validação estrutural ou visual pertinente, registrada como verificação |

Para DEEP ou task crítica, registre Architecture Gate: boundaries, contratos, alternativas, riscos, reversibilidade e ADR quando necessário. O executor exige recibo; o agente/revisor avalia seu conteúdo. Para review, selecione pilares conforme [agentes](agents.md), solicite-os com `request_review` e registre retornos com `review`. Review Council não exige um agente por pilar. Declare quando a independência não existir.

`complete` exige resultado de implementação reconciliado, última verificação aprovada, todos os aceites evidenciados, reviews solicitados respondidos e nenhum achado critical/high aberto. IDs de achados são únicos na task; use prefixos por revisor. Alterar implementação após review exige `rework`, nova validação e resolução com fonte; provas de gerações antigas não fecham a nova tarefa. `deliver` revalida todas as tasks e contratos e registra decisão de memória. Falha nunca vira sucesso aparente.

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
