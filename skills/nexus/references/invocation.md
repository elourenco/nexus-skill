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

Consulte [Policies](policies.md#policy-authority) por seção: autoridade, perfil, testes e conclusão pertinentes. Reutilize leituras válidas para a revisão e contexto atuais; não carregue o catálogo inteiro a cada entrada.
Reaproveite instruções, decisões e autorizações existentes para o mesmo alvo e
escopo. A entrada explicita a atividade; o pedido do usuário delimita os efeitos.
Uma chamada a build sem objetivo suficiente não autoriza inventar alterações;
review não implica correção. Instruções do host prevalecem.

Aplique os invariantes de [segurança e ética em IA](policies.md#policy-ai-safety-ethics)
em todas as entradas. Carregue a [referência detalhada](ai-safety-ethics.md#risk-triggers)
somente pelos gatilhos: fronteiras de confiança, acesso/destino de dados sensíveis,
autonomia de ferramentas, comportamento de produto com IA ou impacto humano material.
Isso preserva FAST e não acrescenta confirmação a ações já autorizadas.

## Seleção e continuidade

- Uma entrada específica seleciona seu procedimento diretamente; não recarregue
  `nexus/SKILL.md` para redescobrir o modo nem invoque outra skill como ritual.
- Ao iniciar por brainstorming, use o [fluxo guiado por aceites](brainstorming.md#fluxo-guiado-por-aceites)
  como padrão: conduza as transições internamente, sem exigir novas invocações.
  Aceites em linguagem natural referem-se à proposta e aos efeitos apresentados;
  preserve limites explícitos de análise e autorizações existentes. Antes de
  implementar, resolva o [método de execução](agents.md#metodo-de-execucao) se ainda
  não definido; perfil de risco e método são escolhas distintas.
- No núcleo geral, selecione pela entrega pedida. Brainstorming explora problema
  e alternativas; Plan organiza uma direção definida. Pedido composto percorre
  somente as etapas necessárias e já autorizadas, sem pedir aprovação novamente. Com plano aprovado e fontes atuais, retome a próxima pendência; não refaça brainstorming/plano sem nova evidência ou mudança material.
- Se nome e pedido divergirem materialmente (por exemplo, build com “somente
  planeje”), respeite o limite do pedido e explique o modo efetivo. Pergunte apenas
  quando a ambiguidade impedir uma decisão de escopo segura.
- FAST/BALANCED/DEEP definem profundidade. Explore/Plan/Build/Review definem
  atividade. Direto ou rastreado é escolha documental independente do perfil: direto usa chat/diff/evidência sem TASK/SPEC/PLAN ou estado obrigatórios. Adoção da CLI preserva seus gates. Os nomes das entradas não criam estados nem novos perfis.
- Execute no agente atual por padrão. Delegue apenas com ganho concreto e
  capacidade/autorização do host, conforme [Agents](agents.md). Paralelismo exige
  tarefas independentes e recursos isolados; não aumente concorrência por comando.
- Para tarefas, status ou retomada, use a fonte de estado existente conforme
  [Workflows](workflow.md). Não inicialize outro store nem acione helpers, hooks ou
  memória automaticamente. Crie persistência somente quando útil ou solicitada. Resultado externo incerto exige reconciliação antes
  de retry; status `running` sozinho não prova que o processo terminou.

O host escolhe o workflow condutor (NEXUS, Superpowers ou outro), conforme precedência e pedido; NEXUS não desativa skills nem exige duplicar etapas já satisfeitas.

## Entrega comum

Informe resultado, evidências e limitações, arquivos alterados (ou nenhum),
verificações realmente executadas e próxima ação quando pendente. Uma análise pode
terminar com hipótese ou decisão aberta; não apresente inferência como execução.
Use templates apenas quando o artefato for necessário. Resposta no chat é válida
e não implica persistência; ausência de persistência deve ficar explícita quando
o pedido depender de estado salvo.
