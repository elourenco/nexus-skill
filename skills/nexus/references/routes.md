# Índice de rotas

Selecione pela entrega autorizada, não por palavras isoladas. Cada linha é um
atalho interno, sem novo comando, perfil ou estado. Entradas especializadas pulam
este índice. O [contrato mínimo](invocation.md) é obrigatório em todas as rotas;
reutilize-o quando já estiver válido no contexto.

## Destinos obrigatórios

| Rota | Pedido | Ler junto do contrato mínimo |
| --- | --- | --- |
| status | Informar progresso, validação ou bloqueio | [Status](status.md) e fonte de estado pertinente |
| review | Avaliar objeto definido | [Procedimento](review.md), [critérios](review-criteria.md) e objeto/fontes |
| build.fast | Alteração conhecida que satisfaz todos os critérios FAST | [Build — FAST](build.md#fast), [inspeção](build.md#inspeção-e-ferramentas) e arquivos afetados |
| build | Implementação ou contrato que excede FAST | [Build](build.md) e plano existente, se houver |
| debug | Diagnóstico ou correção de bug | [Debug](debug.md) e evidências do sintoma |
| plan | Detalhar direção definida | [Plan](plan.md) |
| explore | Explorar alternativas ou iniciar feature | [Brainstorming](brainstorming.md), limitado à entrega pedida |
| resume | Retomar execução autorizada | [Workflow — retomada](workflow.md#checkpoint-cancelamento-e-retomada), fonte existente e procedimento da próxima pendência |

## Expansões condicionais

Só siga a ligação quando a decisão ainda precisar do detalhe. Uma referência
na seção carregada não torna todas as suas dependências obrigatórias.

| Gatilho concreto | Destino |
| --- | --- |
| Risco/classificação ainda incertos | [Perfis](policies.md#policy-execution) |
| Estratégia de teste não resolvida pelo mínimo | [Testes](policies.md#policy-testing) |
| Regra de conclusão ou exceção ambígua | [Conclusão](policies.md#policy-completion), [autoridade](policies.md#policy-authority) |
| Budget, retry ou efeito externo incerto exigem detalhe | [Limites](policies.md#limites-suaves-e-rígidos), [recuperação](policies.md#tentativas-e-recuperação) |
| Hipótese fraca ou decisão material em aberto | [Ciclo cognitivo](cognitive.md#seleção-adaptativa) |
| Delegação efetiva ou definição de método | [Agents](agents.md) |
| Etapas/estado a reconciliar | [Workflow](workflow.md); [executor](workflow-state.md) somente se adotado |
| Estados, ownership ou invariantes alterados | [Modelagem](domain-design.md) |
| Decisão estrutural aberta / refatoração com efeitos | [Design](architecture-design.md) / [Refatoração](refactoring.md) |
| Confiança, dados sensíveis, autonomia, produto com IA ou impacto humano material | [Segurança e ética](ai-safety-ethics.md#risk-triggers) |
| Escolhas interativas ou acompanhamento complexo | [Chat](chat.md) |

## Referências informativas

Exemplos e proveniência não exigem carregamento. [Templates](../assets/templates/contracts.md)
só ao produzir o artefato correspondente; [instalação](installation.md),
[hooks](hooks.md) e [memória](memory.md) somente quando o helper for solicitado ou necessário.

Encerre a navegação quando as fontes atuais bastarem à decisão e aos gates.
Referência obrigatória ausente bloqueia o fluxo dependente; não simule seu conteúdo.
