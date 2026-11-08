# Proveniência do conteúdo de design e refatoração

Registro de manutenção consultado em 2026-11-03. A execução usa as referências
locais do NEXUS; estes links não são dependências de instalação, leitura ou rede.
O conteúdo é uma síntese contextual em português, sem copiar scripts, exemplos,
templates ou workflows completos das fontes. Revisões upstream exigem avaliação
explícita; não há sincronização automática.

| Fonte | Conteúdo incorporado | Destino e adaptação |
| --- | --- | --- |
| `software-design-principles`, versão local 2.0.0 fornecida pelo usuário | Coesão, invariantes, tipos, efeitos, dependências explícitas, falhas e performance | [Modelagem](domain-design.md) e [princípios](policies.md#policy-engineering); contexto da linguagem/projeto prevalece sobre máximas de estilo. |
| [codebase-design — Matt Pocock](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) | Complexidade encapsulada, interfaces pequenas, localização de mudanças, teste de remoção e teste pelo contrato | [Design de módulos](architecture-design.md#modulos); sem vocabulário exclusivo nem número mínimo de adapters para justificar uma fronteira. |
| [senior-architect — Alireza Rezvani](https://github.com/alirezarezvani/claude-skills/blob/main/engineering-team/skills/senior-architect/SKILL.md) | Drivers, alternativas, trade-offs, decisões de banco/deploy e ADR | [Sistemas e soluções](architecture-design.md#sistemas); sem limiares universais de equipe, registros ou QPS, scores não demonstrados ou scripts externos. |
| [architecture-patterns — wshobson/agents](https://github.com/wshobson/agents/blob/main/plugins/backend-development/skills/architecture-patterns/SKILL.md) | Clean Architecture, Hexagonal, DDD estratégico/tático e fronteiras de dependência | [Padrões condicionais](architecture-design.md#padroes); sem interface/camada obrigatória ou equivalência presumida entre fake e storage real. |
| [improve-codebase-architecture — Matt Pocock](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md) | Investigar atrito real, partes frequentemente alteradas e oportunidades de consolidar comportamento | [Diagnóstico](architecture-design.md#diagnostico) e [refatoração](refactoring.md); sem relatório HTML, skills adicionais ou agentes obrigatórios. |
| [Refactoring — Martin Fowler](https://refactoring.com/) e [catálogo](https://refactoring.com/catalog/) | Transformações incrementais que preservam comportamento; extração, inline, movimentação, simplificação e delegação | [Padrões de refatoração](refactoring.md#padroes); seleção pelo problema e verificação dos contratos afetados. |

## Identidade das fontes consultadas

Os identificadores abaixo são hashes dos blobs Git de `SKILL.md`, não commits ou
tags de release. Os URLs acima acompanham a branch principal e podem mudar.

| Fonte | Blob Git |
| --- | --- |
| codebase-design | `3f63c8146dd2604b419c929e9876b90c30d410e9` |
| senior-architect | `5fabc117b9f80070a9f2c8b332647551a7fca8d9` |
| architecture-patterns | `d893cabeab6a84c17bd0dd4ea9f56b3c4d02c0f5` |
| improve-codebase-architecture | `f1eabb568464f03ae79a3346fc1918fdde6d8285` |

A versão local de software-design-principles 2.0.0 tem SHA-256
`49e34bf9f0f37c71869aad44f23d6e1747484d8918849adef494163d6ba5af5e`.
É distinta da [versão pública NTCoding](https://github.com/NTCoding/claude-skillz/blob/main/software-design-principles/SKILL.md):
esta integração usa a adaptação local; não importa proibição de comentários,
exigência de Zod ou rejeição universal de defaults válidos.

## Critério de manutenção

Uma atualização deve preservar autoridade, escopo, contratos existentes e o
carregamento seletivo. Reavaliar os cenários afetados antes de declarar melhoria.
Popularidade, nomes de padrões e conformidade estrutural não comprovam qualidade,
correção concorrente ou desempenho em produção.
