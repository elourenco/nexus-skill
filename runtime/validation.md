# Validação de agentes e review — 2026-10-31

Escopo: CLI textual opcional, separada da skill portátil. Ambiente local observado: Python 3.14.6. Nenhum provider externo foi chamado; nenhuma chave real foi usada. Os servidores HTTP de teste escutam somente em loopback e são encerrados ao terminar. No sandbox desta sessão, bind local exigiu execução autorizada fora da restrição de sockets.

## Resultado executado

`python3 -m unittest discover -s runtime/tests -v`: **56 testes aprovados**, sem falhas ou skips. Inclui CLI → router → Council → HTTP → parser para os dois protocolos, com resposta sintética contendo um achado verificável e decisão `CHANGES_REQUESTED`.

`inspect` com a configuração de exemplo retornou providers desabilitados, sem declarar autenticação verificada. Os testes de CLI comprovaram `BLOCKED` sem dispatch para provider indisponível, validação de entradas e roteamento sem I/O de rede.

`python3 scripts/validate.py`: metadados e links Markdown locais válidos. `git diff --check`: sem erros nos arquivos rastreados alterados.

## Aceite e cenários

| Critério | Evidência local |
| --- | --- |
| Responsabilidades claras | Registry com seis papéis; ferramentas vazias; Implementer, Tester e Memory Curator marcam handoff ao host |
| Modelos substituíveis | Alterar somente o identificador remoto na configuração muda a chamada construída |
| Providers ausentes | Sem credencial/disponibilidade produz BLOCKED; outro provider elegível continua utilizável |
| Independência de marca | Testes usam IDs sintéticos; catálogo e papéis não fixam modelos; protocolos ficam nos adapters |
| Pilares por risco | Seleção por arquivos/riscos; FAST agrupa; risco critical exige DEEP; apenas pilares aplicáveis |
| Deduplicação | Mesma descrição/localização/evidência consolida proveniência; bugs diferentes na mesma linha permanecem distintos |
| Falhas sem loops | Timeout não repete; saída inválida admite uma escalada compartilhada; falha parcial não aprova |
| Custos/limites | Reservas atômicas de chamadas e custo estimado; corrida de saldo reavalia candidato; uso acima da estimativa bloqueia novos dispatches |
| Um provider suficiente | Council DEEP sequencial conclui com um provider e contextos separados |
| Concorrência e recuperação | Sobreposição real limitada, concorrência de duas escaladas, deadline, recusa, quota/credencial, slow-drip, respostas grandes e redirects |

## Correções orientadas por reprodução

- Review sem snapshots de arquivos alterados: teste falhou antes; entrada agora é rejeitada antes do dispatch.
- `confidence` e usage com inteiros extremos: provocavam overflow ou eram aceitos; agora são rejeitados na fronteira de validação.
- Modelo preferido não cabia no saldo, mas outro cabia: teste reproduziu bloqueio indevido; seleção e admissão agora verificam saldo restante, inclusive corrida após roteamento.
- Uso observado acima da reserva: teste reproduziu dispatch adicional; a reserva agora cresce para refletir o uso informado.
- Streaming lento de bytes sem finalizar: teste reproduziu ausência de prazo de leitura; verificações monotônicas com `read1` interrompem o caso.
- Erros operacionais/pending/tools interpretados como truncamento: corrigidos para impedir escalada de capacidade indevida; apenas truncamento comprovado permanece escalável.

Uma revisão independente de código encontrou os três primeiros problemas de cobertura, robustez numérica e saldo; os cenários foram transformados em regressões. Testes de contrato não demonstram que um modelo real seguirá os prompts ou encontrará bugs. Não houve benchmark nem avaliação de qualidade de inferência.

Na reavaliação, o revisor confirmou as três correções, executou os 33 testes de engine/Council e não identificou novo bloqueador no escopo revisado.

## Limites da evidência

Compatibilidade autenticada com serviços, modelos disponíveis, preços vigentes, quotas e comportamento em projetos consumidores continuam não verificados. O código não garante teto financeiro remoto, deadline rígido envolvendo DNS nem cancelamento remoto. O histórico é restrito ao processo; não há coordenação de orçamento entre processos. A CI foi configurada para executar a suíte, mas execução remota não foi realizada nesta frente.
