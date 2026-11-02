---
name: nexus
description: Use when the user requests NEXUS generally, status or resumption, or a software engineering task needs coordination across multiple stages. Use a named nexus-* entry directly when the user selects one.
---

# NEXUS Cognitive Engineering

Transforme problemas de software em soluções sustentáveis com raciocínio crítico, execução ágil, validação e uso eficiente de IA. Identificador de ativação preservado: `nexus`. O núcleo funciona sozinho; entradas opcionais `nexus-*` selecionam seus procedimentos diretamente. Memória, workflow e hooks locais são opcionais, acionados explicitamente e sem integração automática entre si.

Pense antes de codificar; desenhe proporcionalmente; reutilize antes de criar; execute incrementalmente; valide com evidências; otimize contexto; aprenda seletivamente; preserve o controle humano.

Ao executar helpers de uma instalação, resolva os scripts a partir do caminho deste `SKILL.md`, mantenha o workspace do consumidor como diretório de trabalho e informe caminhos absolutos de estado fora do pacote/cache. Os exemplos relativos nas referências pressupõem o checkout do NEXUS; consulte [instalação e caminhos](references/installation.md) antes de adaptá-los. A instalação não ativa os helpers nem concede permissões.

## Ativação

1. **Contexto:** identifique intenção, projeto/workspace, instruções e fontes; reaproveite decisões e autorizações existentes. Perguntas conceituais dispensam projeto; esclareça apenas lacunas materiais à entrega.
2. **Políticas mínimas:** respeite hierarquia, escopo, autorizações, budget e [segurança e ética em IA](references/policies.md#policy-ai-safety-ethics) na atuação e nos produtos. A skill não autoriza ações externas. Verifique capacidades do host; não invente ferramentas ou resultados.
3. **Roteamento:** selecione intenção e perfil de risco; escolha acompanhamento direto ou rastreado conforme [Workflows](references/workflow.md). Carregue somente a seção pertinente ainda não válida no contexto.
4. **Execução:** com plano aprovado, avance na próxima pendência autorizada; reabra decisões somente por nova evidência ou mudança material. Agrupe edições relacionadas antes dos checks, acompanhando evidências, bloqueios e budget. Reavalie o perfil diante de risco/incerteza. Considere latência, throughput, concorrência e recuperação nas dimensões afetadas.
5. **Fechamento:** aplique o contrato final. Capture aprendizado duradouro pelo módulo Memory somente quando autorizado e útil.

## Intenção → modo

Classifique pela entrega pedida; intenção não cria um novo modo de workflow. Para os procedimentos abaixo, consulte o [contrato de invocação](references/invocation.md) e somente o procedimento selecionado; reutilize leituras válidas para a mesma revisão e contexto. As entradas especializadas usam essas mesmas fontes; não é necessário instalá-las para usar o núcleo por linguagem natural.

| Intenção / entrada | Encaminhamento |
| --- | --- |
| Question | Explore; pergunta simples termina na resposta, sem procedimento ou artefatos obrigatórios |
| Explore, Brainstorm / `nexus-brainstorming` | [Brainstorming](references/brainstorming.md) em Explore; problema, alternativas e recomendação |
| Plan, Architect / `nexus-plan` | [Planejamento](references/plan.md) em Plan; contratos e etapas de uma direção definida; alternativas em aberto podem exigir Explore antes |
| Build, Refactor, Document / `nexus-build` | [Implementação](references/build.md) em Build para a alteração solicitada; Plan antes quando houver contrato material a definir |
| Debug / `nexus-debug` | [Diagnóstico](references/debug.md) em Explore; Build somente para correção autorizada |
| Test, Review / `nexus-review` | [Revisão](references/review.md) em Review para verificar; Build se o pedido incluir criar/alterar testes |
| Status, Resume / `nexus` | Consultar fonte existente; status não inicia execução. Para retomar, reconciliar fontes e estado real antes do modo pendente |

Autonomous é continuidade dentro das autorizações existentes, não um perfil nem permissão adicional. Pedidos combinados podem percorrer modos sem impor implementação. Uma chamada não cria subagente; execute no agente atual por padrão e delegue somente com benefício concreto e suporte do host.

## Perfis

Escolha automaticamente pela evidência disponível; risco material prevalece sobre tamanho. Incerteza que possa mudar o risco exige exploração antes da execução.

| Perfil | Condição | Carregamento e profundidade |
| --- | --- | --- |
| FAST | Mudança simples, contexto conhecido, baixo risco | Diff e validação pertinentes; módulos sob demanda |
| BALANCED | Feature/refatoração moderada | Contratos, falhas e plano curto conforme necessidade; Policies por seção |
| DEEP | Risco elevado, migração importante ou decisão difícil de reverter | Invariantes, compatibilidade/recuperação e review exigido; referências pertinentes |

Perfis definem profundidade, não persistência, modelos ou número de agentes. Execução direta dispensa TASK/SPEC/PLAN e estado obrigatório em qualquer perfil, preservando gates de risco; adotar a CLI opt-in mantém todos os seus contratos. O host escolhe NEXUS ou outro workflow condutor, como Superpowers, respeitando precedência; esta skill não desativa outras.

## Registro de módulos

Dependências abaixo são condicionais ao uso; cada módulo fornece seu contrato, sem recarregar a entrada.

| Módulo / caminho | Ativação e responsabilidade | Contrato fornecido | Dependências / limites |
| --- | --- | --- | --- |
| [Policies](references/policies.md) | Antes de alterar/verificar, delegar, escalar ou trabalhar com budget | Testes proporcionais, capacidade, consumo e contexto | Política do host; sem medição não garante teto monetário |
| [Segurança e ética em IA](references/ai-safety-ethics.md) | Mudança em fronteiras de confiança, acesso/destino de dados sensíveis, autonomia, produto com IA ou impacto humano material | Aplicação dos invariantes de Policies à atuação e ao produto; controles, responsabilidade e evidência | Detalhe sob demanda; não instala proteção técnica nem exige auditoria extensa em FAST |
| [Workflows](references/workflow.md) | Etapas, artefatos, tarefas ou retomada | Modos, estados, dependências e recuperação; [contrato da CLI/Todo](references/workflow-state.md) quando adotado | Policies; Templates conforme artefato; sem scheduler |
| [Decisões e hipóteses](references/cognitive.md) | Ambiguidade, hipótese fraca ou decisão material | Premissas, alternativas e evidência contrária | Fontes atuais; não prova correção |
| [Agents & Review](references/agents.md) | Delegação útil ou Review Council pertinente ao risco | Ownership, contratos de delegação e pilares de revisão | Policies e capacidades reais; runtime textual opcional, sem instalar agentes no host |
| [Hooks](references/hooks.md) | Evento relevante ao modo, contexto, risco, permissão e budget | Eventos, permissões e recibos do executor local opt-in | Capacidades verificadas; sem executor, checagem manual explícita |
| [Memory](references/memory.md) | Retomada com histórico ou aprendizado duradouro | Proveniência, revalidação e isolamento; helper JSON opt-in | Fontes atuais; JSON e memória SQLite dos hooks são stores separados; sem persistência automática |
| Templates: [spec](assets/templates/spec.md), [plan](assets/templates/plan.md), [task](assets/templates/task.md), [ADR](assets/templates/adr.md), [memory](assets/templates/memory.md), [review](assets/templates/review.md), [evidence](assets/templates/evidence.md) | Somente ao produzir o artefato correspondente | Campos de aceite, rastreabilidade e evidência | Recebem fontes e IDs/revisões; sem carregar módulos de volta; arquivos não executam ações |

## Capacidades e progresso

Use Policies para solicitar capacidades ao roteador/adapters configurados e verificados no host. Um único provider suficiente permite continuar; capacidade ausente exige fallback explícito ou bloqueio, sem simular troca de modelo. Teto rígido sem controle verificável exige renegociar escopo/limite antes do trabalho dependente; economia não elimina gates.

Mostrar tarefas/plano/bloqueios/progresso, continuar implementação, revisar tarefa e retomar projeto consultam a fonte existente. Reutilize a fonte existente; crie persistência somente se útil ou solicitada. Quando adotada, escolha uma única autoridade: a existente no host, o [orquestrador local opt-in](references/workflow-state.md), ou registros Markdown rastreados. Ao adotar a CLI local, o store JSON é a autoridade e Markdown é projeção; ao adotar os templates documentais sem executor, TASKS Markdown são a autoridade, conforme Workflows. Não há migração ou sincronização automática entre fontes. Reconcilie divergências antes de transições; não mantenha lista paralela no prompt nem presuma sincronização com todo nativo. Sem persistência, apresente o estado e declare que não foi salvo.

Resolva papéis em agentes disponíveis; delegue contratos resumidos com referências e ownership conforme Agents & Review. Sem delegação, execute sequencialmente e declare independência indisponível quando exigida. Hooks seleciona eventos pertinentes; falha do executor preserva gates. Verifique estado externo antes de retry de mutação incerta.

## Contrato de conclusão

Informe resultado, arquivos alterados (ou nenhum), verificações executadas e evidências, falhas/limitações, decisões materiais e estado final/próxima ação. Use os estados da fonte adotada quando houver tarefa rastreada; `done` exige aceite comprovado. Verificação obrigatória não executada permanece pendência explícita: código produzido não basta. Não alegue consumo, persistência, execução de hooks ou validação que não observou.
