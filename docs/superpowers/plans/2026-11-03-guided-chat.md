# Chat guiado NEXUS — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox tracking.

**Goal:** orientar chat guiado com componentes existentes no host e texto portátil como fallback.

**Architecture:** contrato textual compartilhado em `skills/nexus/references/`,
carregado pelo núcleo e pelo contrato das entradas especializadas. A apresentação
projeta a fonte existente; não cria store, UI runtime, adapter ou serviço.

**Tech Stack:** Markdown e ferramentas já expostas pelo host.

**Spec:** descrição aprovada no chat em 2026-11-03: resumo de situação, listas de
tarefas, decisões contextualizadas, evidências acessíveis e atualizações relevantes;
seleção por capacidade verificada do aplicativo, com texto portátil como fallback.

## Restrições

- Preservar alterações preexistentes e fronteiras do pacote portátil.
- Sem dependências, instalação, caches, commit, push ou publicação.
- Instruções e autorizações do host prevalecem; UI não concede permissão.
- Fonte única; ações obsoletas e resultados incertos exigem reconciliação.
- Contagem de tarefas não estima esforço; consumo e duração só quando observados.

## Foco da revisão

- Host somente texto: mesmas decisões e evidências, sem botões fictícios.
- Host com UI parcial ou ferramenta proibida no modo atual: fallback por capacidade.
- Lista nativa editável: não criar uma segunda autoridade sem sincronização real.
- Clique duplicado, revisão alterada ou timeout: não repetir efeitos incertos.
- Consulta simples ou status: apresentação proporcional, sem iniciar trabalho.

## Tarefa 1 — contrato e integração

Arquivos: criar `skills/nexus/references/chat.md`; integrar em
`skills/nexus/SKILL.md`, `skills/nexus/references/invocation.md` e `README.md`.

- [x] Observar baseline com consumidor em contexto novo antes da edição.
- [x] Definir composição, seleção de recursos, fallback e limites de interação.
- [x] Conectar núcleo e entradas especializadas sem duplicar o contrato.

## Tarefa 2 — aplicação e validação

Arquivo: criar `docs/guided-chat-validation.md` com cenários, resultados e limites.

- [x] Aplicar contrato em novos consumidores: UI rica, texto, UI parcial,
  status, revisão desatualizada, duplicação e resultado incerto.
- [x] Revisar o incremento isoladamente, preservando trabalho preexistente.
- [x] Executar `python3 scripts/validate.py`, testes de pacote pertinentes e
  `git diff --check`; registrar o que foi efetivamente observado.

## Registro

Implementação pelo agente principal; consumidores/revisor somente leitura.
Baseline `chat_baseline`: fonte única e retry incerto já tratados, mas escolha de
componentes, composição e vínculo entre ação/revisão não tinham contrato específico.
Snapshots dos três arquivos preexistentes guardados fora do repositório para
revisar apenas este incremento. Execução autorizada pelo pedido do usuário;
o plano registra essa direção sem reabrir aprovação já concedida.

Concluído: `chat_consumer` aplicou seis cenários; `chat_review` revisou o incremento
e quatro cenários de interação, sem achados acionáveis. Validador, 19 testes
de pacote/portabilidade e diff-check aprovados. Resultados e limites em
[Validação do chat guiado](../../guided-chat-validation.md).
