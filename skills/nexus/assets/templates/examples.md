# Exemplos de preenchimento

Todos os registros, timestamps, capacidades e resultados deste arquivo são
**fixtures sintéticas**, não trabalho executado nem custos medidos. Os links
usam âncoras no mesmo arquivo para facilitar inspeção; no consumidor, cada registro
pode ficar em seu arquivo. O formato é Markdown estruturado, sem parser implícito.
Contrato de artefatos: 1. Aplique o [contrato comum](contracts.md).

## FAST

### Tarefa: TASK-F01 — corrigir título de ajuda

- Perfil: FAST
- Revisão do registro: 1
- spec_id: não se aplica — FAST
- plan_id: não se aplica — FAST
- Spec/plano e revisão: pedido sintético “corrigir título”, neste exemplo
- Estado: pending
- Prioridade: normal
- Risco: baixo — texto reversível, sem alteração de execução
- Dependências: nenhuma
- Objetivo: trocar “Ajdua” por “Ajuda” no título
- Responsável/papel: agente-A / Implementer
- Capabilities requeridas e disponibilidade: edição Markdown — a verificar no host
- Arquivos permitidos e recursos exclusivos: help.md, escritor único
- Critérios de aceite: AC1 — título igual a “Ajuda”, sem outras alterações
- Testes e verificações: inspecionar título e diff de help.md
- Evidências: nenhuma — verificação ainda não executada
- Impedimento ou próxima ação: verificar capability e iniciar após gate ready

Ao concluir, uma evidência inline pode ser `EVD-F01: inspeção do título e diff;
resultado observado: “Ajuda”, somente o título alterado; timestamp com fuso;
limite: revisão textual, sem execução da aplicação`. Preencha com o resultado
real e associe AC1; registre as transições. Não crie SPEC, PLAN ou EVIDENCE separado.

## Cadeia BALANCED

<a id="spec-001"></a>

### Spec: SPEC-001

- ID e revisão: SPEC-001 @ 1
- Perfil: BALANCED
- Status: accepted
- Objetivo e problema observável: impedir repetição ilimitada de leitura remota após timeout
- Contexto e fonte do requisito: requisito sintético deste cenário
- Requisitos: R1 — no máximo duas tentativas por leitura; R2 — cancelamento encerra retries
- Escopo e exclusões: leitura remota; exclui mutações e alteração de API pública
- Restrições e premissas: operação de leitura idempotente; um único cliente chamador
- Contratos e invariantes: cancelamento não agenda nova tentativa
- Concorrência, latência e throughput afetados: retry pode ampliar latência e carga;
  validar duas tentativas máximas e cancelamento, sem alegar ganho medido
- Falhas, recuperação e compatibilidade: timeout terminal propagado ao chamador;
  preservar erro público; rollback reverte política de retry
- Critérios de aceite: AC1 — até duas chamadas em timeout; AC2 — nenhuma chamada após cancelamento
- Riscos, incertezas e evidências disponíveis: comportamento do cliente sob cancelamento a verificar
- Dependências e referências: contrato do cliente a inspecionar no projeto consumidor
- Planos e tarefas derivados: [PLAN-001](#plan-001),
  [TASK-001](#task-001), [TASK-002](#task-002)
- Decisões pendentes: nenhuma decisão duradoura exige ADR neste incremento
- Aprovação: fixture de escopo aceito; no projeto real consultar fonte da autorização

<a id="plan-001"></a>

### Plano: PLAN-001

- ID e revisão: PLAN-001 @ 1
- spec_id: SPEC-001
- Spec e revisão/commit: [SPEC-001 @ 1](#spec-001)
- Resultado esperado: SPEC-001/AC1 e AC2
- Estratégia de implementação incremental: reproduzir timeout; limitar retry; verificar cancelamento
- Arquivos ou módulos previstos: cliente de leitura e testes correspondentes
- Dependências e sequência: TASK-001 antes de TASK-002
- Estratégia de testes proporcional ao risco: contagem de chamadas, timeout terminal e cancelamento
- Recursos compartilhados e limites de concorrência: um escritor no cliente; testes com servidor isolado
- Recuperação/rollback: regressão na propagação de erro → reverter política → reexecutar aceites
- Arquitetura proposta: fronteiras preservadas; sem novo serviço
- Alternativas e trade-offs: sem retry reduz carga, mas não tolera falha transitória;
  retry limitado aumenta latência máxima e permanece observável
- Todo (visão na revisão 4 de TASK-001):

| ID/link | Estado | Responsável/papel | Modelo efetivo | Dependências | Bloqueio/próxima ação | Artefatos |
| --- | --- | --- | --- | --- | --- | --- |
| [TASK-001](#task-001) | blocked | agente-A / Implementer | indisponível | nenhuma | verificar ambiente | [SPEC-001](#spec-001), [PLAN-001](#plan-001), [EVD-001](#evd-001) |
| [TASK-002](#task-002) | pending | agente-B / Implementer | indisponível | TASK-001 | aguardar dependência | [SPEC-001](#spec-001), [PLAN-001](#plan-001) |

- Progresso: 0/2 done, 1 blocked, 0 cancelled; contagem de tarefas, não esforço
- Validação final: AC1/AC2 pendentes; evidência de bloqueio não comprova aceite

<a id="task-001"></a>

### Tarefa: TASK-001

- Perfil: BALANCED
- Revisão do registro: 4
- spec_id: SPEC-001
- plan_id: PLAN-001
- Spec/plano e revisão: [SPEC-001 @ 1](#spec-001), [PLAN-001 @ 1](#plan-001)
- Estado: blocked
- Prioridade: alta
- Risco: médio — política de retry altera carga em falha
- Dependências: nenhuma
- Objetivo: limitar tentativas da leitura remota
- Responsável/papel: agente-A / Implementer
- Capabilities requeridas e disponibilidade: editar cliente — disponível na fixture;
  executar testes locais — bloqueado por ambiente
- Arquivos permitidos e recursos exclusivos: módulo de leitura e seus testes, escritor único
- Critérios de aceite: SPEC-001/AC1, observado por contagem de chamadas
- Testes e verificações: testar timeout sucessivo e propagação do erro terminal
- Evidências: [EVD-001](#evd-001)
- Impedimento ou próxima ação: ambiente de testes indisponível; restaurar e conferir estado antes de retry
- Contratos preservados: SPEC-001/R1 e erro público
- Provider/modelo/esforço efetivos: indisponível
- Budget autorizado e origem: não informado
- Consumo medido: tentativa A1, agente-A, provider/modelo indisponíveis;
  valor 120, unidade tokens, fonte fixture sintética;
  intervalo 2026-10-31T09:01:00-03:00/2026-10-31T09:02:00-03:00;
  custo monetário indisponível
- Tentativas e hipóteses descartadas: A1 falhou ao iniciar testes, sem conclusão sobre AC1
- Checkpoint: workspace sintético, revisão de código base-A, sem alteração aplicada;
  nenhuma operação externa pendente; próximo passo é restaurar ambiente
- Review/decisões associados: [REV-001](#rev-001), pendente
- Histórico de transições:
  - 2026-10-31T08:59:00-03:00, criação em pending, agente-A, revisão 1
  - 2026-10-31T09:00:00-03:00, pending → ready, agente-A, aceite/escopo conferidos, revisão 2
  - 2026-10-31T09:01:00-03:00, ready → running, agente-A, início A1, revisão 3
  - 2026-10-31T09:02:00-03:00, running → blocked, agente-A, EVD-001, revisão 4

<a id="task-002"></a>

### Tarefa: TASK-002

- Perfil: BALANCED
- Revisão do registro: 1
- spec_id: SPEC-001
- plan_id: PLAN-001
- Spec/plano e revisão: [SPEC-001 @ 1](#spec-001), [PLAN-001 @ 1](#plan-001)
- Estado: pending
- Prioridade: normal
- Risco: médio — cancelamento durante retry
- Dependências: [TASK-001](#task-001)
- Objetivo: verificar e ajustar cancelamento
- Responsável/papel: agente-B / Implementer
- Capabilities requeridas e disponibilidade: edição e testes — a verificar antes de ready
- Arquivos permitidos e recursos exclusivos: cliente e testes; somente após liberar TASK-001
- Critérios de aceite: SPEC-001/AC2, observado por ausência de nova chamada
- Testes e verificações: cancelar entre tentativas
- Evidências: nenhuma — não executado
- Impedimento ou próxima ação: aguardar TASK-001 done e revalidar evidências

<a id="evd-001"></a>

### Evidência: EVD-001

- Tipo de verificação: tentativa de regressão automatizada
- Task/spec e aceites relacionados: [TASK-001](#task-001), [SPEC-001/AC1](#spec-001)
- Comando ou procedimento reproduzível: invocar a suíte do cliente no ambiente consumidor
- Contexto da execução: fixture A1, workspace sintético, código base-A
- Resultado real: não executado — ambiente indisponível; nenhum código de saída observado
- Arquivos/artefatos relacionados: cliente e seus testes, sem saída anexada
- Timestamp: 2026-10-31T09:02:00-03:00
- Limitações: fixture; não comprova AC1, latência ou throughput

<a id="rev-001"></a>

### Review: REV-001

- Data e revisão do registro: 2026-10-31T09:03:00-03:00, revisão 1
- task_id: [TASK-001](#task-001)
- spec_id: [SPEC-001](#spec-001)
- Pilar responsável e revisor: Qualidade, agente-C
- Alvo revisado: registro TASK-001 @ 4; código base-A sem mudança aplicada
- Referências e critérios de aceite: SPEC-001/AC1
- Achado F1 — aceite sem execução
  - Severidade: média
  - Estado: aberto
  - Condição e impacto: suíte indisponível; concluir a tarefa agora deixaria AC1 sem comprovação
  - Evidências reproduzíveis: [EVD-001](#evd-001), repetir após restaurar ambiente
  - Correção recomendada: executar regressão e anexar evidência nova
  - Resolução: pendente
- Decisão final: alterações necessárias
- Justificativa e limitações: review documental, não revisou implementação
- Gates aplicáveis e resultado: aceite atual não demonstrado; manter tarefa sem conclusão

## Retomada da fixture

O agente-B lê TASK-001 @ 4, SPEC-001 @ 1, PLAN-001 @ 1 e EVD-001. Confere
workspace, ambiente, autorização, ownership e ausência de operação externa incerta.
Não interpreta o checkpoint como prova de estado atual. Não precisa de transcrição.

Após restaurar o ambiente, registra transferência A → B, disponibilidades verificadas
e `blocked → ready` na revisão 5; registra `ready → running` na revisão 6 e tentativa
A2. O ID continua TASK-001. Mantém A1, os 120 tokens sintéticos e EVD-001; A2 terá
entrada própria. Se A2 tiver 30 tokens sintéticos, da mesma unidade e intervalo
posterior sem sobreposição, o total da fixture será 150 tokens, sem inferir moeda.
Sem medição de A2, o total conhecido permanece 120 e a cobertura é parcial.

Se restaurar o ambiente falhar, permanece blocked e adiciona a tentativa/evidência;
não avança para done. Ao obter evidência válida de AC1, revalida REV-001 e somente
então registra done; a tarefa dependente ainda precisa passar pelo gate ready.

## Extensão DEEP — somente quando necessária

Se o escopo passar a alterar o contrato público, atualize SPEC/PLAN, reavalie as
TASKS afetadas e aprofunde cenários de falha/concorrência. Registre uma decisão
necessária com [ADR](adr.md), e uma review de Arquitetura/Resiliência sobre a revisão
atual. O exemplo a seguir não promove automaticamente a cadeia BALANCED.

<a id="adr-001"></a>

### ADR: ADR-001 — limitar retry ao cliente de leitura

- Revisão: 1
- Status: proposed
- Data e fontes: 2026-10-31, [SPEC-001 @ 1](#spec-001), [PLAN-001 @ 1](#plan-001)
- Spec/task relacionada: [TASK-001](#task-001)
- Contexto e restrições: timeout transitório, leitura idempotente, carga limitada
- Alternativas consideradas: retry no chamador; retry no cliente; nenhuma repetição
- Decisão e justificativa: proposta de concentrar retry no cliente para evitar multiplicação entre camadas
- Consequências: um ponto de controle; aumento de latência em falha; risco de carga extra
- Efeitos em latência, throughput e concorrência: medir antes de alegar melhora; limitar tentativas por chamada
- Falhas e recuperação: cancelamento e timeout terminal mantêm erro público
- Compatibilidade e reversibilidade: sem mudança pública; reversão da política local
- Evidências e condição para reavaliar: mudança de idempotência ou evidência de sobrecarga
- Substituído por: não se aplica

### Registro: hipótese de retry

- ID e revisão: MEM-001 @ 1
- Tipo: hipótese
- Escopo: fixture, cliente de leitura, SPEC-001 @ 1
- Data: 2026-10-31
- Fonte verificável: [ADR-001 @ 1](#adr-001)
- Conteúdo mínimo: concentrar retry em uma camada pode evitar multiplicação de tentativas
- Confiança e justificativa: baixa; proposta sem medição
- Revalidar quando: adoção do ADR, alteração de idempotência ou medição de carga
- Status: active
- Substituído por: não se aplica
- Autorização para persistir/compartilhar: somente fixture sintética neste pacote;
  não autoriza memória global nem persistência de dados de projeto consumidor

## Produto com IA — recomendação de acesso a serviço essencial

Recorte **sintético e proposto** de uma SPEC, sem produto, workflow ou helper
executado. Demonstra o preenchimento dos campos existentes; não é uma cadeia de
artefatos pronta para execução. Regra: [nexus.policies revisão 2](../../references/policies.md#policy-ai-safety-ethics).

- ID e revisão: SPEC-AI-DEMO @ 1
- Perfil: DEEP — recomendação pode influenciar acesso a serviço essencial.
- Status: draft
- Objetivo e problema observável: assistente propõe encaminhamento; decisão final
  cabe ao responsável humano do serviço, com autoridade para corrigir/interromper.
- Contexto e fonte do requisito: fixture fictícia; pessoas podem receber negativa
  indevida, especialmente se o erro afetar grupos de modo assimétrico.
- Escopo e exclusões: preparar critérios de avaliação; não automatizar negativas,
  coletar atributos sensíveis ou operar serviço real.
- Contratos e invariantes: recuperação respeita acesso do usuário; nenhuma saída
  do modelo altera o cadastro antes de validação/autorização pelo executor.
  Interface informa uso de IA e limites. Pessoa afetada pode contestar por canal
  acessível; responsável humano recebe evidência e pode corrigir o resultado.
- Concorrência, latência e throughput afetados: limitar chamadas agregadas e
  manter autorização válida até o efeito; metas e desempenho ainda não definidos.
- Falhas, recuperação e compatibilidade: controle indispensável indisponível
  suspende a recomendação dependente; atendimento humano autorizado permanece.
  Timeout de escrita exige reconciliação, sem reenvio cego.
- Critérios de aceite propostos: AC1 — demonstrar revisão e correção humanas antes
  da negativa; AC2 — avaliar erros/danos por grupos pertinentes com amostra adequada
  e permitida, documentando cobertura/limitações; AC3 — verificar transparência e
  acessibilidade da explicação e contestação; AC4 — testar isolamento, saída inválida
  e falha do controle antes do efeito.
- Riscos, incertezas e evidências disponíveis: dados/amostra e responsáveis reais
  não existem nesta fixture. Sem esses insumos, a avaliação de equidade permanece
  inconclusiva; não há coleta automática para suprir a lacuna.
- Planos e tarefas derivados: ainda não criados; nenhuma tarefa concluída.
- Decisões pendentes: critérios do domínio, amostra permitida, responsáveis reais,
  canal de contestação e testes. Desenho do produto ainda não aprovado.

**Evidência proposta:** não executado. Procedimento futuro: aplicar casos sintéticos
de negativa indevida, saída não autorizada, controle indisponível e contestação;
depois avaliar amostra permitida representativa. Não há resultado de teste,
recibo de helper ou alegação de conformidade. O preenchimento acima apenas ilustra
o contrato; não demonstra que os controles foram implementados ou verificados.
