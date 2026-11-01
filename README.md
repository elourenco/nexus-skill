# NEXUS — Engineering Intelligence

Fundação de uma skill portátil de engenharia: especificação, decisões arquiteturais, execução incremental e validação com evidências.

**Status: skill portátil com componentes locais opcionais.** `skills/nexus/` contém instruções, templates, um [helper de memória JSON](skills/nexus/references/memory.md) e a [CLI de workflows](skills/nexus/references/workflow-state.md) para tarefas, DAG, gates e recuperação. A [CLI de agentes e review](runtime/README.md) fornece roteamento, adapters textuais e Council. Esses componentes são acionados explicitamente; não há scheduler, dashboard ou ligação automática entre eles. Implementação, testes do projeto e dispatch do workflow continuam nas ferramentas reais do host.

## Começar

O ponto de entrada é [skills/nexus/SKILL.md](skills/nexus/SKILL.md). Carregue esse arquivo no agente e forneça o objetivo e o repositório de trabalho. Para runtimes com instalação de skills, copie a pasta `skills/nexus` para o diretório de skills suportado pelo host. A instalação e a descoberta precisam ser verificadas em cada host; este repositório não modifica configurações globais.

Exemplo de solicitação: “Use NEXUS para planejar a sincronização offline deste projeto; preserve os contratos existentes e registre os cenários de conflito e recuperação.”

## Estrutura

| Caminho | Responsabilidade |
| --- | --- |
| [Skill](skills/nexus/SKILL.md) | Entrada curta e seleção de referências |
| [Workflow](skills/nexus/references/workflow.md) | FAST/BALANCED/DEEP, Explore/Plan/Build/Review e Autonomous |
| [Todo executável](skills/nexus/references/workflow-state.md) | Store local, orquestração, CLI/Markdown e limites do runtime |
| [Políticas](skills/nexus/references/policies.md) | Testes adaptativos, contexto e modelos |
| [Agentes](skills/nexus/references/agents.md) | Ownership e revisão por pilar |
| [Hooks](skills/nexus/references/hooks.md) | Contratos lógicos e limites de execução |
| [Memória](skills/nexus/references/memory.md) | Persistência local opt-in, proveniência, recuperação e isolamento |
| [Helper de memória](skills/nexus/scripts/memory.py) | CLI Python sem dependências; filesystem local POSIX |
| [Princípios cognitivos](skills/nexus/references/cognitive.md) | Premissas, alternativas e evidências |
| [Templates](skills/nexus/assets/templates/spec.md) | Spec, plano, tarefa, ADR e memória |
| [Escopo](docs/phase-1.md) | Entrega atual e próximos refinamentos |

## Validar

Requer Python 3.10 ou superior, sem dependências externas:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

O validador cobre metadados e links Markdown locais. A suíte em `tests/` exercita memória e workflows, incluindo persistência, concorrência e recuperação. Veja as [evidências de memória](docs/memory-validation.md), a [auditoria de workflows](docs/workflow-implementation.md) e suas [evidências](docs/workflow-validation.md). Não demonstra aderência geral de agentes ou instalação entre hosts.

Para o runtime textual opcional, execute `python3 -m unittest discover -s runtime/tests -v`. Os testes usam dados sintéticos e HTTP em loopback; não exigem credenciais nem comprovam acesso autenticado a providers. Veja [escopo e limites](runtime/README.md) e o [desenho do incremento](docs/agents-review-runtime-design.md).

As [evidências da base](docs/validation.md) e os documentos da fase 1 registram o estágio documental anterior; os incrementos executáveis têm escopo nas referências acima.

## Origem e limites

O desenho parte de práticas de desenvolvimento orientado por especificação, execução persistente com limites e arquitetura proporcional ao risco. Superpowers e UB-Mode são referências conceituais citadas no planejamento, não dependências incorporadas nem integrações verificadas. O conteúdo deste repositório é próprio; nenhuma implementação de terceiros foi copiada.

A licença de distribuição ainda será definida. Não publicar releases nem assumir permissão de redistribuição enquanto essa decisão estiver aberta.
