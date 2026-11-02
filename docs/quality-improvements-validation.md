# Evidências do incremento 0.3.0 — 2026-11-02

Base de implementação: `30ffba2`. Nenhum helper foi ativado globalmente; o runtime
textual permanece separado. Não foram instaladas dependências novas.

## Cobertura dos sete itens

| Item | Entrega | Evidência observada |
| --- | --- | --- |
| Avaliações e hosts | Suíte de 11 cenários, fixtures, prepare/record/report e descoberta isolada | 10 testes do harness, 6 do protocolo dos hosts; seis entradas 0.3.0 encontradas no Codex e Claude; smoke textual 5+5 contextos independentes |
| Recibos no workflow | `evidence_policy`, `import_receipt`, revalidação em complete/deliver e proveniência declarada de review | 19 testes de recibos; tarefa/workspace/evento/registro/snapshot/run incorretos rejeitados; políticas ausentes preservam fluxo anterior |
| Pacote de review | Base/alvo Git, diff/hash/anexos/lacunas, modo commit ou worktree | 10 testes; staged/unstaged/untracked, não sobrescrita, mudança durante coleta, limites, filtros Git e newline |
| Modelagem | Checklist contextual domínio/fronteiras/ownership | Inspeção independente; corrigida distinção entre mutex em memória e locks locais entre processos |
| Checks seletivos | Receita de flags, thresholds/timeout e comandos do consumidor | Mutante real morto e sobrevivente quando teste é enfraquecido; contagem AST demonstrativa, sem alegar cobertura/CRAP genéricos |
| Procedimentos | Contratos curtos de entrada/decisão/evidência/saída e ações cognitivas explícitas | Smoke de pedido somente análise sobre entrada Build; sem alegar redução de tokens/latência |
| Consumidor mínimo | Demo executável, guia de adoção e escolha dos stores | 4 testes; pacote relocado somente leitura, ausência de overwrite e execução completa do fluxo de falha/recuperação |

## Comandos e resultados

```sh
python3 -B -m unittest discover -s tests -q
python3 -B -m unittest discover -s runtime/tests -q
python3 scripts/validate.py
python3 -B skills/nexus/scripts/hook_engine.py validate
python3 -B skills/nexus/scripts/consumer_demo.py --output-dir /tmp/nexus-consumer-final-20261102
git diff --check
```

- Helpers/pacote: **173 testes aprovados**. O baseline tinha 124 testes aprovados.
- Runtime textual: **56 testes aprovados**, sem alterações na implementação.
- Validador: metadados, links e manifestos aprovados; registro de **26 hooks** válido.
- Demo real: RED bloqueado; importação/conclusão rejeitadas; testes, check AST e
  mutação GREEN; edição posterior bloqueou delivery; rework/novo recibo encerrou
  em `delivered`, geração 1. Nada foi enviado a serviço externo.
- A execução inicial de um teste de crash foi bloqueada por consulta a grupos de
  processos, e a suíte do runtime por bind HTTP em loopback. Reexecução com as
  permissões locais necessárias passou. Isso não era falha funcional do patch.
- Avisos `ResourceWarning` de conexões SQLite existentes no baseline continuam
  aparecendo na suíte; sem novos warnings atribuídos aos componentes adicionados.

Os novos helpers começaram com testes RED por ausência das capacidades; os achados
do review também tiveram reprodução RED antes das correções e regressões GREEN.

## Avaliações de agentes e descoberta

[Recibo dos hosts](../evals/results/host-discovery-2026-11-02.json): Codex
`0.166.0-alpha.5.1` e Claude Code `2.1.308`, perfis temporários sem copiar credenciais.
Ambos listaram as seis entradas habilitadas da 0.3.0. Nenhuma inferência foi
executada nesses perfis; discovery não demonstra seleção implícita conversacional.

[Smoke comportamental](../evals/results/analysis-only-2026-11-02.json): cinco
contextos baseline e cinco contextos NEXUS, sem histórico herdado; mesmo papel
`implementation`, configurado Sol/medium. A skill foi fornecida por snapshot
congelado, com hashes no manifesto. Todos receberam limite de 180 palavras e
pedido apenas conceitual sobre dois threads atualizando um contador.

Um agente de testes independente avaliou manualmente as respostas: **10/10 no
escopo textual e 10/10 na análise de concorrência**. O baseline também passou:
esse recorte não comprova benefício adicional do NEXUS nem equivalência geral.
A rubrica de verificação proporcional foi interpretada como explicitar atomicidade,
invariantes e limites da evidência; não exigiu plano de teste. Essa ambiguidade
limita a força do resultado e deve ser eliminada antes de estudo comparativo maior.

Limites: somente um dos onze cenários foi repetido, condições não randomizadas,
avaliação não cega, sem rastros completos de ferramentas, latência/calls/leituras
desconhecidas (`null`). Passes descrevem conteúdo das respostas, não certificam
ausência de efeitos ou execução. O snapshot precede a correção textual sobre
locks locais; não se apresenta o smoke como certificação de cada byte final.

## Review independente

O revisor leu diff e fontes diretamente. Encontrou e reproduziu: execução/ocultação
por filtros Git, headers concatenados sem newline, leitura bloqueante do app-server
e ausência de integridade no snapshot sem núcleo. Correções verificadas com testes
e reproduções independentes. A coleta agora desabilita fsmonitor/diff externo/textconv
e rejeita filtros em arquivos rastreados no modo worktree. O protocolo dos hosts
usa deadline e limite de bytes, encerramento limitado e formato inválido inconclusivo.

Após as correções, review de código/documentação sem achados bloqueantes; revisor
reexecutou 30 testes focados, além de 19 testes de recibos na rodada anterior.
Recibos continuam confiando no operador/journal/relógio local, e identidades
informadas não autenticam independência. Captura Git não é transação de filesystem;
editores externos precisam estar parados. São limites assumidos, não garantias novas.
