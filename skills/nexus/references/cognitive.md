# Decisões e hipóteses verificáveis

Protocolo documental, sem executor, para premissa frágil, ambiguidade ou impacto
material. Entregue decisão, evidência e próxima ação; sem pensamento privado,
monólogos ou agentes filosóficos. Consulte apenas os contratos pertinentes.

## Seleção adaptativa

Profundidade cognitiva e [modo operacional](workflow.md) são eixos diferentes:
FAST/BALANCED/DEEP podem acompanhar Explore, Plan, Build, Review ou Autonomous.
Não selecionam provider/modelo, não concedem permissões e não aprovam gates.

| Profundidade | Gatilho observável | Aplicação e saída suficiente |
| --- | --- | --- |
| FAST | Objetivo claro, efeito local/reversível, sem risco material | Execute o autorizado após checar objetivo e risco. Justificativa de até três frases se necessária; sem comparação, hook ou ADR obrigatório. |
| BALANCED | Premissa crítica incerta, diagnóstico ambíguo ou trade-off relevante/reversível | Selecione premissa decisiva, até duas alternativas e validação discriminante. Registre decisão relevante no artefato existente. |
| DEEP | Difícil reversão ou risco concreto de perda de dados, autorização, falha distribuída ou concorrência sutil | Até três opções pelos contratos; hipótese contrária, falhas, segurança, escala e reversibilidade. ADR para decisão arquitetural duradoura. |

Escolha a menor profundidade pelo comportamento, não por palavras como “pagamento”
ou quantidade de arquivos. Risco material em FAST recomenda DEEP com motivo breve;
após resolvê-lo, reduza profundidade. Urgência reduz escopo/resposta, não invariantes.
Preferências do usuário e regras do host prevalecem. Evidência insuficiente bloqueia
só a ação dependente; avance no trabalho independente autorizado.

## Compreender com o menor esforço suficiente

Use somente os passos necessários para resolver a lacuna atual; não são etapas,
perguntas ou campos obrigatórios da resposta. Em FAST, avance diretamente no trabalho
autorizado. [Fundamentos e limites](cognitive-foundations.md) são leitura sob demanda
para estudar ou revisar o protocolo; não os carregue para aplicar estas instruções.

1. **Delimitar:** resultado desejado → observado → diferença relevante → restrições
   → decisão necessária. Reutilize o que já está claro; “adicionar cache” é solução
   candidata, não descrição do problema. Separe requisito, restrição verificada,
   suposição e convenção. Reconstrua por primeiros princípios apenas a parte que
   não atende às restrições.
2. **Localizar a lacuna:** objetivo ambíguo pede esclarecer intenção; causa desconhecida
   pede observação; escolha de solução pede comparação por critérios. Consulte fontes
   pertinentes antes de perguntar. Para detalhe reversível dentro da autorização,
   adote o padrão existente ou uma suposição razoável e sinalize-a se afetar a entrega.
   Pergunte somente se a resposta mudar materialmente escopo, aceite, risco ou
   autorização e não puder ser obtida nas fontes disponíveis. Reúna lacunas relacionadas
   numa intervenção curta; reutilize respostas e aprovações. Preferência por rapidez
   não autoriza supor permissão nem requisito crítico: bloqueie só a parte dependente.
3. **Discriminar:** formule hipóteses plausíveis e a previsão observável de cada uma;
   selecione uma observação que as diferencie. Use até duas hipóteses iniciais em
   BALANCED, três em DEEP, sem preencher cotas. Evidência incompatível com todas pede
   revisar o enquadramento, não forçar uma vencedora. Sintoma e correlação não provam
   causa; compare condições equivalentes e possíveis fatores de confusão.
4. **Escolher a próxima evidência:** antes de leitura, pergunta ou teste, identifique
   qual resultado mudaria a próxima ação. Priorize poder de discriminação, impacto do
   erro, custo/latência e risco da verificação; não calcule scores sem dados. Se nenhum
   resultado mudar a ação, adie a investigação, preservando verificações obrigatórias
   e invariantes. Compare uma alternativa real quando a favorita depender só de
   familiaridade; aproveite comparações existentes.
5. **Atualizar:** separe fato com fonte, hipótese e inferência. Use histórico comparável
   quando houver; indique qual hipótese ganhou/perdeu suporte e o que permanece incerto.
   Logs, dashboard e relato derivados da mesma medição não são confirmações independentes.
   Evidência compatível com todas as hipóteses não desempata; ausência de falha não prova
   correção. Percentuais de confiança exigem base calibrada, não impressão subjetiva.
6. **Encerrar:** pare quando a evidência sustentar a próxima ação autorizada e o risco
   residual for compatível com sua reversibilidade. A entrega começa pela decisão/ação,
   seguida da evidência decisiva e da pendência que condiciona o avanço. Use um parágrafo
   curto para decisão simples; risco material recebe as condições de segurança e retomada
   necessárias. Referencie contexto já fornecido em vez de reapresentá-lo. Não espere
   certeza total para ação reversível suficiente nem declare diagnóstico pendente resolvido.

**Contexto e tokens:** leia só fontes/seções pertinentes ainda não válidas no contexto;
preserve versão e proveniência ao reutilizá-las. Agrupe consultas independentes quando
as ferramentas permitirem; mantenha dependências, mutações e reconciliação sequenciais.
Decomponha problemas maiores por contratos, invariantes e ownership. Registre uma única
síntese no artefato existente, atualizando apenas o que mudou. Sem gatilho, não emita
checklists, nomes de métodos/hooks, campos vazios ou pedidos de confirmação. Resposta
curta não dispensa evidência; não prometa economia sem medição do consumo total.

Escolha a menor solução que preserve invariantes, avaliando manutenção e custo
operacional, não só linhas/componentes. Considere latência, throughput, concorrência
e recuperação nas dimensões alteradas; não invente medições nem infraestrutura.
Em DEEP, mudanças em confiança, identidade ou persistência exigem invariante de
autorização/isolamento, inclusive na deduplicação, e validação pelo pilar Segurança.
Estas heurísticas não provam correção nem eliminam vieses.

## Contrato comum dos hooks cognitivos

Os oito nomes abaixo são contratos conceituais destinados ao módulo [Hooks](hooks.md).
Não são registrados nem executados automaticamente. Sem adapter verificado, a checagem
é manual; informe isso ao relatar um hook. Selecione somente o contrato pertinente,
sem segunda orquestração ou sequência obrigatória de chamadas. Todos se aplicam a
BALANCED/DEEP em qualquer modo operacional; exceções FAST estão indicadas abaixo.

**Inputs comuns:** objetivo/aceite, decisão/hipótese, modo, profundidade, restrições,
autorizações, evidências com fonte e versão/data disponíveis, lacunas e limites de
execução. Contexto mínimo, sem segredos/transcrições; dado ausente fica pendente.

**Output comum, apenas campos pertinentes:** `decision`, `depth`, `basis`
(fato com fonte, hipótese ou inferência), `alternatives`, `validation`
(refutação esperada e estado proposto/executado), `residual_risk`, `next_action`
e `status` (`sufficient`, `needs_evidence`, `blocked` ou `not_applicable`).
Resumo lógico, sem JSON ou novo arquivo obrigatório. `sufficient` recomenda o próximo
passo; não aprova gate nem prova correção. Sem gatilho, encerre silenciosamente.

**Limite transversal:** uma passagem por decisão/conjunto de evidências; agrupe
checagens e reutilize saídas. Reabrir exige evidência nova, requisito/risco alterado
ou insumo antes ausente. Após duas tentativas sem progresso, aplique [recuperação](workflow.md)
sem zerar contagem por hook/profundidade. Ao esgotar prazo/budget do host, entregue
estado e próxima ação, sem conclusão artificial.

Sem fan-out obrigatório, consultas externas automáticas ou teto garantido de consumo.
Executor futuro herda timeout, cancelamento, concorrência, identificação de tentativa
e falhas de Hooks. Checagem falha não aprova gate; efeito externo incerto exige
reconciliação antes de retry. Reabrir decisão não autoriza repetir efeitos.

### `reasoning.challenge`

- **Trigger:** objetivo ambíguo, requisito contraditório ou conclusão que depende de premissa sem suporte.
- **Inputs:** comuns + premissa decisiva e restrição possivelmente violada.
- **Procedimento:** delimite resultado desejado, observado, diferença, restrições e decisão. Localize a lacuna e aplique a regra de esclarecimento do ciclo acima; separe causa de sintoma.
- **Output:** problema delimitado, premissa corrigida ou pergunta material ainda sem resposta.
- **Limite:** uma premissa decisiva por passagem; reúna apenas esclarecimentos bloqueantes relacionados, sem sequência de perguntas sobre detalhes reversíveis.
- **Encerramento:** objetivo suficiente para avançar ou dependência explicitamente bloqueada, com condição de retomada.
- **FAST:** ambiguidade material recomenda reclassificação, sem questionário.

### `assumptions.validate`

- **Trigger:** decisão depende de comportamento, capacidade ou restrição não verificados.
- **Inputs:** comuns + premissas ordenadas pelo impacto de estarem erradas.
- **Procedimento:** classifique requisito, restrição verificada, suposição ou convenção; confronte os decisivos com fonte atual ou teste escolhido pelo efeito sobre a próxima ação. Preserve a origem comum de evidências derivadas.
- **Output:** premissas sustentadas, refutadas ou desconhecidas, com evidência e validação pendente.
- **Limite:** até duas premissas em BALANCED, três em DEEP; uma checagem discriminante por premissa por passagem. Se restar premissa bloqueante, delimite nova unidade de trabalho ou registre impedimento; não a ignore para caber no limite.
- **Encerramento:** nenhuma premissa decisiva fica implicitamente aceita; lacunas têm próxima ação e responsável quando conhecido.

### `alternatives.compare`

- **Trigger:** escolha com trade-off relevante ou primeira solução adotada sem critério.
- **Inputs:** comuns + opções viáveis e critérios de aceite afetados.
- **Procedimento:** explore opções, incluindo manter o estado atual quando viável; selecione por contrato, manutenção, desempenho, falhas e reversibilidade pertinentes. Elimine opção que viole invariante antes de comparar custos.
- **Output:** escolha ou experimento que desempate, com diferença decisiva entre opções.
- **Limite:** duas opções em BALANCED, três em DEEP, uma rodada de comparação; não invente alternativa inviável para cumprir quantidade.
- **Encerramento:** opção suficiente selecionada ou evidência de desempate especificada.

### `bias.challenge`

Questionar vieses de engenharia não comprova equidade: impactos assimétricos exigem
[avaliação de domínio](ai-safety-ethics.md#ai-products), dados permitidos e limites.
Inclua afetados, finalidade e menor exposição quando materiais; não infira dano
ou neutralidade sem evidência.

- **Trigger:** justificativa baseada em familiaridade, primeira proposta ou seleção apenas de evidências favoráveis.
- **Inputs:** comuns + opção preferida e justificativa observável.
- **Procedimento:** procure contraevidência e teste a adequação de uma alternativa real; confronte o padrão familiar com a restrição atual. Reutilize comparação já feita.
- **Output:** evidência contrária encontrada ou busca inconclusiva, e efeito sobre a decisão.
- **Limite:** um contraexemplo ou uma alternativa por passagem, sem auditoria psicológica da pessoa.
- **Encerramento:** preferência sustentada, revisada ou dependente de evidência identificada; ausência de contraexemplo não prova ausência de viés.

### `hypothesis.falsify`

- **Trigger:** diagnóstico causal ou decisão importante depende de hipótese ainda não refutada.
- **Inputs:** comuns + hipótese, invariante afetada e observação discriminante disponível.
- **Procedimento:** para as hipóteses concorrentes, explicite previsão e refutação antes do teste discriminante; atualize suporte e incerteza após o resultado. Em concorrência/integrações, cubra duplicidade, timeout, interrupção e recuperação pertinentes.
- **Output:** cenário, resultado que refutaria a hipótese e evidência observada ou teste proposto, incluindo limitações do ambiente.
- **Limite:** um cenário discriminante por hipótese por passagem; isso não limita a suíte necessária às invariantes, definida pelas políticas e pelo gate.
- **Encerramento:** hipótese refutada, ainda compatível com evidências ou sem validação; nunca “provada” por ausência de falha.
- **Execução:** testes dependem das ferramentas e autorizações existentes.

### `complexity.reduce`

- **Trigger:** mecanismo, dependência ou abstração não tem necessidade demonstrada, ou custo operacional supera o benefício.
- **Inputs:** comuns + solução candidata, invariantes e custos conhecidos.
- **Procedimento:** compare com a menor alternativa suficiente; avalie carga cognitiva, manutenção, latência, throughput e recuperação afetados. Preserve proteções necessárias.
- **Output:** simplificação concreta ou motivo verificável para manter a complexidade.
- **Limite:** uma simplificação candidata por passagem, aproveitando alternativas já examinadas.
- **Encerramento:** contrato preservado com redução justificável, ou simplificação rejeitada por risco/custo total.
- **FAST:** checagem breve, sem chamada obrigatória.

### `reasoning.reflect`

- **Trigger:** fim de investigação, contradição nova ou tentativa sem progresso.
- **Inputs:** comuns + resultados das checagens e tentativas já feitas.
- **Procedimento:** sintetize apenas o que mudou no conhecido, inferido e incerto; identifique próxima ação controlável ou dependência externa. Preserve contratos e fontes úteis para retomada, sem recapitular o histórico.
- **Output:** resumo curto de estado, risco residual e próximo passo ou bloqueio.
- **Limite:** um resumo por passagem, sem recapitular o histórico; não inicia investigação recursiva.
- **Encerramento:** próxima ação definida ou impedimento com condição de retomada; preserve o limite transversal de tentativas.
- **FAST:** somente diante de falha ou incerteza relevante.

### `decision.capture`

- **Trigger:** decisão relevante precisa orientar implementação, review ou retomada; mudança arquitetural duradoura exige rastreabilidade.
- **Inputs:** comuns + decisão selecionada, alternativas relevantes e condição de reavaliação.
- **Procedimento:** registre uma síntese no artefato existente; para decisão arquitetural duradoura use o [template ADR](../assets/templates/adr.md). Mantenha `proposed` até satisfazer a aprovação requerida pelo host/projeto; reutilize aprovação já concedida.
- **Output:** registro ou proposta de registro com fontes, consequências, validação e condição de reabertura.
- **Limite:** um registro por decisão, atualizado em vez de duplicado; persistência depende do escopo autorizado.
- **Encerramento:** registro acessível no local autorizado, ou pendência explícita; não abre novo debate por conta própria.
- **FAST:** somente registro já exigido pelo projeto, sem ADR adicional.

## Recomendações aos consumidores

Encaminhe só o resumo pertinente, referenciando evidências existentes. Architecture
Gate e Review Council são pontos lógicos, não novos serviços; cada consumidor
mantém seus critérios, execução e autorizações.

| Consumidor | Encaminhamento |
| --- | --- |
| [Planejamento e modo operacional](workflow.md) | Lacuna material → Explore; contrato/alternativa a definir → Plan; decisão suficiente e autorização → Build; incremento revisável → Review. Autonomous preserva essas condições. Sem troca automática de modo/modelo. |
| Architecture Gate — `architecture.guard` em [Hooks](hooks.md) | Invariantes, trade-offs, compatibilidade, reversibilidade e pendências; recomendação não aprova gate. |
| Review Council em [Agentes](agents.md) | Apenas pilares afetados, diff e fontes; hipótese do autor rotulada, sem impor conclusão ao revisor independente. |
| [Seleção de testes](policies.md) | Hipótese, refutação e invariantes; carga equivalente, saturação, concorrência e recuperação quando pertinentes. Separar proposto de executado. |
| [ADR](../assets/templates/adr.md) | Decisão duradoura, alternativas, fontes, riscos e condição de reavaliação; sem transcrições privadas ou memória persistida sem autorização. |

## Aceite observável

FAST entrega alteração trivial sem cerimônia nem perguntas dispensáveis. BALANCED
formula o problema, escolhe evidência discriminante e encerra investigação sem novidade.
DEEP preserva refutação, autorização, reversibilidade, isolamento e recuperação.
Saída suficiente: “Espera no pool domina a amostra local; medir ocupação das conexões
antes de escolher cache; produção ainda não validada”. Mutação externa de resultado
incerto exige reconciliação antes de retry, mesmo sob pressão de prazo.
