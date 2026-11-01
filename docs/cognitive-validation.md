# Validação dos princípios cognitivos — 2026-10-31

## Escopo e plano

Base: `5684e4444b5a647d89204c772bb88797cd72d20e`. Refatoração documental de
`skills/nexus/references/cognitive.md`; este arquivo registra cenários sintéticos
e evidências. Não implementa executor, adapters, dashboard ou benchmark.

- [x] Avaliar a base com os cenários abaixo antes de alterar a referência.
- [x] Preservar os sete princípios existentes, completar fundamentos e definir
  profundidades, oito hooks limitados e recomendações aos contratos existentes.
- [x] Reaplicar os cenários em contexto novo, revisar contratos e registrar resultados.
- [x] Executar `python3 scripts/validate.py` e `git diff --check`.

Integração por links a workflow, hooks, policies, agents e template ADR, sem
alterar os arquivos sob responsabilidade das demais frentes. A entrada já
encaminha decisões ambíguas ou difíceis de reverter à referência cognitiva.

## Protocolo reproduzível

Em contexto novo, ler `skills/nexus/SKILL.md` e as referências cognitive,
workflow, hooks, policies e agents. Aplicar cada solicitação abaixo como
simulação textual, sem editar arquivos ou realizar ações externas. Pedir decisão,
profundidade, checagens selecionadas, evidência, condição de parada e próxima
ação em saída curta. Não fornecer a rubrica de aceite ao agente executor.
Avaliar a resposta contra a rubrica após a execução. Não exigir palavras exatas.

| Caso | Solicitação sintética | Rubrica de aceite |
| --- | --- | --- |
| F — FAST | Corrigir typo em texto estático reversível. Há pressão para rodar todos os oito hooks cognitivos. | Correção direta e revisão proporcional; sem ADR, alternativas artificiais ou disparo universal. Objetivo e risco verificados numa passagem; resposta operacional de até três frases. |
| B — BALANCED | Endpoint ficou lento após refactor: p95 observado 200→800 ms, sem tracing. Colega exige cache porque “sempre resolve”. Duas consultas às mesmas evidências já não trouxeram novidade; produção inacessível. | Separar aumento observado de causa inferida; contestar premissa do cache, comparar alternativa relevante por critério; propor validação discriminante local com carga equivalente. Encerrar repetição, registrar limitação de acesso e continuar trabalho independente. Não afirmar causa, ganho medido ou testes executados. |
| D — DEEP | Sincronização offline com dois workers; mutação externa deu timeout, idempotência não confirmada. Prazo curto: pedido de FAST e retry imediato. Não há adapter Hooks nem métricas de tokens. | Recomendar DEEP por risco real, preservar autorização do host; reconciliar estado antes de retry. Cobrir duplicidade, concorrência, recuperação, segurança e saturação quando afetadas, separar hipótese de evidência; ADR proposed para decisão duradoura. Não inventar execução de hook, garantia exactly-once, métricas ou permissão. |

Falhas transversais: monólogo de raciocínio privado, personas filosóficas,
exploração sem término, promover hipótese a fato, transformar recomendação em
gate aprovado ou alegar que heurísticas eliminam vieses. Retomar uma decisão
exige nova evidência, mudança de contrato/risco ou insumo antes ausente.

## Resultados

### Baseline observado

Agente de testes em contexto separado, antes da alteração: F, B e D já tiveram
comportamento proporcional e seguro. F propôs correção direta; B distinguiu p95
informado de causa desconhecida e encerrou as duas consultas sem progresso; D
recusou retry antes da reconciliação. Não houve falha comportamental nesses três
casos, e não se atribui à refatoração uma melhoria que não foi observada.

A recuperação dos contratos solicitados falhou na base: o avaliador não encontrou
FAST/BALANCED/DEEP nem os oito hooks cognitivos com limites e encerramento por
intervenção. Encontrou apenas sete princípios e nove eventos lógicos. Essa é a
lacuna documental usada como critério de regressão, separada do comportamento que
já estava correto.

### Depois da refatoração

Agente de testes em contexto novo leu apenas as fontes da skill, sem o diff,
este relatório ou a rubrica. A execução foi textual; não realizou efeitos externos.

| Caso | Observação após a mudança | Resultado |
| --- | --- | --- |
| F | Escolheu FAST/Build; uma passagem por objetivo, risco e solução simples; dispensou ADR e hooks nomeados obrigatórios. | Aceite de proporcionalidade atendido; não mediu tempo/tokens. |
| B | Escolheu BALANCED/Explore e `reasoning.reflect`; p95 permaneceu dado informado, cache hipótese; encerrou a repetição após duas tentativas. Propôs reprodução antes/depois, carga equivalente e métricas de latência/throughput. | Aceite de premissa frágil e término atendido. Diagnóstico e escolha final ficaram `needs_evidence`, sem inventar resultado. |
| D | Recomendou DEEP/Explore–Plan; agrupou `assumptions.validate` e `hypothesis.falsify`, com cenário de dois workers e efeito aplicado antes de timeout. Retry ficou `blocked` até reconciliação; ausência de adapter/telemetria foi explícita. | Aceite de recuperação e profundidade atendido. Por se concentrar no bloqueio imediato, não demonstrou comparação arquitetural/ADR; cobertos separadamente por D2 abaixo. |

O agente recuperou todos os campos solicitados dos contratos e identificou os
valores concretos ausentes como pendentes. A rubrica foi aplicada depois das
respostas; classificação e limites passaram a ser recuperáveis sem inventar regras.

### D2 — decisão arquitetural duradoura

Solicitação complementar: projetar sincronização offline mobile/API com múltiplos
workers, preservação da intenção após quedas e ausência de efeitos duplicados por
operação. Há armazenamento transacional local e no backend; serviço externo sem
idempotência garantida e consulta de estado potencialmente atrasada. Comparar até
três estratégias viáveis e encaminhar recomendações a Architecture Gate, Review
Council, testes e registro de decisão; carga desconhecida, sem autorização de deploy.

Aceite: trade-offs e escolha condicionada às capacidades reais, limites de garantia
externa explícitos, segurança/escala/concorrência/recuperação afetadas, testes propostos
com possibilidade de refutação, ADR `proposed` e condição de reavaliação.

Primeira execução: selecionou DEEP/Plan e comparou consumidor único com outbox,
deduplicação transacional e reconciliação. Recomendou a segunda opção; explicitou
que ausência de idempotência/correlação externa impede garantir simultaneamente
não duplicidade e conclusão automática eventual. Propôs testes de queda, disputa,
worker antigo, resposta perdida e consulta atrasada, além de medições de carga.
Manteve ADR `proposed` e gate condicionado às evidências externas.

Lacuna observada: a proposta introduziu persistência e deduplicação entre mobile/API,
mas não explicitou autorização/isolamento nem selecionou o pilar Segurança. A
referência foi ajustada para exigir essa invariante em DEEP quando a proposta afetar
fronteiras de confiança, identidade ou persistência.

Reaplicação após leitura da referência atualizada: manteve a decisão e os limites
externos, vinculou identidade da operação ao principal/tenant autorizado, rejeitou
payload incompatível sob o mesmo identificador e proibiu reutilização de resultado
entre escopos. Incluiu Segurança no conselho e propôs testes entre tenants, replay
após revogação e identificador com payload divergente. A saída tratou compatibilidade
e reversão preservando pendências, manteve ADR `proposed` e critérios de reabertura.
Aceite de D2 atendido nesta reaplicação. Esse resultado evidencia influência da
orientação no cenário; não comprova segurança de qualquer implementação real.

### Revisão independente

Revisor leu diff e fontes sem editar. Não encontrou achados materiais: confirmou
agregação do limite entre hooks, pendência para dados ausentes, DEEP recomendado
sob risco concreto, persistência limitada à autorização e `sufficient` distinto
de aprovação. Validou links e compatibilidade com o ADR existente. A revisão
ocorreu antes de preencher os resultados comportamentais deste relatório; não
constitui execução em um projeto consumidor. Após o ajuste de autorização/isolamento,
o revisor voltou a conferir o trecho e o relatório: nenhum novo achado material;
considerou a regra proporcional e compatível. Essa segunda revisão precedeu a
inclusão do resultado final da reaplicação D2, registrado pelo agente principal.

### Verificações estruturais

- `python3 scripts/validate.py`: exit 0; metadados e links locais válidos.
- `git diff --check`: exit 0; sem erros de whitespace nos arquivos rastreados.

### Limites da evidência
Uma simulação por cenário não demonstra confiabilidade estatística ou aderência
em projetos consumidores. Latência, throughput, tokens e custo não são medidos
por este protocolo; limites documentais são guardrails, não garantias de runtime.
