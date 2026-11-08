# Revisão — Review

Use para avaliar diff, implementação, contrato ou solução existente contra seu
objetivo e aceite. Aplica-se o [contrato de invocação](invocation.md). Uma escolha
arquitetural ainda em aberto pertence a Explore/Plan; revisão avalia um objeto definido.

## Procedimento

**Entrada:** alvo/base e critérios. **Decisão:** defeitos demonstráveis e cobertura.
**Evidência:** diff/fontes e verificações observadas. **Saída:** achados, limites e
decisão; nunca autorização implícita para corrigir ou publicar. Para handoff por
arquivo, use a [coleta opcional](review-package.md).

1. Identifique alvo, revisão/base do diff, requisitos e critérios. Para WIP, inclua
   staged/unstaged e identifique untracked incluídos/omitidos; diff até HEAD não
   cobre alterações locais. Fixe SHAs para commits, ou identidade do snapshot/diff
   para worktree; revalide se houver escrita concorrente. Leia artefato e
   fontes pertinentes diretamente, sem depender da narrativa do implementador.
   Se faltar o objeto revisável, obtenha-o nas fontes disponíveis ou peça o insumo;
   não invente achados a partir de uma descrição genérica.
   Se houver contrato material ambíguo ou omitido no handoff, reconstrua das fontes
   normativas o comportamento exigido, a invariante e um cenário que distinguiria
   a implementação correta da incorreta; confronte então código e testes. Faça
   isso dentro deste review, sem paráfrase integral, novo agente ou fase obrigatória.
   Interpretação divergente pode ser erro do leitor: confira a autoridade e a
   evidência antes de atribuir defeito à SPEC; não use a intenção do autor como
   único critério de correção.
2. Selecione os pilares de [critérios de review](review-criteria.md#review-council-adaptativo) pelo comportamento alterado.
   Avalie contratos, falhas parciais, latência, throughput e concorrência quando
   pertinentes. Preserve achados existentes e diferencie defeito demonstrável,
   hipótese e preferência de estilo.
   Confira divergências de documentação na fronteira afetada: requisito vigente,
   produtor, consumidor e teste pertinentes. Diferencie documento desatualizado,
   implementação incompleta, mudança aprovada e proposta ainda não implementada;
   ausência de item planejado não é defeito por si. Teste verde que repete o código
   não resolve conflito com o requisito. Amplie a busca só por dependência ou
   lacuna concreta, preservando a cobertura exigida e os limites do escopo.
3. Execute verificações proporcionais nas ferramentas e recursos autorizados,
   isolando artefatos temporários. Não edite o objeto para facilitar o review;
   registre testes não executados e lacunas de cobertura. Se o alvo mudar durante
   a avaliação, reconcilie a revisão e invalide conclusões afetadas.
4. Para cada achado acionável, informe severidade, arquivo/linha quando aplicável,
   condição de reprodução, impacto, evidência, confiança e recomendação. Demonstre um caso que distinguiria o defeito de um falso positivo. Não use
   quantidade de achados nem aprovação por votação como prova de qualidade.
5. Consolide a decisão conforme [critérios](review-criteria.md#contrato-de-saída-e-decisão):
   APPROVED, CHANGES_REQUESTED, BLOCKED ou INCONCLUSIVE, respeitando cobertura e
   critérios efetivamente verificados. Independência só pode ser declarada quando
   real; revisão pelo próprio implementador não satisfaz gate independente.

## Entrega e limite

Em mudança estrutural, use [design](architecture-design.md#diagnostico) para conferir
dependências e consequências demonstráveis. Em refatoração com efeitos/contratos,
use [preservação](refactoring.md#contrato) e os [riscos operacionais](refactoring.md#efeitos)
pertinentes: compare semântica, não só assinaturas. Fakes não demonstram garantias
do storage real. Essas consultas não autorizam redesenhar ou corrigir o objeto.

Pelos [gatilhos de segurança e ética](ai-safety-ethics.md#risk-triggers), confira
fronteiras/dados, autonomia e impacto humano no alvo real. Em produto com impacto
material, examine responsável capaz de intervir, revisão/contestação, transparência,
acessibilidade e erros assimétricos pertinentes. Diferencie controle recomendado,
implementado e verificado; amostra insuficiente mantém a conclusão limitada.
Avaliação de mesa não comprova resistência a ataques nem equidade em produção.

Entregue primeiro achados priorizados ou a ausência de achados demonstrados,
seguida de cobertura, verificações, limitações e decisão. Declare proveniência,
confiança e limitações comuns uma vez quando forem iguais. Cada achado preserva
severidade, localização, trigger, impacto, evidência e correção; explicite confiança,
proveniência e status quando diferirem. Preserve todos os campos do contrato
rastreado quando adotado. Use o
[template de review](../assets/templates/review.md) quando um registro for necessário.
Não confunda relatório concluído com aprovação do objeto; achados podem permanecer
abertos ao concluir uma tarefa exclusivamente de análise.

Review sem pedido de correção termina no relatório. Quando o usuário também pedir
correções, conclua a avaliação do alvo antes de passar a Build, preserve o escopo
autorizado e revalide o diff alterado. A decisão de review não autoriza publicação.

Exemplo: “NEXUS review: revise este diff de retry após timeout, sem corrigir.”
Relacione a condição de duplicação ao contrato do destino e ao trecho alterado;
se a deduplicação não puder ser verificada, explicite a incerteza.
