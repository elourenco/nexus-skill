# PLAN-NAMES — revisão 1 — aprovado

Fonte: [SPEC-NAMES](spec.md), revisão 1.
Direção aprovada: reutilizar normalize_name na implementação de normalize_names.

1. Concluído: definir contrato e verificar disponibilidade de unittest.
2. Pendente: implementar a função e regressões em names.py e test_names.py.
3. Pendente: executar python3 -B -m unittest discover -s . -v, revisar diff e
   registrar evidências na [TASK-NAMES](TASK.md).

Agente principal possui os dois arquivos. Não há tarefa paralela ou rollout.
Recuperação: reverter somente a alteração local caso necessária; nenhum dado migra.
Plano aprovado para execução; não requer nova proposta ou aprovação.
