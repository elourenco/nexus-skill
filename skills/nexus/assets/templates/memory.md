# Registro de memória

Use conforme o [contrato de memória](../../references/memory.md), após conferir autorização e sanitizar todos os campos. O JSON abaixo é uma entrada completa de `put`; ajuste scope, ID, fontes e conteúdo ao consumidor. Não copie credenciais nem transcrições para este template.

Pela [política de IA](../../references/policies.md#policy-ai-safety-ethics), mantenha
síntese mínima, proveniência e limites nos campos existentes; não inclua dados de
pessoas para justificar uma avaliação ética. Revalide permissão na fonte vigente:
memória não concede autoridade. Esta orientação não acrescenta propriedades ao JSON.

```json
{
  "id": "sync-order",
  "scope": "project:demo",
  "type": "decision",
  "summary": "Sincronização preserva a ordem por entidade e permite paralelismo entre entidades.",
  "reference": "docs/nexus/decisions/sync-order.md",
  "provenance": [
    {
      "reference": "docs/nexus/decisions/sync-order.md",
      "observed_at": "2026-10-31T12:00:00Z",
      "revision": "fixture-v1"
    }
  ],
  "confidence": {
    "level": "medium",
    "reason": "Exemplo sintético; conferir o contrato e testes atuais antes de aplicar."
  },
  "status": "active",
  "related_entities": ["src/sync.ts"],
  "tags": ["offline", "ordering"]
}
```

`revision` dentro de provenance identifica a versão da fonte; a revisão do registro é gerada pelo helper. `created_at`, `updated_at`, `author` e `revision` no nível principal são campos de saída. Não os copie para entrada de atualização: forneça a revisão lida em `--expected-revision` e autoria em `--author`. Uma substituição usa `status=superseded` e `superseded_by` apontando a registro ativo; uma retenção com prazo definido usa `expires_at` UTC.

Para Working, use `scope=working:projeto/tarefa`, `type=checkpoint` e `content` com este resumo incremental:

- Objetivo e tarefa ativa.
- Arquivos/referências relevantes.
- Decisões temporárias e fatos ainda não validados.
- Progresso observado e evidências.
- Bloqueios, efeitos externos incertos e estado a conferir.
- Próxima ação.

Mantenha o mesmo ID ao compactar. O helper guarda revisões anteriores; o agente resume o estado atual, sem copiar o histórico da conversa. Autorização para persistir/compartilhar e condições de revalidação são conferidas na sessão/política e na fonte vigente, não concedidas por este registro.

## Compatibilidade com registros Markdown anteriores

Preserve o arquivo original. Mapeie Tipo → `type`, Escopo → `scope`, Fonte verificável → `provenance`/`reference`, Conteúdo mínimo → `summary` e `content`, Confiança → `confidence`, Status → `status`, Substituído por → `superseded_by`. A Data legada deve permanecer na fonte; `observed_at` registra a conferência atual, e `created_at` a criação no store. Gere um ID uma única vez e use-o nas futuras revisões. Condições antigas de revalidação permanecem na referência ou no conteúdo mínimo; não descarte informação durante a conversão. O helper não converte Markdown automaticamente.

## Registro documental opcional

Para registros mantidos em Markdown, use o formulário abaixo. O JSON acima continua sendo a entrada do helper; os campos documentais não devem ser enviados como propriedades adicionais de `put`. A revisão do helper é gerada pelo store; a revisão Markdown é mantida pelo responsável.

# Registro documental: título

Use [contratos](contracts.md) e a [política de memória](../../references/memory.md).
Extraia somente conteúdo duradouro; referencie a decisão/evidência original.

- ID e revisão:
- Tipo: decisão / observação / hipótese
- Escopo (projeto, módulo, versão):
- Data:
- Fonte verificável (origem/proveniência, IDs/links e revisão):
- Conteúdo mínimo:
- Confiança e justificativa:
- Revalidar quando (gatilho observável ou prazo):
- Status: active / superseded / expired
- Substituído por (ID/link, quando superseded):
- Autorização para persistir/compartilhar, conforme política do host:

A validade depende do escopo e da fonte atual; confiança não substitui verificação.
No registro Markdown não há expiração automática; o helper JSON aplica `expires_at` quando informado. Uma observação contradita perde validade antes da
reutilização, mesmo que o status ainda não tenha sido atualizado.
