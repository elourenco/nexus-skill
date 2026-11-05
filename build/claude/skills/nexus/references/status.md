# Status

Aplique o [contrato mínimo](invocation.md). Status informa estado; não autoriza
executar testes, editar, retomar jobs ou publicar. Use a fonte existente e os dados
fornecidos quando suficientes; não inicialize store, TASK ou workflow.

## Decisão e evidência

- Identifique alvo, revisão e origem do estado. Separe evidência observada, relato
  recebido e informação ainda desconhecida; não invente inspeção atual.
- Evidência só vale para inputs, revisão, configuração, ambiente e run/geração
  aplicáveis. Mudança relevante invalida a cobertura afetada. Resultado de A não
  comprova B; ausência de resultado também não comprova falha.
- Check obrigatório ausente/bloqueado ou review independente exigido e indisponível
  impede concluir o objeto. Declare o gate e próxima ação; custo/prazo não o dispensa.
- Resultado externo incerto exige reconciliação por identidade antes de repetir
  efeitos. `running`, timeout e cancelamento não comprovam término ou rollback.
- Fontes divergentes exigem consulta autorizada à autoridade pertinente. Se acesso
  faltar ou o pedido proibir execução, reporte a incerteza e a ação necessária.
  Só então expanda para [retomada](workflow.md#checkpoint-cancelamento-e-retomada)
  ou [recuperação](policies.md#tentativas-e-recuperação) quando esse detalhe faltar.

Com fontes suficientes e atuais, entregue estado, evidências, pendências e próxima
ação e encerre. Não carregue Policies, Agents ou Workflow apenas para repetir um
gate já explícito. O relatório pode estar concluído enquanto o objeto permanece
bloqueado. Um pedido adicional de execução usa a rota da pendência autorizada.
