# NEXUS — Engineering Intelligence

Fundação de uma skill portátil de engenharia: especificação, decisões arquiteturais, execução incremental e validação com evidências.

[Segurança e ética em IA](skills/nexus/references/ai-safety-ethics.md) orientam tanto
a atuação da NEXUS quanto os produtos com IA que ela ajuda a construir: autorização,
privacidade, confiabilidade, impacto humano e supervisão proporcional ao risco.
As regras vivem em [Policies](skills/nexus/references/policies.md#policy-ai-safety-ethics)
e chegam às seis entradas pelos contratos compartilhados, com detalhes sob demanda.
São instruções e critérios de avaliação; não instalam barreiras técnicas, certificam
conformidade ou comprovam resistência a prompt injection.

**Status: skill portátil com componentes locais opcionais.** `skills/nexus/` contém instruções, templates, um [helper de memória JSON](skills/nexus/references/memory.md), o [executor local de hooks](skills/nexus/references/hooks.md) com journal SQLite e a [CLI de workflows](skills/nexus/references/workflow-state.md) para tarefas, DAG, gates e recuperação. A [CLI de agentes e review](runtime/README.md) fornece roteamento, adapters textuais e Council. Esses componentes são acionados explicitamente; não há scheduler, dashboard ou ligação automática entre eles. Implementação, testes do projeto e dispatch do workflow continuam nas ferramentas reais do host.

## Começar

O ponto de entrada geral é [skills/nexus/SKILL.md](skills/nexus/SKILL.md). Carregue esse arquivo no agente e forneça o objetivo e o repositório de trabalho. O núcleo funciona sozinho e seleciona procedimentos conforme o pedido. Para chamadas individuais no seletor do host, o pacote também oferece cinco entradas especializadas.

Também há empacotamento local como plugin **`nexus@nexus-local`**, versão **0.3.0**, para Claude Code e Codex. Ambos usam o mesmo diretório `skills/`, agora com seis entradas; a instalação não ativa hooks, servidores MCP ou o runtime textual. Veja [instalação e uso](skills/nexus/references/installation.md) e [avaliação e descoberta nos hosts](docs/behavioral-evaluation.md). O [histórico de empacotamento](docs/plugins-validation.md) registra a versão inicial 0.1.0. A licença continua pendente; este incremento não publica uma distribuição.

Na raiz deste repositório, escolha o host. Estes comandos alteram a configuração do usuário **quando você os executar**:

```sh
claude plugin marketplace add "$PWD"
claude plugin install nexus@nexus-local
```

```sh
codex plugin marketplace add "$PWD"
codex plugin add nexus@nexus-local
```

Exemplo de solicitação: “Use NEXUS para planejar a sincronização offline deste projeto; preserve os contratos existentes e registre os cenários de conflito e recuperação.”

## Entradas disponíveis

| Entrada | Quando usar | Entrega |
| --- | --- | --- |
| [nexus](skills/nexus/SKILL.md) | Coordenação geral, status ou retomada | Roteamento ou estado reconciliado |
| [nexus-brainstorming](skills/nexus-brainstorming/SKILL.md) | Explorar problema e alternativas | Recomendação, trade-offs e questões abertas |
| [nexus-plan](skills/nexus-plan/SKILL.md) | Detalhar uma direção definida | Contratos, etapas, dependências e validação |
| [nexus-build](skills/nexus-build/SKILL.md) | Implementar o escopo autorizado | Alterações verificadas e pendências |
| [nexus-debug](skills/nexus-debug/SKILL.md) | Investigar bug ou comportamento inesperado | Diagnóstico; correção quando solicitada |
| [nexus-review](skills/nexus-review/SKILL.md) | Avaliar diff, contrato ou solução existente | Achados com evidências e decisão de review |

“Brainstorming do NEXUS sobre sincronização offline” e “Use NEXUS para fazer
brainstorming sobre sincronização offline” selecionam o mesmo procedimento.
Brainstorming e planejamento não autorizam implementação; “revise e corrija” pode
percorrer Review e Build dentro do escopo já autorizado. FAST/BALANCED/DEEP continuam
sendo perfis de profundidade, sem criar variações de comandos. Status e retomada
continuam em `nexus`, sem entradas adicionais.

Os procedimentos e políticas vivem em `skills/nexus/`. As cinco entradas são
seletores curtos com referências relativas ao núcleo; não duplicam workflow,
estado ou regras. A [invocação](skills/nexus/references/invocation.md) carrega apenas
o procedimento escolhido e executa no agente atual por padrão.

## Instalação e invocação por host

Como plugin, os manifestos incluem o diretório `skills/` completo. Na instalação
manual de skills standalone, copie **as seis pastas** de `skills/` para o mesmo diretório
de skills suportado pelo host, preservando nomes e conteúdo. `nexus/` deve ficar
ao lado de `nexus-brainstorming/`, `nexus-plan/`, `nexus-build/`, `nexus-debug/` e
`nexus-review/`. Atualize o conjunto a partir da mesma revisão para preservar os
contratos. Antes de substituir uma instalação, confira alterações locais.

Para instalação mínima, copie somente `skills/nexus/`; os pedidos em linguagem
natural continuam disponíveis. Uma entrada especializada isolada é incompleta:
se faltar o núcleo ou a referência exigida, o agente informa a dependência e
interrompe esse fluxo. Não há instalador nem atualização global automática.

| Host / instalação | Exemplo após instalação e descoberta |
| --- | --- |
| Codex CLI / IDE — standalone | `$nexus-brainstorming Compare as alternativas de sincronização offline.` |
| Claude Code — standalone | `/nexus-brainstorming Compare as alternativas de sincronização offline.` |
| Codex — plugin `nexus` | `$nexus:nexus-brainstorming Compare as alternativas de sincronização offline.` |
| Claude Code — plugin `nexus` | `/nexus:nexus-brainstorming Compare as alternativas de sincronização offline.` |
| Outros hosts / carregamento manual | Carregue a entrada e peça “Use nexus-brainstorming para comparar as alternativas”. Verifique o mecanismo de seleção do host. |

No Codex, skills de repositório podem ficar em `.agents/skills/`; no Claude Code,
em `.claude/skills/`. Essas sintaxes são interfaces dos hosts, não subcomandos de
uma CLI NEXUS. Confira a documentação de [skills no Codex](https://learn.chatgpt.com/docs/build-skills)
e [skills no Claude Code](https://code.claude.com/docs/en/skills).

Após copiar, verifique que o host lista as seis entradas e invoque uma com um
pedido apenas de análise. Confira a leitura do procedimento e o escopo respeitado.
A presença dos arquivos não prova descoberta automática ou acesso aos links entre
pastas em qualquer host. Este repositório não modifica configurações globais.

## Estrutura

| Caminho | Responsabilidade |
| --- | --- |
| [Skill](skills/nexus/SKILL.md) | Entrada curta e seleção de referências |
| [Workflow](skills/nexus/references/workflow.md) | FAST/BALANCED/DEEP, Explore/Plan/Build/Review e Autonomous |
| [Todo executável](skills/nexus/references/workflow-state.md) | Store local, orquestração, CLI/Markdown e limites do runtime |
| [Políticas](skills/nexus/references/policies.md) | Testes adaptativos, contexto e modelos |
| [Segurança e ética em IA](skills/nexus/references/ai-safety-ethics.md) | Conduta do agente, impacto humano nos produtos, controles e evidências proporcionais |
| [Agentes](skills/nexus/references/agents.md) | Ownership e revisão por pilar |
| [Hooks](skills/nexus/references/hooks.md) | Executor local opt-in, permissões, recibos e recuperação |
| [Memória](skills/nexus/references/memory.md) | Persistência local opt-in, proveniência, recuperação e isolamento |
| [Helper de memória](skills/nexus/scripts/memory.py) | CLI Python sem dependências; filesystem local POSIX |
| [Decisões e hipóteses](skills/nexus/references/cognitive.md) | Premissas, alternativas e evidências |
| [Modelagem](skills/nexus/references/domain-design.md) | Estados, fronteiras e ownership proporcionais à mudança |
| [Pacote de review](skills/nexus/references/review-package.md) | Coleta Git com hashes, anexos e limites explícitos |
| [Templates](skills/nexus/assets/templates/spec.md) | Spec, plano, tarefa, ADR e memória |
| [Escopo](docs/phase-1.md) | Entrega atual e próximos refinamentos |

## Validar

Para adotar os componentes locais, siga o [consumidor mínimo](skills/nexus/references/consumer-guide.md).
O [registro de segurança e ética](docs/ai-safety-ethics-validation.md) distingue
verificações estruturais, aplicação documental dos cenários e limites da entrega.
O exemplo executável demonstra falha, bloqueio, correção e recuperação com recibos
reais. Os [checks de qualidade](skills/nexus/references/quality-checks.md) reutilizam
o executor de hooks com flags, escopo e thresholds definidos pelo consumidor.

A [suíte comportamental](docs/behavioral-evaluation.md) separa descoberta nos hosts,
aplicação por agentes e testes dos helpers. `scripts/evaluate.py` prepara condições
baseline/NEXUS com contextos independentes, registra observações reais e mantém
amostras ausentes como inconclusivas; não inicia inferência nem inventa métricas.

O workflow aceita agora uma política opcional de [recibos dos hooks](skills/nexus/references/workflow-state.md):
importação explícita, vínculo a tarefa/run/snapshot e revalidação na conclusão.
Consumidores antigos continuam usando o contrato declarado. Identidades de review
são proveniência informada pelo host, não autenticação de independência.

Requer Python 3.10 ou superior, sem dependências externas:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -p test_validate.py -v
python3 skills/nexus/scripts/hook_engine.py validate
python3 -m unittest discover -s tests -v
```

O validador cobre metadados das seis entradas, links Markdown locais e contratos dos manifestos/catálogos. Os testes de pacote verificam dependências ausentes e portabilidade do núcleo isolado e do conjunto. As [evidências das entradas](docs/entrypoints-validation.md) registram avaliações comportamentais com cenários sintéticos e seus limites. A suíte em `tests/` exercita memória, workflows, hooks e relocação dos helpers, incluindo persistência, concorrência e recuperação. Veja as [evidências de memória](docs/memory-validation.md), a [auditoria de workflows](docs/workflow-implementation.md), suas [evidências](docs/workflow-validation.md) e a [validação de plugins](docs/plugins-validation.md). Os testes Python não demonstram aderência geral de agentes nem substituem a instalação nos hosts.

Para o runtime textual opcional, execute `python3 -m unittest discover -s runtime/tests -v`. Os testes usam dados sintéticos e HTTP em loopback; não exigem credenciais nem comprovam acesso autenticado a providers. Veja [escopo e limites](runtime/README.md) e o [desenho do incremento](docs/agents-review-runtime-design.md).

As [evidências da base](docs/validation.md) e os documentos da fase 1 registram o estágio documental anterior; os incrementos executáveis têm escopo nas referências acima.

Consulte os [limites do executor de hooks](skills/nexus/references/hooks.md) e suas [evidências](docs/hooks-validation.md) antes de conceder permissões. O registro padrão valida este repositório; consumidores configuram ferramentas e arquivos que compõem os recibos. A memória SQLite dos hooks é isolada da memória JSON do projeto; não existe sincronização automática.

As [evidências do incremento 0.3.0](docs/quality-improvements-validation.md) mapeiam
as entregas aos testes, ao review independente e aos limites das avaliações.

O fluxo distingue **perfil de risco** de **acompanhamento direto ou rastreado**:
uma entrega local pode usar chat, diff e verificações sem criar TASK/SPEC/PLAN;
retomadas reutilizam o estado e o plano aprovados. A CLI opt-in mantém seus gates.
A [suíte de eficiência](evals/efficiency-suite.json) e o
[comparador de versões](docs/behavioral-evaluation.md)
avaliam artefatos desnecessários, preservação das validações e consumo observado.
Consulte os [resultados e limites](docs/efficiency-validation.md) antes de inferir economia.

## Origem e limites

O desenho parte de práticas de desenvolvimento orientado por especificação, execução persistente com limites e arquitetura proporcional ao risco. Superpowers e UB-Mode são referências conceituais citadas no planejamento, não dependências incorporadas nem integrações verificadas. O conteúdo deste repositório é próprio; nenhuma implementação de terceiros foi copiada.

A licença de distribuição ainda será definida. Não publicar releases nem assumir permissão de redistribuição enquanto essa decisão estiver aberta.
