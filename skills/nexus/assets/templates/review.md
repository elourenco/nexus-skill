# Review: ID — título

Use [contratos](contracts.md). Uma review registra um alvo/revisão e pode agrupar
vários achados; cada achado tem ID local estável (`F1`, `F2`). Não exige arquivo
por achado. Ausência de achados deve ser declarada, com limites da inspeção.

- Data e revisão do registro:
- task_id:
- spec_id (ou não se aplica — FAST):
- Pilar responsável e revisor:
- Alvo revisado (arquivos/linhas, diff, commit ou outra revisão verificável):
- Referências e critérios de aceite:

## Achado F1 — título (repetir somente quando houver achados)

- Severidade: crítica / alta / média / baixa
- Estado: aberto / corrigido / aceito / descartado
- Condição e impacto:
- Evidências reproduzíveis (procedimento/resultado ou EVIDENCE ID/link):
- Correção recomendada:
- Resolução (justificativa, responsável, data e evidência de revalidação):

## Decisão final

- Decisão: pendente / alterações necessárias / aprovado / aprovado com ressalvas
- Justificativa e limitações:
- Gates aplicáveis e resultado (fonte):

“Corrigido” exige revalidação; “aceito” exige registro do responsável autorizado
conforme o projeto; “descartado” exige evidência/justificativa. Findings bloqueantes
abertos impedem aprovação. Aceite de risco não dispensa gate obrigatório. Mudança
no alvo exige reavaliar a validade da review antes de usá-la para concluir a TASK.
