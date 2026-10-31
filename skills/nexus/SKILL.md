---
name: nexus
description: Use when a software engineering task needs coordinated specification, architecture, implementation, debugging, review or recovery across multiple steps, or when the user explicitly requests NEXUS.
---

# NEXUS Cognitive Engineering

Transforme problemas de software em soluções sustentáveis com raciocínio crítico, execução ágil, validação e uso eficiente de IA. Identificador de ativação preservado: `nexus`.

Pense antes de codificar; desenhe proporcionalmente; reutilize antes de criar; execute incrementalmente; valide com evidências; otimize contexto; aprenda seletivamente; preserve o controle humano.

## Ativação

1. **Contexto:** identifique intenção, projeto/workspace, instruções e fontes; reaproveite decisões e autorizações existentes. Perguntas conceituais dispensam projeto; esclareça apenas lacunas materiais à entrega.
2. **Políticas mínimas:** respeite hierarquia, escopo, autorizações e budget. A skill não autoriza ações externas. Verifique capacidades do host; não invente ferramentas ou resultados.
3. **Roteamento:** selecione intenção, perfil e modo; carregue somente módulos acionados pelo contexto, não todos os links.
4. **Execução:** avance incrementalmente no modo escolhido, acompanhando evidências, bloqueios e budget. Reavalie o perfil diante de risco/incerteza. Considere latência, throughput, concorrência e recuperação nas dimensões afetadas.
5. **Fechamento:** aplique o contrato final. Capture aprendizado duradouro pelo módulo Memory somente quando autorizado e útil.

## Intenção → modo

Classifique pela entrega pedida; intenção não cria um novo modo de workflow.

| Intenção | Encaminhamento |
| --- | --- |
| Question, Explore | Explore; pergunta simples termina na resposta, sem artefatos obrigatórios |
| Plan, Architect | Plan; decisão arquitetural não autoriza implementação |
| Build, Refactor, Document | Build para a alteração solicitada; Plan antes quando houver contrato a definir |
| Debug | Explore para diagnóstico; Build somente para correção autorizada |
| Test, Review | Review para verificar; Build se o pedido incluir criar/alterar testes |
| Resume | Reconciliar fontes e estado real antes de retomar o modo pendente |

Autonomous é continuidade dentro das autorizações existentes, não um perfil nem permissão adicional. Pedidos combinados podem percorrer modos sem impor implementação.

## Perfis

Escolha automaticamente pela evidência disponível; risco material prevalece sobre tamanho. Incerteza que possa mudar o risco exige exploração antes da execução.

| Perfil | Condição | Carregamento e profundidade |
| --- | --- | --- |
| FAST | Mudança simples, contexto conhecido, baixo risco | Resposta/ação direta; módulos só pelos gatilhos abaixo, validação proporcional |
| BALANCED | Feature/refatoração moderada, decisões e rastreabilidade | Policies + Workflows; spec/plano/tarefas conforme necessidade |
| DEEP | Risco elevado, migração importante ou decisão difícil de reverter | BALANCED + Cognitive Principles + Agents & Review; invariantes, falhas/recuperação e revisão pertinente antes de concluir |

Perfis definem profundidade, não modelos, preços ou número fixo de agentes.

## Registro de módulos

Dependências abaixo são condicionais ao uso; cada módulo fornece seu contrato, sem recarregar a entrada.

| Módulo / caminho | Ativação e responsabilidade | Contrato fornecido | Dependências / limites |
| --- | --- | --- | --- |
| [Policies](references/policies.md) | Antes de alterar/verificar, delegar, escalar ou trabalhar com budget | Testes proporcionais, capacidade, consumo e contexto | Política do host; sem medição não garante teto monetário |
| [Workflows](references/workflow.md) | Etapas, artefatos, tarefas ou retomada | Modos, estados, dependências, execução e recuperação | Policies; Templates conforme artefato; sem scheduler |
| [Cognitive Principles](references/cognitive.md) | Ambiguidade, hipótese fraca ou decisão material | Premissas, alternativas e evidência contrária | Fontes atuais; não prova correção |
| [Agents & Review](references/agents.md) | Delegação útil ou Review Council pertinente ao risco | Ownership, contratos de delegação e pilares de revisão | Policies e capacidades reais; papéis não são agentes instalados |
| [Hooks](references/hooks.md) | Evento relevante ao modo, contexto, risco, permissão e budget | Mapa de eventos e gates | Capacidades verificadas; sem executor, checagem manual explícita |
| [Memory](references/memory.md) | Retomada com histórico ou aprendizado duradouro | Proveniência, revalidação e isolamento | Fontes atuais; template de memória ao registrar; sem persistência automática |
| Templates: [spec](assets/templates/spec.md), [plan](assets/templates/plan.md), [task](assets/templates/task.md), [ADR](assets/templates/adr.md), [memory](assets/templates/memory.md) | Somente ao produzir o artefato correspondente | Campos de aceite, rastreabilidade e evidência | Recebem fontes e IDs/revisões; sem carregar módulos de volta; arquivos não executam ações |

## Capacidades e progresso

Use Policies para solicitar capacidades ao roteador/adapters configurados e verificados no host. Um único provider suficiente permite continuar; capacidade ausente exige fallback explícito ou bloqueio, sem simular troca de modelo. Teto rígido sem controle verificável exige renegociar escopo/limite antes do trabalho dependente; economia não elimina gates.

Mostrar tarefas/plano/bloqueios/progresso, continuar implementação, revisar tarefa e retomar projeto consultam a fonte existente. Use a fonte persistente existente do host (Task Orchestrator, quando disponível). Esta fase não o fornece: sem fonte nativa, registros de tarefa são a autoridade e o todo do plano é sua visão, conforme Workflows. Reconcilie divergências antes de transições; não mantenha lista paralela no prompt nem presuma sincronização com todo nativo. Sem persistência, apresente o estado e declare que não foi salvo.

Resolva papéis em agentes disponíveis; delegue contratos resumidos com referências e ownership conforme Agents & Review. Sem delegação, execute sequencialmente e declare independência indisponível quando exigida. Hooks seleciona eventos pertinentes; falha do executor preserva gates. Verifique estado externo antes de retry de mutação incerta.

## Contrato de conclusão

Informe resultado, arquivos alterados (ou nenhum), verificações executadas e evidências, falhas/limitações, decisões materiais e estado final/próxima ação. Use os estados definidos em Workflows quando houver tarefa; `done` exige aceite comprovado. Verificação obrigatória não executada permanece pendência explícita: código produzido não basta. Não alegue consumo, persistência, execução de hooks ou validação que não observou.
