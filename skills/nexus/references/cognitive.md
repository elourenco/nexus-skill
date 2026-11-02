# Decisões e hipóteses verificáveis

Este módulo é um protocolo documental de decisão, sem executor.
Use diante de premissa frágil, ambiguidade relevante ou impacto material; consulte
apenas a profundidade e os contratos pertinentes. Entregue decisão, evidência e
próxima ação, sem simular pensamento privado, monólogos ou agentes filosóficos.

## Seleção adaptativa

Profundidade cognitiva e [modo operacional](workflow.md) são eixos diferentes:
FAST/BALANCED/DEEP podem acompanhar Explore, Plan, Build, Review ou Autonomous.
Não selecionam provider/modelo, não concedem permissões e não aprovam gates.

| Profundidade | Gatilho observável | Aplicação e saída suficiente |
| --- | --- | --- |
| FAST | Objetivo claro, efeito local e reversível, sem risco material identificado | Verifique objetivo, risco óbvio e caminho mais simples em uma passagem. Execute o trabalho autorizado; justificativa de até três frases quando necessária. Sem comparação, hook nomeado ou ADR obrigatório. |
| BALANCED | Premissa crítica incerta, diagnóstico ambíguo ou alternativas com consequência relevante e reversível | Selecione a premissa decisiva, compare até duas alternativas significativas e proponha validação discriminante. Registre decisão relevante no artefato de trabalho existente. |
| DEEP | Alteração difícil de reverter ou risco concreto de perda de dados, autorização, falha distribuída ou concorrência sutil | Compare até três opções pelos contratos afetados; inclua hipótese contrária, falhas, segurança, escala e reversibilidade. Produza ADR quando a decisão arquitetural for duradoura. |

Escolha a menor profundidade suficiente pelo comportamento afetado, não por palavras
como “pagamento” ou pelo número de arquivos. Se surgir risco material numa tarefa
FAST, recomende DEEP para essa decisão e explique o motivo em uma frase. Urgência
reduz escopo e tamanho da resposta; não remove invariantes. Preferências do usuário
e regras do host prevalecem; se a análise permitida não sustentar uma decisão
segura, declare a lacuna e avance apenas no trabalho independente autorizado.
Após resolver a incerteza, volte à profundidade suficiente para a próxima unidade.

## Princípios como intervenções

| Ação | Quando usar e efeito observável |
| --- | --- |
| Esclarecer a pergunta decisiva | Quando uma resposta muda a solução, escolha a pergunta decisiva: problema real, evidência da premissa, requisito ambíguo, alternativa simples ou fato que invalidaria a decisão. Consulte fontes antes de perguntar ao usuário; não percorra um questionário. |
| Separar requisito de suposição | Se o padrão atual não atende ao contrato, separe requisito fundamental, restrição verificada, suposição herdada e convenção. Reconstrua apenas a parte inadequada a partir das restrições; não reabra requisitos válidos sem evidência. |
| Verificar a inferência | Detecte contradições entre premissa e conclusão; separe fato, hipótese e inferência. Sintoma ou correlação temporal não prova causa: procure observação que discrimine causas concorrentes. |
| Definir como refutar | Para hipótese decisiva, formule previsão testável e o resultado que a refuta. Procure falha e contraexemplo antes de fechar diagnóstico; teste não executado permanece pendente. |
| Escolher a menor solução suficiente | Prefira a menor complexidade que preserva invariantes. Compare manutenção, latência, risco e custo operacional total; menos linhas ou menos componentes não é prova de simplicidade. |
| Separar ação de dependência externa | Separe ação controlável de dependência externa. Registre bloqueio, condição de retomada e trabalho independente útil; não transforme impossibilidade de observar em sucesso. |
| Buscar evidência contrária | Quando houver preferência por hipótese, procure uma evidência contrária com potencial de mudar a escolha; preserve o achado mesmo quando contraria a proposta. |
| Comparar a primeira opção | Quando a primeira opção dominar sem comparação, confronte-a com uma alternativa viável por critérios explícitos; evite opções artificiais só para justificar a favorita. |
| Reavaliar o padrão conhecido | Quando “sempre fazemos assim” sustentar uma escolha, confronte o padrão familiar com restrições atuais; mantenha-o se continuar adequado. |
| Decompor por contratos | Quando dependências excederem o contexto útil, decomponha por contratos, invariantes e ownership; mantenha só fontes pertinentes e referências às evidências. |
| Resumir conhecido e incerto | Ao encerrar ou perder progresso, resuma o que é conhecido, inferido, incerto e precisa ser testado, sem expor raciocínio privado. |
| Explorar e encerrar a escolha | Quando houver escolha material, primeiro levante opções dentro do limite da profundidade; depois selecione por critérios de aceite, custo total e reversibilidade. Encerre a exploração após a comparação. |

Essas heurísticas apoiam decisões; não provam correção nem eliminam vieses.
Considere latência, throughput, concorrência e recuperação nas dimensões alteradas;
não invente medições nem acrescente infraestrutura sem necessidade demonstrada.
Em DEEP, se a proposta alterar fronteiras de confiança, identidade ou persistência
de dados, explicite a invariante de autorização/isolamento e encaminhe sua validação
ao pilar Segurança; mecanismos de deduplicação também precisam preservar esse escopo.

## Contrato comum dos hooks cognitivos

Os oito nomes abaixo são contratos conceituais destinados ao módulo [Hooks](hooks.md).
Não estão registrados nem são executados automaticamente. Sem adapter verificado,
a checagem pertinente é manual; informe isso ao relatar um hook. Não transforme
FAST numa sequência de oito chamadas, nem crie uma segunda orquestração de eventos.

**Inputs comuns:** objetivo/aceite, decisão ou hipótese delimitada, modo operacional,
profundidade, restrições e autorizações do host, evidências com fonte e versão/data
quando disponíveis, lacunas e limites de execução fornecidos. Use contexto mínimo,
sem segredos ou transcrições. Falta de dado material produz pendência, não fabricação.

**Output comum, apenas campos pertinentes:** `decision`, `depth`, `basis`
(fato com fonte, hipótese ou inferência), `alternatives`, `validation`
(refutação esperada e estado proposto/executado), `residual_risk`, `next_action`
e `status` (`sufficient`, `needs_evidence`, `blocked` ou `not_applicable`).
Esses campos formam um resumo lógico; não exigem JSON, texto extenso ou novo arquivo.
`sufficient` significa suficiente para recomendar o próximo passo, nunca aprovação
de gate ou prova de correção. Sem gatilho, encerre silenciosamente como não aplicável.

**Limite transversal:** uma passagem por decisão e conjunto de evidências. Agrupe
checagens sobre a mesma premissa; reutilize a saída existente. Uma nova passagem
requer evidência nova, requisito/risco alterado ou insumo antes ausente. Após duas
tentativas sem progresso verificável, aplique [recuperação](workflow.md), sem zerar
contagem por troca de hook ou profundidade. Limites do host prevalecem; ao esgotar
prazo/budget, entregue estado e próxima ação, não uma conclusão artificial.

Não há fan-out obrigatório, consultas externas automáticas nem promessa de teto de
tokens, custo ou latência. Um executor futuro deve herdar timeout, cancelamento,
concorrência, identificação de tentativa e política de falha de Hooks. Falha de
checagem não aprova gate; mutação externa de resultado incerto exige reconciliação
antes de retry. Reabrir uma decisão não autoriza repetir efeitos.

### `reasoning.challenge`

- **Trigger:** objetivo ambíguo, requisito contraditório ou conclusão que depende de premissa sem suporte.
- **Inputs:** comuns + premissa decisiva e restrição possivelmente violada.
- **Procedimento:** confronte problema, evidência e requisito; separe causa de sintoma. Use primeiros princípios se a abordagem não atender às restrições verificadas.
- **Output:** problema delimitado, premissa corrigida ou pergunta material ainda sem resposta.
- **Limite:** uma premissa decisiva e uma pergunta ao usuário por passagem, somente se as fontes não resolverem a lacuna.
- **Encerramento:** objetivo suficiente para avançar ou dependência explicitamente bloqueada, com condição de retomada.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional; em FAST, detectar a ambiguidade recomenda reclassificação, sem questionário.

### `assumptions.validate`

- **Trigger:** decisão depende de comportamento, capacidade ou restrição não verificados.
- **Inputs:** comuns + premissas ordenadas pelo impacto de estarem erradas.
- **Procedimento:** classifique cada item como requisito, restrição verificada, suposição ou convenção; confronte os decisivos com fonte atual ou teste discriminante.
- **Output:** premissas sustentadas, refutadas ou desconhecidas, com evidência e validação pendente.
- **Limite:** até duas premissas em BALANCED, três em DEEP; uma checagem discriminante por premissa por passagem. Se restar premissa bloqueante, delimite nova unidade de trabalho ou registre impedimento; não a ignore para caber no limite.
- **Encerramento:** nenhuma premissa decisiva fica implicitamente aceita; lacunas têm próxima ação e responsável quando conhecido.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional.

### `alternatives.compare`

- **Trigger:** escolha com trade-off relevante ou primeira solução adotada sem critério.
- **Inputs:** comuns + opções viáveis e critérios de aceite afetados.
- **Procedimento:** explore opções, incluindo manter o estado atual quando viável; selecione por contrato, manutenção, desempenho, falhas e reversibilidade pertinentes. Elimine opção que viole invariante antes de comparar custos.
- **Output:** escolha ou experimento que desempate, com diferença decisiva entre opções.
- **Limite:** duas opções em BALANCED, três em DEEP, uma rodada de comparação; não invente alternativa inviável para cumprir quantidade.
- **Encerramento:** opção suficiente selecionada ou evidência de desempate especificada.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional.

### `bias.challenge`

Este procedimento questiona vieses de raciocínio na decisão de engenharia.
Não comprova equidade de um produto: impactos assimétricos sobre pessoas exigem
a [avaliação pertinente ao domínio](ai-safety-ethics.md#ai-products), dados permitidos
e limites explícitos. Na comparação de alternativas, inclua afetados, finalidade
e menor exposição quando materiais; não infira dano ou neutralidade sem evidência.

- **Trigger:** justificativa baseada em familiaridade, primeira proposta ou seleção apenas de evidências favoráveis.
- **Inputs:** comuns + opção preferida e justificativa observável.
- **Procedimento:** procure contraevidência e teste a adequação de uma alternativa real; confronte o padrão familiar com a restrição atual. Reutilize comparação já feita.
- **Output:** evidência contrária encontrada ou busca inconclusiva, e efeito sobre a decisão.
- **Limite:** um contraexemplo ou uma alternativa por passagem, sem auditoria psicológica da pessoa.
- **Encerramento:** preferência sustentada, revisada ou dependente de evidência identificada; ausência de contraexemplo não prova ausência de viés.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional.

### `hypothesis.falsify`

- **Trigger:** diagnóstico causal ou decisão importante depende de hipótese ainda não refutada.
- **Inputs:** comuns + hipótese, invariante afetada e observação discriminante disponível.
- **Procedimento:** formule previsão e condição de refutação antes de testar; cubra a falha mais relevante. Em concorrência/integrações, considere duplicidade, timeout, interrupção e recuperação conforme o comportamento alterado.
- **Output:** cenário, resultado que refutaria a hipótese e evidência observada ou teste proposto, incluindo limitações do ambiente.
- **Limite:** um cenário discriminante por hipótese por passagem; isso não limita a suíte necessária às invariantes, definida pelas políticas e pelo gate.
- **Encerramento:** hipótese refutada, ainda compatível com evidências ou sem validação; nunca “provada” por ausência de falha.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional; execução de teste depende de ferramentas e autorização existentes.

### `complexity.reduce`

- **Trigger:** mecanismo, dependência ou abstração não tem necessidade demonstrada, ou custo operacional supera o benefício.
- **Inputs:** comuns + solução candidata, invariantes e custos conhecidos.
- **Procedimento:** compare com a menor alternativa suficiente; avalie carga cognitiva, manutenção, latência, throughput e recuperação afetados. Preserve proteções necessárias.
- **Output:** simplificação concreta ou motivo verificável para manter a complexidade.
- **Limite:** uma simplificação candidata por passagem, aproveitando alternativas já examinadas.
- **Encerramento:** contrato preservado com redução justificável, ou simplificação rejeitada por risco/custo total.
- **Modo aplicável:** FAST como checagem breve sem chamada obrigatória; BALANCED/DEEP em qualquer modo operacional.

### `reasoning.reflect`

- **Trigger:** fim de investigação, contradição nova ou tentativa sem progresso.
- **Inputs:** comuns + resultados das checagens e tentativas já feitas.
- **Procedimento:** separe conhecido, inferido e incerto; identifique teste necessário, ação controlável e dependência externa. Reduza contexto a contratos e evidências úteis para retomada.
- **Output:** resumo curto de estado, risco residual e próximo passo ou bloqueio.
- **Limite:** um resumo por passagem, sem recapitular o histórico; não inicia investigação recursiva.
- **Encerramento:** próxima ação definida ou impedimento com condição de retomada; preserve o limite transversal de tentativas.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional; FAST somente se surgir falha ou incerteza relevante.

### `decision.capture`

- **Trigger:** decisão relevante precisa orientar implementação, review ou retomada; mudança arquitetural duradoura exige rastreabilidade.
- **Inputs:** comuns + decisão selecionada, alternativas relevantes e condição de reavaliação.
- **Procedimento:** registre uma síntese no artefato existente; para decisão arquitetural duradoura use o [template ADR](../assets/templates/adr.md). Mantenha `proposed` até satisfazer a aprovação requerida pelo host/projeto; reutilize aprovação já concedida.
- **Output:** registro ou proposta de registro com fontes, consequências, validação e condição de reabertura.
- **Limite:** um registro por decisão, atualizado em vez de duplicado; persistência depende do escopo autorizado.
- **Encerramento:** registro acessível no local autorizado, ou pendência explícita; não abre novo debate por conta própria.
- **Modo aplicável:** BALANCED/DEEP em qualquer modo operacional; em FAST, somente registro já exigido pelo projeto, sem ADR adicional.

## Recomendações aos consumidores

Os nomes Architecture Gate e Review Council designam pontos lógicos dos contratos
atuais, não novos serviços. Encaminhe o resumo comum, omitindo campos vazios e
referenciando evidências já registradas. O consumidor decide e executa no seu escopo.

| Consumidor existente | Recomendação cognitiva |
| --- | --- |
| [Planejamento](workflow.md) | Objetivo, premissa frágil, decisão, dependências e validação que desempata; converter lacuna material em tarefa delimitada. |
| Architecture Gate — `architecture.guard` em [Hooks](hooks.md) | Invariantes, trade-offs, compatibilidade/reversibilidade, riscos e pendências; recomendar avançar ou resolver evidência. O gate mantém seus critérios e autorizações. |
| Review Council — conselho em [Agentes](agents.md) | Selecionar apenas pilares afetados e perguntas verificáveis. Fornecer diff e fontes; hipótese do autor é rotulada, não conclusão imposta ao revisor independente. |
| [Seleção de testes](policies.md) | Hipótese, condição de refutação, falhas e invariantes afetadas. Encaminhar cenários de carga equivalente, saturação, concorrência e recuperação quando pertinentes; distinguir proposto de executado. |
| [Registro de decisões](../assets/templates/adr.md) | Decisão, alternativas, fontes, riscos e condição de reavaliação; não registrar transcrições privadas nem persistir memória sem autorização. |
| [Modo operacional](workflow.md) | Lacuna material → Explore; contrato/alternativa a definir → Plan; decisão suficiente e autorização válida → Build; incremento revisável → Review. Autonomous mantém essas condições. Profundidade e recomendação não provocam troca automática de modo/modelo. |

## Aceite observável

FAST resolve alteração trivial sem cerimônia. BALANCED identifica a premissa que
muda a solução e para de repetir investigação sem evidência nova. DEEP trata risco
material, refutação, reversibilidade e validação sem autorizar efeitos externos.
Em todos os casos, a saída é uma justificativa curta e operacional, independente
de provider. Exemplos de forma suficiente: “Cache é hipótese; comparar consulta
antes/depois com carga equivalente antes de adotá-lo” ou “Resultado externo
incerto; reconciliar estado antes de qualquer retry”.
