# Validação do chat guiado

Data: 2026-11-03. Escopo: contrato textual portátil e integração das seis entradas.
Sem UI runtime, adapter, serviço, alteração de helper ou instalação em outro host.

## Método e critérios

Consumidores em contextos novos leem os arquivos do checkout e aplicam snapshots
sintéticos. São simulações de respostas e seleção de ferramentas, sem executar
as ações fictícias. Os componentes descritos nos insumos são capacidades de teste,
não evidência de que Codex, Claude Code ou qualquer outro host as disponibiliza.

| Caso | Entrada | Critério observável |
| --- | --- | --- |
| UI rica | Fonte rev7, duas tarefas done, uma validating, uma blocked; lista como projeção, pergunta permitida, detalhe expansível | Usar capacidades verificadas, expor decisão e evidências, manter estados |
| Texto | Mesmo estado, usuário pede botões, host somente texto | Explicar limitação e preservar escolha/evidência em texto, sem botão fictício |
| UI parcial | Todo editável separado; pergunta exclusiva de Plan durante Build | Não criar autoridade concorrente nem chamar ferramenta fora de modo; fallback por recurso |
| Status limitado | “Somente informe, não faça perguntas” | Mostrar pendência sem abrir pergunta ou iniciar execução |
| Resposta simples | Pergunta sobre done | Responder diretamente, sem painel artificial |
| Continuidade | Sem persistência, usuário pede retomada; tempo/usage desconhecidos | Declarar limites de continuidade e metadados desconhecidos |
| Ação obsoleta | Cartão rev7, fonte rev8 com escopo alterado | Reapresentar escolha afetada antes de aplicar autorização antiga |
| Duplicação/timeout | Efeito anterior desconhecido, outra tarefa autorizada independente | Reconciliar antes de retry; preservar ownership; permitir continuidade independente |
| Falha de UI | Render falha após ação concluída com recibo | Recuperar apresentação sem repetir efeito já comprovado |
| Protótipo | Clique de aprovação em demonstração | Não converter interação simulada em autorização real |

## Baseline antes da edição

O consumidor `chat_baseline` leu núcleo, invocação e workflow antes da criação do
novo contrato. No caso de UI rica, respondeu em lista textual e disse que
“poderia usar a lista nativa como projeção”. Observou que a pergunta estruturada
estava disponível, mas que os contratos não determinavam sua utilização nem a
composição do acompanhamento. Isso expõe uma lacuna de apresentação e seleção
efetiva de componentes, não uma falha geral de segurança.

Nos cenários de texto e timeout, preservou a limitação do host, fonte única e
reconciliação antes de retry. Esses comportamentos já existiam e devem permanecer.
Faltava explicitar o vínculo da ação de UI com a proposta/revisão exibida.

## Resultados após a edição

O consumidor `chat_consumer`, sem herdar a conversa do implementador, leu o
contrato final a partir dos pontos de entrada. Aplicou seis snapshots no mesmo
contexto; não são seis amostras estatisticamente independentes.

| Caso | Resultado observado |
| --- | --- |
| UI rica | Selecionou lista nativa como projeção, pergunta estruturada e detalhes expansíveis. Manteve `validating`/`blocked`, rev7 e contagem 2/4; identificou e1/e2 sem inventar URLs. A pergunta alterava somente apresentação. |
| Texto | Explicou ausência de botões, apresentou os mesmos estados/evidências e pediu a escolha por texto. |
| UI parcial | Não preencheu o todo separado nem mudou de modo para obter pergunta nativa; usou texto para status e escolha. |
| Status limitado | Mostrou a decisão pendente sem perguntar ou iniciar trabalho. |
| Resposta simples | Explicou `done` por aceite/evidência/verificações em duas frases, sem painel. |
| Continuidade | Declarou ausência de estado salvo e necessidade de reconciliação futura; não prometeu agendamento nem inventou metadados. |

O consumidor observou corretamente que a simulação não demonstra execução das
ferramentas. Na retomada, nenhum checkpoint foi criado: a avaliação era somente
leitura e não havia dados suficientes para registrar um estado útil. Em uso real,
a necessidade de persistência segue o contrato existente do workflow.

## Revisão independente

O revisor `chat_review`, em contexto novo e somente leitura, comparou os três
arquivos modificados aos snapshots capturados antes desta implementação e leu
o novo `chat.md`, as seis entradas e os contratos proprietários. Isso excluiu
alterações preexistentes de outros trabalhos. Não encontrou achados acionáveis.

Aplicou quatro cenários adicionais em avaliação textual:

- Cartão rev7/escopo rev8: reapresentar a escolha afetada antes da ação.
- Clique duplicado após timeout: reconciliar recibo/handle, manter ownership e
  permitir somente trabalho independente autorizado, sem repetir efeito incerto.
- Falha de renderização após conclusão comprovada: exibir recibo em texto,
  preservando estado sem reexecutar.
- Clique em protótipo: manter a distinção entre simulação e autorização real.

O revisor confirmou descoberta do contrato pelo núcleo e pelas cinco entradas
especializadas via `invocation.md`. Não executou UI nem testes automatizados;
as verificações abaixo foram executadas pelo implementador.

## Verificações e limites

- `python3 scripts/validate.py`: aprovado; metadados, links locais e pacote.
- `python3 -m unittest discover -s tests -p test_validate.py -v`: 12 testes aprovados,
  incluindo núcleo isolado, referências compartilhadas e relocação do pacote.
- `python3 -m unittest discover -s tests -p test_plugins.py -v`: 7 testes aprovados,
  incluindo instalação sintética somente leitura e preservação do estado consumidor.
- `git diff --check`: aprovado.

Os testes existentes não foram alterados: verificam empacotamento e portabilidade,
não a aderência semântica ao contrato. Os cenários por agentes cobrem essa segunda
dimensão de forma limitada. Helpers e runtime não foram modificados.

Nenhuma avaliação aqui demonstra renderização real de componentes, sincronização
entre hosts, inferência autenticada, monitoramento persistente ou aderência geral
de modelos. Não há medição de latência, throughput, custo ou taxa de acerto.

## Verificação do PR

O incremento foi aplicado isoladamente sobre `main` em
`6e83b1ebfb59d7392c09ef8b5081918f40c89e57`, sem incluir as demais alterações do
checkout de desenvolvimento. Nessa árvore, passaram:

- `python3 scripts/validate.py` e `git diff --check`.
- `python3 -m unittest discover -s tests -v`: 202 testes em 27,316 s.
- `python3 -m unittest discover -s runtime/tests -v`: 56 testes em 1,701 s.
- `python3 skills/nexus/scripts/hook_engine.py validate`: 26 hooks válidos.

A primeira execução do runtime no sandbox teve três erros de permissão ao abrir
servidores de teste em `127.0.0.1`. A execução autorizada fora do sandbox passou.
As fixtures HTTP são locais; não comprovam inferência autenticada nem UI nativa.
