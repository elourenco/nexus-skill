# Plano — evidência, avaliação e adoção do NEXUS

Implementação autorizada em 2026-11-02 a partir dos sete itens da análise comparativa.
Base: `30ffba2`. Núcleo portátil em `skills/nexus/`; runtime textual separado.

## Contratos

- Python 3.10+, biblioteca padrão, sem serviços/dependências novas.
- Helpers continuam opt-in; estado do consumidor fica fora do pacote instalado.
- Preservar operações antigas do workflow; requisitos novos só por política explícita.
- Evidência declarada, recibo de execução e independência autenticada são distintos.
- Nenhuma configuração global, publicação ou operação externa implícita.
- Checks caros têm escopo e timeout; nenhuma promessa de performance sem medição.

## Unidades e aceite

1. **Avaliações** — fixtures, prompts, rubricas, preparação/registro/relatório de
   amostras baseline/NEXUS independentes. Ausência de dados é inconclusiva;
   métricas indisponíveis são nulas. Testar integridade e agregação; verificar
   instalação/listagem das seis entradas em perfis temporários dos hosts.
2. **Recibos** — política opcional por tarefa e importação explícita de evento
   do journal dos hooks; verificar tarefa/workspace/registro/snapshot/comando.
   Revalidar em conclusão/entrega. Testar falha, obsolescência, rework, operação
   idempotente e compatibilidade. Proveniência de review é declarada pelo host.
3. **Pacote de review** — coletar base/alvo Git, diff, hashes, brief/evidências
   e lacunas, inclusive trabalho não commitado; sem commit obrigatório. Testar
   alvo inválido, mudança durante captura, untracked explícito e não sobrescrita.
4. **Modelagem** — checklist contextual de estados válidos, parsing na fronteira,
   núcleo determinístico e ownership de estado, sem impor camadas.
5. **Checks de qualidade** — receita configurável sobre hooks existentes:
   mutation testing seletivo, complexidade e duplicação como sinais, limites
   definidos pelo consumidor, falha/timeout nunca equivalentes a sucesso.
6. **Procedimentos** — entrada, decisão, evidência e saída visíveis; ações
   cognitivas antes dos nomes conceituais, sem remover gates ou criar fases.
7. **Consumidor mínimo** — execução real de check falhando, gate bloqueado,
   correção, check passando, importação e conclusão; demonstrar obsolescência.
   Escolha explícita entre estado do host/workflow/memória/checkpoint técnico.

## Execução e validação

- [x] Testes novos antes da implementação dos helpers; registrar RED/GREEN.
- [x] Cenários de aplicação independentes para instruções alteradas.
- [x] Integração do exemplo com os contratos finais.
- [x] `python3 scripts/validate.py`, suíte `tests/`, suíte `runtime/tests/`,
  validação do registro de hooks, diff e exemplo relocável.
- [x] Review independente do diff completo; corrigir achados e revalidar.
- [ ] Commit, push e PR com evidências e limites observados.

## Foco do review

Recibos de outra tarefa/generation; mudanças após verificação; contorno por evidência
declarada; paths/symlinks e saída sobrescrita; perda de dados no exemplo; efeitos
incertos após timeout; avaliações sem amostra ou com rubrica incompleta; compatibilidade
dos consumidores existentes. Testes de cada unidade devem cobrir esses casos.
