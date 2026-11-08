# Planejamento — Plan

Use quando houver uma direção a detalhar em contratos, etapas e validação.
Aplica-se o [contrato de invocação](invocation.md). Preserve decisões já tomadas;
reabra somente as contraditas por novas evidências ou restrições materiais.

## Procedimento

**Entrada:** direção e restrições existentes. **Decisão:** contratos, sequência e
ownership. **Evidência:** fontes e validações propostas identificadas como tais.
**Saída:** etapas verificáveis; aceite de planejamento não comprova implementação.

1. Consulte objetivo, fontes atuais, SPEC/ADR/plano existente e escopo autorizado.
   Sem direção suficiente, delimite a decisão pendente e use
   [brainstorming](brainstorming.md) apenas para resolvê-la. Lacunas independentes
   não impedem planejar o restante.
2. Decomponha no plano ou fonte existente. Consulte [Workflows](workflow.md) somente
   para resolver ownership, acompanhamento, retomada ou estado ainda indefinidos;
   a mera existência de passos não exige outro procedimento. Persistência nova
   somente se útil ou solicitada. Defina
   contratos, invariantes, critérios de aceite e compatibilidade nas fronteiras alteradas. Execução direta pode registrar decisões no chat, sem TASK/SPEC/PLAN ou estado obrigatório; a CLI opt-in conserva seu contrato.
3. Prefira slices verticais demonstráveis, com critério/invariante → cenário →
   evidência. Para migração incompatível, explicite expandir contrato, migrar em
   lotes e remover legado somente após compatibilidade comprovada; etapas que
   não ficam verdes isoladamente precisam de integração final identificada.
   Decomponha em incrementos verificáveis: arquivos ou componentes afetados,
   dependências, ownership, validação e condição de conclusão. Trate latência,
   throughput, concorrência e falhas conforme o comportamento; reserve recursos
   compartilhados antes de propor execução paralela.
   Em repositório Git, defina base/destino, branch/worktree do plan, incrementos
   de commit, ownership e integração conforme a [política Git](git.md). Separe
   autorização de implementar, comitar e integrar; não fixe nomes globais nem
   crie branch por task sequencial. Registre decisões na fonte existente.
4. Inclua migração, rollout compatível e recuperação quando pertinentes. Distinga
   rollback de código de reversão de dados/efeitos. Nomeie hipóteses, bloqueios e
   verificações ainda necessárias; não estime desempenho sem dados.

## Entrega e limite

Decisão pendente sobre módulos, dependências ou integração usa
[design](architecture-design.md); estados/invariantes afetados usam
[modelagem](domain-design.md). Para refatoração que afete contratos ou efeitos,
use [preservação e incrementos](refactoring.md#contrato) para definir caracterização,
transformação e evidência. Reutilize decisões suficientes; isso não cria uma fase
de arquitetura para todo plano nem amplia o escopo aprovado.

Para [produtos com IA](ai-safety-ethics.md#ai-products), inclua no plano existente
fronteiras de confiança, dados/destinos permitidos, controles e responsáveis,
supervisão pertinente e cenários de falha. Vincule aceite à evidência necessária;
uma aprovação se refere ao alvo definido, e mudança material exige revalidação.
Planeje limites agregados, latência e recuperação dos controles conforme o risco,
sem impor chamadas adicionais a modelos ou métricas universais de equidade.

Entregue objetivo/escopo, decisões preservadas, etapas com dependências, aceite,
estratégia de validação, riscos/recuperação e pendências. Use o
[template de plano](../assets/templates/plan.md) se houver necessidade de arquivo,
vinculando fontes e revisões conhecidas; não invente hashes ou aceites.
Para revisão da SPEC/PLAN, siga a [apresentação em painel nativo](chat.md#spec-e-plano-em-painel-nativo):
documento organizado por seções e entregas numeradas, abertura no recurso permitido
do host e resumo com links no chat. Preserve o arquivo de plano nativo já adotado.

Se o pedido for somente planejar, entregue o plano e encerre sem exigir escolha
de execução nem apresentar seu aceite como autorização para implementar.
No [fluxo guiado iniciado por brainstorming](brainstorming.md#fluxo-guiado-por-aceites)
que continuará até a implementação,
apresente o plano junto das opções **subagentes** e **agente único**, com recomendação
justificada e capacidades/limitações verificadas conforme [Agents](agents.md#metodo-de-execucao).
Reutilize escolha explícita existente. Quando o método ainda estiver pendente,
apresente método recomendado e efeito do aceite na mesma proposta: “Recomendo
agente único; aprovar este plano autoriza implementar, testar e revisar localmente
com esse método; você pode escolher subagentes”. Nesse caso, aprovação sem ressalva
aceita o método apresentado. Se a proposta deixou ambas as opções abertas sem
vincular método ao aceite, esclareça só essa lacuna. Silêncio não seleciona método. Se o usuário delegar a escolha, adote a recomendação
compatível e informe o método efetivo. Explique que o aceite para executar cobre
implementação, testes, correções no escopo e review locais; sem nova invocação.

Se o plano já foi aprovado e o pedido é executar, retome a próxima pendência autorizada, sem novo brainstorming/plano salvo evidência ou mudança material. Planejar isoladamente não autoriza implementar. Quando o pedido incluir execução e as decisões
necessárias estiverem resolvidas, continue em Build dentro da autorização existente.
Uma lacuna que altere contrato ou risco bloqueia somente a ação dependente.

Exemplo: “NEXUS plan: versão otimista já escolhida; planeje resposta 409 e preservação
da edição local.” Preserve a escolha e detalhe atualização atômica, contrato do
conflito e cenários de concorrência, em vez de rediscutir toda a arquitetura.
