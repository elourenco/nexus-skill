# Implementação — Build

Use para implementar, refatorar, documentar ou criar testes dentro do escopo
solicitado. Aplica-se o [contrato de invocação](invocation.md).

## Procedimento

**Entrada:** objetivo, aceite e autorização. **Decisão:** menor incremento válido.
**Evidência:** verificações executadas sobre o alvo atual. **Saída:** alteração
revisável e pendências; check obrigatório ausente mantém o aceite pendente.

1. Identifique objetivo, aceite e autorização existentes. Inspecione instruções do
   projeto, estado real dos arquivos e plano quando houver; preserve trabalho alheio.
   Plano aprovado conduz à próxima pendência; não refaça brainstorming/plano sem nova evidência ou mudança material. Execução direta não exige TASK/SPEC/PLAN nem store, independentemente do perfil de risco. Se faltar contrato
   material, resolva-o em [Plan](plan.md) antes da alteração dependente.
2. Consulte [Workflows](workflow.md) quando houver etapas, tarefas ou retomada.
   Reuse sua fonte existente; crie persistência somente se útil ou solicitada, sem lista paralela. Antes de retomar run
   incerto, reconcilie com o host para evitar execução duplicada.
3. Agrupe edições relacionadas em um incremento revisável antes dos checks, preservando pontos intermediários exigidos pela estratégia definida em
   [Policies](policies.md#policy-testing). Para bug, reproduza a falha; para
   invariantes críticas testáveis, observe a regressão antes e depois da correção.
   Texto ou mudança simples admite inspeção proporcional. Use ferramentas reais.
4. Valide aceites e efeitos sobre contratos, latência, throughput, concorrência e
   recuperação conforme o comportamento alterado. Não paralelize escritas ou testes
   sobre recursos compartilhados. Se houver falha, preserve evidências e respeite
   limites de tentativas/recuperação; não transforme teste não executado em sucesso.
5. Revise o diff e os pilares pertinentes conforme [Agents](agents.md) quando o
   risco exigir. Reuse check/review válido para os mesmos inputs, revisão, configuração, run/geração aplicáveis e ambiente; repita a cobertura afetada por mudança relevante, novo risco ou integração não coberta. Gates de conclusão continuam vigentes. Independência e agentes adicionais dependem do host; uma entrada
   especializada não cria um worker automaticamente.

## Entrega e limite

Entregue resultado implementado, arquivos alterados, verificações e resultados,
decisões materiais e pendências. Conclusão exige aceite comprovado; ferramenta
ausente ou verificação obrigatória bloqueada permanece limitação explícita.

Continue o trabalho local já autorizado até seu aceite, sem solicitar novamente
aprovação do mesmo plano. Commit, push, merge, deploy e outras ações externas
dependem da autorização correspondente, não da chamada a build.

Exemplo: “NEXUS build: implemente o plano aprovado e valide localmente; não publique.”
Execute implementação e testes dentro desse escopo e informe a evidência obtida.
