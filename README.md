# NEXUS — Engineering Intelligence

Fundação de uma skill portátil de engenharia: especificação, decisões arquiteturais, execução incremental e validação com evidências.

**Status: fase 1, base inicial para refinamento.** O pacote contém instruções e templates. Não contém scheduler, adapters de providers, execução automática de hooks, banco de memória ou dashboard.

## Começar

O ponto de entrada é [skills/nexus/SKILL.md](skills/nexus/SKILL.md). Carregue esse arquivo no agente e forneça o objetivo e o repositório de trabalho. Para runtimes com instalação de skills, copie a pasta `skills/nexus` para o diretório de skills suportado pelo host. A instalação e a descoberta precisam ser verificadas em cada host; este repositório não modifica configurações globais.

Exemplo de solicitação: “Use NEXUS para planejar a sincronização offline deste projeto; preserve os contratos existentes e registre os cenários de conflito e recuperação.”

## Estrutura

| Caminho | Responsabilidade |
| --- | --- |
| [Skill](skills/nexus/SKILL.md) | Entrada curta e seleção de referências |
| [Workflow](skills/nexus/references/workflow.md) | Explore, Plan, Build, Review e Autonomous |
| [Políticas](skills/nexus/references/policies.md) | Testes adaptativos, contexto e modelos |
| [Agentes](skills/nexus/references/agents.md) | Ownership e revisão por pilar |
| [Hooks](skills/nexus/references/hooks.md) | Contratos lógicos e limites de execução |
| [Memória](skills/nexus/references/memory.md) | Proveniência, validade e isolamento |
| [Princípios cognitivos](skills/nexus/references/cognitive.md) | Premissas, alternativas e evidências |
| [Templates](skills/nexus/assets/templates/spec.md) | Spec, plano, tarefa, ADR e memória |
| [Escopo](docs/phase-1.md) | Entrega atual e próximos refinamentos |

## Validar

Requer Python 3.10 ou superior, sem dependências externas:

```sh
python3 scripts/validate.py
```

A verificação cobre metadados essenciais e destinos de links Markdown locais. Não demonstra aderência comportamental dos agentes nem compatibilidade de instalação entre hosts.

Veja as [evidências da base](docs/validation.md).

## Origem e limites

O desenho parte de práticas de desenvolvimento orientado por especificação, execução persistente com limites e arquitetura proporcional ao risco. Superpowers e UB-Mode são referências conceituais citadas no planejamento, não dependências incorporadas nem integrações verificadas. O conteúdo deste repositório é próprio; nenhuma implementação de terceiros foi copiada.

A licença de distribuição ainda será definida. Não publicar releases nem assumir permissão de redistribuição enquanto essa decisão estiver aberta.
