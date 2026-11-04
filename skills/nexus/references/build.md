# Implementação — Build

Use para implementar, refatorar, documentar ou criar testes dentro do escopo
solicitado. Aplica-se o [contrato de invocação](invocation.md).

## FAST

Use somente com escopo conhecido, baixo impacto, reversibilidade e sem alteração
de contrato/fronteira ou invariante crítica, conforme o contrato mínimo.
Inspecione instruções e arquivos afetados, faça o menor incremento, confira o diff
e execute a verificação pertinente sobre a versão final. Preserve trabalho alheio.
Não crie plano, TASK, testes artificiais ou carregue Policies por ritual. Se surgir
incerteza ou risco maior, reclassifique antes da alteração afetada e siga abaixo.
Os checks obrigatórios e os gates do projeto continuam valendo.

## Inspeção e ferramentas

Determine uma vez se Git está disponível no workspace. Sem repositório, use cópia
inicial identificada e comparação do antes/depois; comparar dois arquivos finais
entre si não é diff da alteração. Não repita um comando sabidamente indisponível nem
condicione leitura necessária ao sucesso de Git. Se a ausência for transitória,
só retente com condição alterada e dentro dos limites. Preserve falhas relevantes.
Consolide diff e preservação dos documentos aprovados no estado final, após a última
edição; mantenha verificações intermediárias quando risco ou estratégia exigir.

## Procedimento

**Entrada:** objetivo, aceite e autorização. **Decisão:** menor incremento válido.
**Evidência:** verificações executadas sobre o alvo atual. **Saída:** alteração
revisável e pendências; check obrigatório ausente mantém o aceite pendente.

1. Identifique objetivo, aceite e autorização existentes. Inspecione instruções do
   projeto, estado real dos arquivos e plano quando houver; preserve trabalho alheio.
   Plano aprovado conduz à próxima pendência; não refaça brainstorming/plano sem nova evidência ou mudança material. Execução direta não exige TASK/SPEC/PLAN nem store, independentemente do perfil de risco. Se faltar contrato
   material, resolva-o em [Plan](plan.md) antes da alteração dependente.
   No fluxo guiado de brainstorming, preserve os aceites e o
   [método escolhido](agents.md#metodo-de-execucao); se somente essa escolha faltar,
   resolva-a sem reapresentar o plano aprovado. Execute no método efetivo, sem
   criar sessões ou workers no modo agente único.
2. Consulte [Workflows](workflow.md) quando houver etapas, tarefas ou retomada.
   Reuse sua fonte existente; crie persistência somente se útil ou solicitada, sem lista paralela. Antes de retomar run
   incerto, reconcilie com o host para evitar execução duplicada.
3. Vincule critério/invariante a cenário e evidência observável no registro
   existente. Teste por comportamento com expectativa independente do algoritmo;
   em TDD seletivo, complete um ciclo falha → implementação → sucesso antes de
   ampliar o próximo comportamento. Agrupe edições relacionadas em um incremento revisável antes dos checks, preservando pontos intermediários exigidos pela estratégia definida em
   [Policies](policies.md#policy-testing). Para bug, reproduza a falha; para
   invariantes críticas testáveis, observe a regressão antes e depois da correção.
   Texto ou mudança simples admite inspeção proporcional. Use ferramentas reais.
4. Valide aceites e efeitos sobre contratos, latência, throughput, concorrência e
   recuperação conforme o comportamento alterado. Não paralelize escritas ou testes
   sobre recursos compartilhados. Se houver falha, preserve evidências e respeite
   limites de tentativas/recuperação; não transforme teste não executado em sucesso.
5. Revise o diff e os pilares pertinentes conforme os [critérios](review-criteria.md) quando o
   risco exigir. Reuse check/review válido para os mesmos inputs, revisão, configuração, run/geração aplicáveis e ambiente; repita a cobertura afetada por mudança relevante, novo risco ou integração não coberta. Gates de conclusão continuam vigentes. Independência e agentes adicionais dependem do host; uma entrada
   especializada não cria um worker automaticamente.

## Entrega e limite

Para refatoração que afete responsabilidades, contratos ou efeitos, siga
[Refactoring](refactoring.md), preservando decisões do plano e verificando a versão
final. Estados/invariantes alterados usam [Modelagem](domain-design.md). Consulte
[Design](architecture-design.md) somente se houver decisão estrutural ainda aberta;
mudança mecânica local com equivalência clara mantém este fluxo curto.

Quando pertinente, implemente os controles de [segurança e ética](policies.md#policy-ai-safety-ethics)
definidos no aceite: valide saídas de IA no ponto de uso e autorização no executor,
preservando isolamento e minimização. Se um controle indispensável estiver ausente
ou falhar, suspenda somente o efeito dependente e mantenha o trabalho autorizado
independente. Não apresente instrução no prompt como controle técnico verificado.

Entregue resultado implementado, arquivos alterados, verificações e resultados,
decisões materiais e pendências. Conclusão exige aceite comprovado; ferramenta
ausente ou verificação obrigatória bloqueada permanece limitação explícita.

Continue o trabalho local já autorizado até seu aceite, sem solicitar novamente
aprovação do mesmo plano. Commit, push, merge, deploy e outras ações externas
dependem da autorização correspondente, não da chamada a build.

Exemplo: “NEXUS build: implemente o plano aprovado e valide localmente; não publique.”
Execute implementação e testes dentro desse escopo e informe a evidência obtida.
