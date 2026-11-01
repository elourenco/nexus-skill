# Workflows — evidências de validação

Data: 2026-10-31. Ambiente observado: macOS/POSIX, Python 3.14.6. Fontes em skills/nexus/scripts; fixtures sintéticas e temporárias, sem dados de consumidores. Python 3.10+ é o contrato de sintaxe/APIs; execução nesta sessão ocorreu apenas na versão informada.

## Testes automatizados

`python3 -m unittest discover -s tests -v`: **39 testes passaram**. Cobrem [orquestração e store](../tests/test_workflow.py) e [CLI](../tests/test_workflow_cli.py). As falhas esperadas foram observadas antes da implementação inicial e das correções de fronteira; não são bugs pendentes.

`python3 scripts/validate.py`: **OK**, metadados e links Markdown locais válidos. `git diff --check`: sem erros de whitespace nas alterações rastreadas. Essas verificações são complementares à suíte comportamental.

| Cenário solicitado | Evidência executada | Resultado |
| --- | --- | --- |
| 1. Correção FAST | test_fast_flow_requires_real_acceptance_before_delivery | Done/deliver rejeitados antes de teste e aceite; entrega aceita depois |
| 2. Feature com SPEC/PLAN | test_balanced_requires_spec_plan_and_detects_changed_contract | Requer artefatos; alteração silenciosa ou PLAN antigo impede execução |
| 3. Refatoração com dependências | test_dependency_blocks_start_until_predecessor_done; test_rework_invalidates_completed_dependents | Predecessor deve estar done; rework invalida dependentes |
| 4. Tarefa crítica/TDD | test_critical_tdd_requires_architecture_red_green_and_review; test_deep_mode_enforces_architecture_and_review | Architecture Gate, red, green, aceite e review exigidos |
| 5. Falha e recuperação | test_failure_budget_stops_retries_and_preserves_diagnostics; test_attempt_limit_cannot_be_reset_by_recovery | Duas falhas exigem diagnóstico; teto total de tentativas preservado |
| 6. Review com problema | test_review_finding_blocks_done_and_rework_invalidates_evidence; test_review_cannot_overwrite_a_blocking_finding_with_same_id | Achado bloqueia conclusão; colisão não apaga finding; rework exige novas provas |
| 7. Interrupção/retomada | test_interrupted_run_holds_resources_until_reconciled; test_stale_worker_result_cannot_finish_a_new_attempt | Estado reaberto conserva run/reserva; exige resultado reconciliado; recibo antigo rejeitado |
| 8. Provider indisponível | test_provider_unavailable_does_not_simulate_dispatch | Snapshot unavailable rejeita despacho sem consumir tentativa; bloqueio explícito registrado |
| 9. Budget esgotado | test_budget_uses_measured_data_and_stops_new_execution | Sem medição ou no limite, nenhum start; estimativa não vira consumo medido |
| 10. Paralelismo independente | test_independent_parallel_tasks_allowed_conflicts_rejected; test_concurrent_processes_cannot_lose_updates | Tasks disjuntas podem executar; CAS entre processos aceita somente um writer por revisão |
| 11. Ciclos | test_cycles_and_missing_dependencies_are_transactional | Dependência ausente/cíclica rejeitada sem alterar bytes do snapshot |
| 12. Atualização do Todo | test_cli_mutations_are_reflected_in_markdown_json_and_history | CLI altera estado; JSON, Markdown e histórico refletem a mudança |

Também foram exercitados lock com timeout, corrupção de JSON, falha antes do rename, falha de fsync após rename com resultado incerto, replay idempotente, cancelamento com recibo de parada, reserva durante validação bloqueada, conflito de diretórios/symlinks, campos desconhecidos, contador inteiro grande, pedidos de review pendentes e integridade de memória registrada.

## Demonstrações reais

`python3 skills/nexus/scripts/workflow.py demo --output-dir /tmp/nexus-workflow-demo` reproduz o fluxo completo em diretório novo. Na execução desta sessão, o demo BALANCED registrou **13 revisões**, teste red com exit 1, green com exit 0 e task/fluxo concluídos. Os dois testes executaram a função sintética real; não foram mockados. report.json, todo.md, red.txt, green.txt e o estado privado são gerados no diretório escolhido. O review incluído nessa receita é explicitamente autoinspeção, não revisão independente.

Uma segunda demonstração exerceu o handoff pelo host atual: create → register → ready → dispatch → chamada real da ferramenta de colaboração → ack → result → evidências → review → complete → deliver. O revisor independente inspecionou labels.py/test_labels.py e executou `python3 -B -m unittest discover -s . -v`: **2 testes passaram, exit 0, nenhum achado**. O estado recebeu handle real e 11 revisões. O papel review era gpt-6.1-sol/high, conforme a configuração exposta pelo runtime; provider e consumo ficaram desconhecidos. O coordenador realizou a chamada do host e registrou seu retorno; não foi implementado um adapter automático de provider.

## Revisão independente do executor

Revisor independente examinou fontes e realizou reproduções sem editar o worktree. Identificou liberação prematura de recursos durante validating, colisão de IDs de findings que apagava bloqueio e conversão de inteiro grande para float na CLI. Cada achado recebeu regressão e correção. Na segunda passagem, executou os 37 testes então existentes e confirmou as correções, inclusive rejeição atômica de review inválido e de recibo de geração anterior; nenhum novo achado material no escopo revisado.

Os dois testes finais adicionais cobrem timeout do lock e integridade da memória na entrega; também foi verificado que Context Pack inclui caminhos dos artefatos e proveniência da autorização. A execução final de 39 testes foi realizada pelo agente principal.

## Limitações verificadas

- Não existe Todo nativo com botões neste ambiente. Interação efetiva é por comandos da CLI; Markdown é projeção atualizável. Nenhuma sincronização com outros painéis foi afirmada.
- Registry e recibos descrevem capacidades/resultados informados pelo host. Testes de provider indisponível usam estado controlado; não houve falha induzida em serviço remoto nem integração por SDK.
- Budget não interrompe uma chamada externa em andamento nem garante teto financeiro. Tokens/custos não foram medidos nesta sessão.
- Testes de persistência injetam falhas de I/O; não simulam perda física de energia. Não houve teste de Windows, NFS, cloud drive ou coordenação entre hosts.
- Não foi realizado benchmark de latência/throughput. Tempos do demo são observações de um caso sintético, não capacidade do executor.
- `skill-creator/scripts/quick_validate.py` não executou no Python padrão por falta de PyYAML. Essa dependência pertence ao validador auxiliar, não ao pacote; nenhuma instalação global foi feita. A validação obrigatória do repositório é independente desse módulo.
- A CI existente da base executa a validação estrutural. A suíte nova foi executada localmente; não há evidência de execução remota da suíte nem de instalação em consumidores reais.

## Integração dos módulos — 2026-10-31

Resolução com main preserva memória JSON e runtime textual de agentes. Templates distinguem operação documental de operação pela CLI: store JSON é a única autoridade quando opt-in; `validating` precede `done`; `cancelled` é terminal; run incerto mantém reserva até `reconcile_run`. Cenários documentais verificados: editar projeção não altera store; retomar sem confirmação não libera recursos; revisão Markdown não substitui revisão global. A CI herdada de main descobre toda a suíte de memória/workflows em `tests/` e a suíte textual separada.
