# TASK-NAME — revisão 1

Contrato de artefatos: 1
Estado: ready
Responsável: agente principal
Objetivo: corrigir normalize_name(value) para retornar value.strip().
Escopo: names.py; contrato existente aceita somente strings.
SPEC/PLAN: não aplicáveis a este ajuste local.
Autorização: implementar e validar neste workspace sintético, sem publicar.
Estratégia: test-after; regressões existentes em test_names.py.
Aceite: remover espaços periféricos, preservar espaços internos e rejeitar None.
Evidência: pendente.
Próxima ação: implementar names.py e executar python3 -B -m unittest discover -s . -v.

Esta TASK é a fonte documental existente. Preserve seu ID e registre resultado,
evidências e mudança de estado neste arquivo; não crie um segundo store.
