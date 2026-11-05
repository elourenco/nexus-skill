# Workflow adaptativo e retomável

Escolha profundidade pelo contrato mínimo; consulte [Policies](policies.md#policy-execution) quando a classificação precisar de detalhe. Links do executor só são necessários quando a CLI for adotada, não por aparecerem nesta referência. FAST, BALANCED e DEEP não determinam se haverá arquivos ou estado persistido. Explore, Plan, Build e Review são atividades; Autonomous é continuidade na autorização existente, sem permissão adicional ou scheduler.

## Modos de profundidade

| Perfil | Foco |
| --- | --- |
| FAST | Escopo conhecido, baixo risco e reversão simples; implementação, diff e verificação pertinentes |
| BALANCED | Decisões, contratos e falhas de uma alteração moderada; plano curto quando necessário |
| DEEP | Invariantes críticas, compatibilidade, recuperação, testes aprofundados e revisão independente exigida |

Escolha separadamente como acompanhar a entrega:

- **Direta:** objetivo, decisões, diff e evidências no chat bastam. Não exige TASK, SPEC, PLAN, inicialização de store ou transições de estado. Gates de risco, testes, review e conclusão continuam obrigatórios, inclusive em BALANCED/DEEP.
- **Rastreada:** use a fonte existente (plano, issue, todo do host ou registro documental). Crie persistência somente quando útil à coordenação/retomada ou solicitada. Adote os [templates](../assets/templates/contracts.md) apenas se precisar desse formato; não replique uma fonte suficiente.

Esta escolha é orientação documental, sem novo enum/schema/estado. O [executor local opt-in](workflow-state.md) conserva seu contrato: BALANCED exige discovery/SPEC/PLAN; DEEP acrescenta seus gates. Não use FAST para contornar risco ou exigências do executor.

## Contratos e decomposição

Plano aprovado e fontes atuais suficientes conduzem à próxima pendência autorizada; não reinicie brainstorming ou planejamento sem nova evidência ou mudança material. Divida por entrega verificável, ownership e dependências reais. Agrupe edições relacionadas em um incremento revisável antes dos checks; preserve pontos intermediários exigidos por TDD, caracterização ou risco.

No acompanhamento documental adotado, [SPEC/PLAN/TASK e referências](../assets/templates/contracts.md) preservam origem e revisão. Para registro de artefatos e reconciliação na CLI, consulte [contratos e decomposição](workflow-state.md#contratos-e-decomposição).

## Execução, Todo e paralelismo

Uma única fonte é autoridade; sem persistência, o relato no chat não é estado salvo. Ao adotar a CLI, JSON é autoridade e Markdown é projeção, sem sincronização automática. Na adoção documental dos templates, TASKS são autoridade; um todo nativo existente conserva seu próprio contrato. Delegue entregas delimitadas, com ownership e recursos isolados; worktrees não isolam bancos ou portas. [Estados, reservas e gates da CLI](workflow-state.md#execução-todo-e-paralelismo).

## Testes adaptativos e gates

Aplique [testes proporcionais](policies.md#policy-testing) e [review pertinente](review-criteria.md#review-council-adaptativo). Reutilize evidência somente quando inputs, revisão, configuração, run/geração aplicáveis e ambiente permanecerem válidos; não execute duas vezes o mesmo check válido só por atravessar uma etapa. Mudança relevante invalida a cobertura afetada; check obrigatório ausente impede conclusão. O executor preserva recibos, gerações e revalidação de `complete`/`deliver`: [gates executáveis](workflow-state.md#testes-adaptativos-e-gates).

Critérios pertinentes de [segurança e ética](policies.md#policy-ai-safety-ethics)
entram no aceite/risco/evidência existentes. A aplicação é responsabilidade do
agente e revisor: o executor não interpreta requisitos éticos em prosa nem instala
controles de produto. Preserve enums e schemas; registre bloqueio somente da ação
dependente de controle indispensável. Concluir análise não aprova o objeto analisado.

## Dispatch e execução persistente

O agente atual é padrão; delegação depende de benefício, capacidades e autorização do host. A CLI não despacha providers: [registro, dispatch, ack e resultado](workflow-state.md#dispatch-e-execução-persistente) precisam das ferramentas reais do host. Não repita mutação externa de resultado incerto.

## Checkpoint, cancelamento e retomada

Na fonte de estado existente, registre decisão duradoura, pendência autorizada,
identidade/status dos efeitos realizados e evidência/configuração validada. Atualize
esse registro e referencie logs, diff e recibos, sem replicar plano, TASK ou memória.
Arquivos distintos podem ter papéis distintos; mantenha explícita a autoridade de cada um.
Na retomada, leia esse índice e as fontes atuais afetadas; abra evidência bruta se
houver conflito, lacuna ou auditoria requerida. Relato salvo não substitui autoridade
remota: reconcilie efeito incerto por identidade antes de qualquer retry ou ack local.
Revalide a cobertura afetada quando revisão, inputs, configuração, run/geração ou
ambiente mudarem; evidência da configuração A não comprova a B em contexto novo.
Consulte fonte existente, revisão, evidências e estado real; retome a próxima pendência autorizada. Após duas tentativas sem progresso, pare a repetição e reúna diagnóstico antes de escalar conforme o host. Cancelamento não reverte efeitos. Runs incertos mantêm reservas até reconciliação; [checkpoint e recuperação](workflow-state.md#checkpoint-cancelamento-e-retomada) detalham o executor. Memória permanece útil e autorizada, sem captura automática.

Em Git, registre [checkpoint e retomada](git.md#checkpoint-e-retomada) na mesma
fonte: branch/worktree, SHA, diff restante, checks e próxima ação. O checkpoint
da CLI não cria commit ou snapshot Git nem executa integração de branches.
