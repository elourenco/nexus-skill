# Contratos de artefatos — versão 1

Este módulo padroniza Markdown estruturado para agentes e leitura humana. Não é
um formato de runtime nem instala UI, parser, hooks ou sincronização. Os arquivos
existentes continuam sendo pontos de entrada; carregue este contrato sob demanda. Seus mínimos e estados aplicam-se somente à adoção documental rastreada destes templates. Execução direta em qualquer perfil usa chat/diff/evidência, sem TASK/SPEC/PLAN obrigatórios; um plano, issue ou todo existente pode bastar sem conversão. A CLI opt-in conserva seu contrato próprio.

## Inventário e consumidores

| Template | Necessidade | Consumidores atuais |
| --- | --- | --- |
| [SPEC](spec.md) | Comportamento/contrato a definir; BALANCED/DEEP | Workflow Plan/Build, Planner, Implementer, Reviewer |
| [PLAN](plan.md) | Execução em etapas; BALANCED/DEEP | Workflow, Planner, Implementer, visão de todo |
| [TASK](task.md) | Unidade rastreável quando adotado este formato; todo/retomada | Workflow Build/Autonomous, agentes, review |
| [REVIEW](review.md) | Quando risco ou gate requer revisão | Reviewer e responsável pela conclusão |
| [EVIDENCE](evidence.md) | Validação executada; arquivo separado opcional | Workflow, Reviewer, gates e memória |
| [DECISION/ADR](adr.md) | Decisão duradoura relevante, opcional | Architect, Planner, memória |
| [MEMORY](memory.md) | Conhecimento reutilizável e persistência autorizada, opcional | Retomada e memória do projeto |

Na base `5684e44` havia SPEC, PLAN, TASK, ADR e MEMORY, sem duplicatas ou templates
órfãos: README/workflow referenciavam os quatro primeiros; a referência de memória
usava MEMORY. REVIEW e EVIDENCE eram texto livre. O validador existente verifica
metadados da skill e links, não esquema dos artefatos. Os contratos Markdown são consumidos por instruções/agentes. O template MEMORY também preserva uma entrada JSON para o helper opt-in já existente; isso não converte os demais artefatos em schemas de máquina. Não presumir execução automática.

## Identidade e referências

- Cada artefato tem ID estável no escopo do projeto. Preserve IDs existentes,
  inclusive formatos diferentes; para novos use, por exemplo, `SPEC-001`,
  `PLAN-001`, `TASK-001`, `REV-001`, `EVD-001`, `ADR-001`, `MEM-001`.
- O ID tem uma única declaração canônica no cabeçalho/campo do próprio registro.
  Arquivos podem mudar de nome sem mudar ID; atualize seus links. IDs cancelados
  não são reutilizados. Achados e aceites usam IDs locais (`REV-001/F1`, `SPEC-001/AC1`).
- `ID e revisão` é `ID @ revisão`; revisão é inteiro crescente, começando em 1.
  Na TASK o ID fica no título e `Revisão do registro` é separado. Uma mudança de
  status ou responsável incrementa revisão, nunca muda o ID. EVIDENCE registra
  uma observação imutável por ID; nova execução/correção usa novo ID e referência
  à original, sem revisão mutável da evidência.
- Referência resolvível = ID + link Markdown relativo ao arquivo/âncora; relações
  de entrada (SPEC no PLAN e SPEC/PLAN na TASK) fixam também revisão ou commit.
  `spec_id`/`plan_id` guardam o ID; o campo de referência guarda link e revisão.
  Ambos devem identificar o mesmo artefato. Links de derivados apontam para a
  versão atual e não exigem atualizar a SPEC a cada mudança de status da TASK.
- SPEC lista PLAN e TASKS derivados; PLAN mantém índice de TASKS; TASK aponta para
  SPEC e PLAN; REVIEW aponta para TASK e SPEC e identifica a revisão examinada.
  Registre os dois lados ao criar a relação. Semântica, origem e aceite ficam na
  SPEC; plano registra estratégia e tarefa registra incremento/evidência.
- Gere IDs novos com um responsável serial por escopo, ou um namespace exclusivo
  por frente. Verifique colisões antes de integrar; não use contador concorrente
  compartilhado sem coordenação. Não existe alocador automático.
- Na adoção, registre `Contrato de artefatos: 1` no índice do projeto ou na TASK
  isolada neste formato. Isto versiona o formato, não altera a versão da SPEC.

## Perfis proporcionais

Perfis expressam risco e profundidade, independentemente de execução direta ou rastreada. A tabela descreve mínimos somente para quem adotar este formato documental; não torna artefatos obrigatórios em todo FAST/BALANCED/DEEP nem substitui modos Explore/Plan/Build.

| Perfil | Entrega mínima | Condições |
| --- | --- | --- |
| FAST | Uma TASK com núcleo preenchido, aceite e evidência curta inline | Incremento pequeno e delimitado; SPEC/PLAN podem ser não aplicáveis |
| BALANCED | SPEC compacta, PLAN incremental, TASKS ligadas | Contrato ou execução em etapas |
| DEEP | SPEC completa, PLAN arquitetural, TASKS, review especializado e evidências aprofundadas | Risco/complexidade justificam análise aprofundada; ADR somente para decisões necessárias |

A escolha não dispensa gates do projeto. Review pode ser necessária em qualquer
perfil. MEMORY é sempre condicional à utilidade e autorização. EVIDENCE pode ser
inline com ID local e âncora; extraia arquivo apenas se compartilhada ou extensa.
FAST não requer preencher seções de execução sem execução, budget sem autorização
ou ADR sem decisão. Aceites locais da TASK substituem a SPEC ausente. Ao promover o perfil neste formato rastreado, complete os artefatos pertinentes, atualize referências e preserve TASK ID e histórico; não altere risco para evitar gates.
Não repita contexto por artefato; o consumidor resolve os links relevantes.

## Estados e transições

**Adoção documental rastreada destes templates, sem executor:** o enum dos registros Markdown é:
`pending`, `ready`, `running`, `blocked`, `done`, `cancelled`.
Os nomes de UI BACKLOG, READY, IN_PROGRESS, BLOCKED, DONE e CANCELLED mapeiam,
respectivamente, para esses valores. REVIEW é etapa de `running` com link para
review pendente; FAILED é resultado de tentativa, mantendo `running` enquanto
houver correção autorizada em curso ou `blocked` enquanto aguarda dependência/decisão.
Cancelamento autorizado usa `cancelled` e preserva o resultado observado; não
transforma a tentativa em sucesso. Consulte [Policies](../../references/policies.md)
para os resultados agregados e gates. Não grave REVIEW ou FAILED em `Estado`: isso
exigiria migração coordenada do consumidor documental.

| Origem | Destinos permitidos | Condição |
| --- | --- | --- |
| pending | ready, blocked, cancelled | Refinamento, impedimento ou cancelamento registrado |
| ready | running, pending, blocked, cancelled | Início, escopo invalidado, impedimento ou cancelamento |
| running | done, blocked, cancelled | Aceite/gates satisfeitos, bloqueio ou cancelamento |
| blocked | ready, pending, cancelled | Bloqueio resolvido e revalidado, replanejamento ou cancelamento |
| done | pending | Reabertura explícita com nova evidência ou mudança material |
| cancelled | pending | Reativação explícita dentro da autorização vigente |

`ready` exige dependências `done` com evidência ainda válida, aceite definido,
capabilities disponíveis e autorização suficiente. Uma dependência cancelada não
está satisfeita; replaneje explicitamente. Ciclos de dependência impedem `ready`.
`running` exige responsável e recursos exclusivos. `done` exige evidência para
cada aceite e review/gates exigidos satisfeitos na revisão atual. Toda transição
registra data com fuso, ator, motivo/evidência e revisão nova. Atualizações sem
transição também incrementam revisão e preservam entradas anteriores.

Fatie tarefas por resultado verificável e ownership: se há entregas independentes,
recursos concorrentes ou um próximo passo que não pode ser explicado brevemente,
divida em TASKS ligadas. Não imponha um limite arbitrário de linhas ou horas.

### Uso do executor opt-in

Quando o projeto adotar a [CLI de workflow](../../references/workflow-state.md), o store JSON é a autoridade e seu contrato de operações prevalece sobre a tabela documental acima. Há sete estados, incluindo `validating`: `result(success)` leva `running → validating`, e somente `complete` leva `validating → done` após gates. `cancelled` é terminal; novo escopo autorizado exige outro workflow. `resume`/`recover` levam `blocked → pending`, preservando tentativas; `ready` reavalia os gates. Não há importação automática, migração ou sincronização de TASKS Markdown.

Interrupção ou cancelamento de run ativo mantém a reserva até `reconcile_run` com evidência do host. Nunca use edição Markdown ou a tabela documental para liberar recursos do executor. Se exportar estes templates, eles continuam artefatos documentais; não são requests JSON de `apply`. A revisão de uma TASK Markdown é distinta da revisão global do store e da geração de evidências. Escolha e registre a fonte de estado antes de executar; não mantenha duas autoridades.

## Interactive Todo Contract

**Ao adotar estes templates sem executor**, a fonte persistente é o conjunto de TASKS Markdown e seus artefatos ligados. Um acompanhamento nativo existente conserva seu contrato; execução direta não exige fonte persistente. **Com executor opt-in**, consulte o store por `show` e faça alterações por `apply`, conforme o contrato acima; Markdown é apenas projeção. A UI
ou tabela do PLAN é uma projeção. O contrato mínimo de cada linha é:

| ID/link | Estado | Responsável/papel | Modelo efetivo | Dependências | Bloqueio/próxima ação | Artefatos |
| --- | --- | --- | --- | --- | --- | --- |
| ID estável e link da TASK | Enum persistente | Ator atual | Valor observado ou indisponível | IDs | Resumo da TASK | SPEC/PLAN/review/evidências por link |

Progresso = tarefas `done` / tarefas não canceladas, mais contagem separada de
canceladas e bloqueadas. Sem tarefas ativas, mostre “não aplicável”; não transforme
cancelamento em conclusão. Não use esse quociente como percentual de esforço. A métrica `completion_rate` da CLI usa todas as tarefas, incluindo canceladas, e exibe cancelamento separadamente; não confunda esse indicador com a fração de escopo ativo acima. O executor não entrega workflow com escopo cancelado.

No modo documental, siga os passos abaixo. Com executor, use a revisão global e `operation_id` da CLI; não edite uma projeção para transicionar tarefas.

1. Leia a TASK e sua revisão atual antes de editar, inclusive via UI nativa.
2. Um único responsável escreve cada TASK/recurso. Registre transferência e as
   capabilities/modelo do novo executor; preserve a atribuição das tentativas antigas.
3. Releia antes de salvar. Se a revisão mudou, pare e reconcilie o diff; não faça
   sobrescrita automática. Markdown não fornece compare-and-swap, locks ou atomicidade.
   Sem mecanismo de exclusão verificado, serialize as escritas.
4. Persista a mudança e seu histórico antes de atualizar a visão. Se a UI falhar,
   derive novamente a visão do registro. Não afirme sincronização automática.
5. Na retomada, confira fontes/revisões, dependências, autorizações, budget conhecido,
   evidências e estado real de arquivos/operações. Resultado externo incerto exige
   reconciliação antes de retry. `running` abandonado vai a `blocked` com checkpoint;
   após resolver, siga `blocked → ready → running`.

Sem UI real, a tabela Markdown acima é o fallback disponível. A CLI local é opcional e requer Python/POSIX; use apenas os comandos documentados. O contrato não depende de estado do chat.
Leia apenas a TASK e referências pertinentes na retomada; um índice derivado evita
recarregar toda a documentação. Escritas seriais podem limitar throughput, mas
são proporcionais à fase documental; não há benchmark de latência ou concorrência.

## Custos, evidências e falhas

Budget é autorização, consumo é observação. Ausência de medição é `indisponível`,
nunca zero. Preserve um lançamento por tentativa (ID, executor/provider/modelo,
valor, unidade, fonte e intervalo). Só some valores de mesma unidade/moeda e
intervalos não sobrepostos; revisões de uma medição referenciam a anterior e não
são somadas novamente. Totais são derivados; lacunas de cobertura ficam explícitas.
Não estime gasto monetário a partir de tokens sem preço/fonte válidos e autorização.

Evidência é append-only: uma nova execução gera novo ID; uma correção de transcrição
registra a correção sem apagar o original. Timestamp usa ISO 8601 com fuso. Saída
não executada ou de versão antiga não comprova a versão atual. Separe evidências
sintéticas de observações reais. Nunca copie segredos ou dados privados para exemplos.

## Integração e migração

| Consumidor | Checagem manual neste módulo |
| --- | --- |
| Workflows | Criar relações nos dois sentidos; mudança material invalida aceite/review afetados até reconciliação |
| Agents | Ler TASK + SPEC/PLAN fixados; conferir ownership/capabilities e fontes atuais antes de executar |
| Reviews | Registrar alvo, task_id, spec_id, achados estáveis e decisão; anexar link à TASK |
| Memory | Extrair decisão/observação com proveniência, validade e autorização; referenciar ADR/EVIDENCE |
| Hooks | `context.load`: retomada; `validation.run`: evidência; `completion.verify`: aceite e gates; checagens manuais |
| Policies | Budget conhecido, modelos efetivos, revisão proporcional, limites de tentativa e autorizações do host prevalecem |

Os nomes de hooks são lógicos; este módulo não os registra. Não altere outros
módulos para adotar estes templates sem coordenar o ownership.

Migração incremental de artefatos antigos: preserve arquivo, ID, status, links,
texto e evidências; não regenere documentos. Acrescente ID/revisão ausentes ao PLAN
e MEMORY documental (no helper JSON a revisão é gerada pelo store); mantenha um ID que já exista no título. Separe a relação combinada
`Spec/plano e revisão` em `spec_id` e `plan_id`, conservando o campo original com
links/revisões. Em SPEC, `Fonte do requisito` cabe em `Contexto e fonte do requisito`;
`Evidências disponíveis e hipóteses` cabe em `Riscos, incertezas e evidências disponíveis`;
`Escopo e exclusões`, aceites e aprovação continuam válidos. Em ADR, preserve o
conteúdo de `Falhas, recuperação e custo operacional` nos campos de consequências
e recuperação. Dados ausentes são declarados, nunca reconstruídos por suposição.

Registros legados continuam legíveis. Antes de uma nova transição, complete os
campos necessários ao gate atual e registre a adoção da versão 1; bloqueie somente
o trabalho dependente de informação indispensável. Não converta estados em massa.
Não há validação automática de esquema: o script do repositório continua cobrindo
links/metadados; [cenários e resultados](validation.md) cobrem aplicação documental.
[Exemplos](examples.md) mostram FAST e uma cadeia completa sem requerê-la para todos.
