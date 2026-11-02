# Entradas especializadas NEXUS

Proposta aprovada no chat: manter `nexus` como entrada geral e oferecer
`nexus-brainstorming`, `nexus-plan`, `nexus-build`, `nexus-debug` e `nexus-review`.
Execução local pelo agente principal; agentes independentes apenas para avaliação.

## Contrato e decisões

- A fonte de verdade continua em `skills/nexus/`: contrato de invocação e cinco
  procedimentos em `references/`. As cinco pastas irmãs são entradas finas.
- O núcleo isolado continua funcional por linguagem natural. As entradas
  especializadas exigem o núcleo como pasta irmã; ausência bloqueia a execução
  NEXUS afetada e deve ser informada, sem inventar instalação ou política.
- Explore/Plan/Build/Review e FAST/BALANCED/DEEP permanecem inalterados; status e
  retomada ficam em `nexus`. Nenhum novo runtime, scheduler ou estado persistente.
- Sem instalação global, commit, push, deploy, dependências ou modelos fixos.
- Descrições delimitam descoberta; somente o procedimento selecionado é carregado.
  Invocação não cria subagente nem paralelismo. Estado e recursos continuam sob
  os contratos existentes de workflow, ownership e recuperação.

## Entregas e verificações

- [x] Registrar baseline de descoberta e roteamento com pacote anterior.
- [x] Testar e ampliar `scripts/validate.py` para todas as entradas, metadados,
  nomes e referências; testar pacote copiado e núcleo isolado.
- [x] Criar contrato compartilhado e procedimentos com entrada, saída, limite
  de autorização e condição de parada; avaliar cada entrada com cenário realista.
- [x] Atualizar `skills/nexus/SKILL.md` e `README.md` com roteamento e instalação
  conjunta verificável; documentar sintaxe por host sem alegar instalação.
- [x] Registrar cenários/resultados em `docs/entrypoints-validation.md`, incluindo
  dependência ausente, review sem correção, autorização existente e retomada incerta.
- [x] Executar validador, testes pertinentes, revisão independente e corrigir achados.

## Foco da revisão

Instalação de entrada sem núcleo; divergência entre entrada geral e especializada;
roteamento concorrente entre skills; correção indevida em pedido de review;
repetição de efeito externo incerto; testes estruturais confundidos com execução
real no seletor de um host. As avaliações usam somente fixtures sintéticas.
