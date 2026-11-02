# Contrato das entradas NEXUS

Leia este contrato ao usar uma entrada especializada ou seu procedimento pelo
núcleo. Carregue apenas o procedimento selecionado; não encadeie o catálogo inteiro.

## Dependências e autoridade

As entradas `nexus-*` dependem da pasta irmã `nexus/` da mesma distribuição.
Resolva os links relativamente ao arquivo da skill, nunca ao workspace consumidor.
Se faltar este contrato ou o procedimento selecionado, informe o caminho ausente
e interrompa esse fluxo NEXUS. Não substitua silenciosamente por outra instalação,
não simule a leitura e não instale dependências globais. O núcleo `nexus` pode ser
instalado sozinho e contém todos os procedimentos.

Leia [Policies](policies.md#policy-authority) para autoridade, perfil e validação.
Reaproveite instruções, decisões e autorizações existentes para o mesmo alvo e
escopo. A entrada explicita a atividade; o pedido do usuário delimita os efeitos.
Uma chamada a build sem objetivo suficiente não autoriza inventar alterações;
review não implica correção. Instruções do host prevalecem.

## Seleção e continuidade

- Uma entrada específica seleciona seu procedimento diretamente; não recarregue
  `nexus/SKILL.md` para redescobrir o modo nem invoque outra skill como ritual.
- No núcleo geral, selecione pela entrega pedida. Brainstorming explora problema
  e alternativas; Plan organiza uma direção definida. Pedido composto percorre
  somente as etapas necessárias e já autorizadas, sem pedir aprovação novamente.
- Se nome e pedido divergirem materialmente (por exemplo, build com “somente
  planeje”), respeite o limite do pedido e explique o modo efetivo. Pergunte apenas
  quando a ambiguidade impedir uma decisão de escopo segura.
- FAST/BALANCED/DEEP definem profundidade. Explore/Plan/Build/Review definem
  atividade. Os nomes das entradas não criam estados nem novos perfis.
- Execute no agente atual por padrão. Delegue apenas com ganho concreto e
  capacidade/autorização do host, conforme [Agents](agents.md). Paralelismo exige
  tarefas independentes e recursos isolados; não aumente concorrência por comando.
- Para tarefas, status ou retomada, use a fonte de estado existente conforme
  [Workflows](workflow.md). Não inicialize outro store nem acione helpers, hooks ou
  memória automaticamente. Resultado externo incerto exige reconciliação antes
  de retry; status `running` sozinho não prova que o processo terminou.

## Entrega comum

Informe resultado, evidências e limitações, arquivos alterados (ou nenhum),
verificações realmente executadas e próxima ação quando pendente. Uma análise pode
terminar com hipótese ou decisão aberta; não apresente inferência como execução.
Use templates apenas quando o artefato for necessário. Resposta no chat é válida
e não implica persistência; ausência de persistência deve ficar explícita quando
o pedido depender de estado salvo.
