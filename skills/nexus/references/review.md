# Revisão — Review

Use para avaliar diff, implementação, contrato ou solução existente contra seu
objetivo e aceite. Aplica-se o [contrato de invocação](invocation.md). Uma escolha
arquitetural ainda em aberto pertence a Explore/Plan; revisão avalia um objeto definido.

## Procedimento

1. Identifique alvo, revisão/base do diff, requisitos e critérios. Leia artefato e
   fontes pertinentes diretamente, sem depender da narrativa do implementador.
   Se faltar o objeto revisável, obtenha-o nas fontes disponíveis ou peça o insumo;
   não invente achados a partir de uma descrição genérica.
2. Selecione os pilares de [Agents & Review](agents.md) pelo comportamento alterado.
   Avalie contratos, falhas parciais, latência, throughput e concorrência quando
   pertinentes. Preserve achados existentes e diferencie defeito demonstrável,
   hipótese e preferência de estilo.
3. Execute verificações proporcionais nas ferramentas e recursos autorizados,
   isolando artefatos temporários. Não edite o objeto para facilitar o review;
   registre testes não executados e lacunas de cobertura. Se o alvo mudar durante
   a avaliação, reconcilie a revisão e invalide conclusões afetadas.
4. Para cada achado acionável, informe severidade, arquivo/linha quando aplicável,
   condição de reprodução, impacto, evidência, confiança e recomendação. Não use
   quantidade de achados nem aprovação por votação como prova de qualidade.
5. Consolide a decisão conforme [Agents](agents.md#contrato-de-saída-e-decisão):
   APPROVED, CHANGES_REQUESTED, BLOCKED ou INCONCLUSIVE, respeitando cobertura e
   critérios efetivamente verificados. Independência só pode ser declarada quando
   real; revisão pelo próprio implementador não satisfaz gate independente.

## Entrega e limite

Entregue primeiro achados priorizados ou a ausência de achados demonstrados,
seguida de cobertura, verificações, limitações e decisão. Use o
[template de review](../assets/templates/review.md) quando um registro for necessário.
Não confunda relatório concluído com aprovação do objeto; achados podem permanecer
abertos ao concluir uma tarefa exclusivamente de análise.

Review sem pedido de correção termina no relatório. Quando o usuário também pedir
correções, conclua a avaliação do alvo antes de passar a Build, preserve o escopo
autorizado e revalide o diff alterado. A decisão de review não autoriza publicação.

Exemplo: “NEXUS review: revise este diff de retry após timeout, sem corrigir.”
Relacione a condição de duplicação ao contrato do destino e ao trecho alterado;
se a deduplicação não puder ser verificada, explicite a incerteza.
