# Registro de memória

Use conforme o [contrato de memória](../../references/memory.md), após conferir autorização e sanitizar todos os campos. O JSON abaixo é uma entrada completa de `put`; ajuste scope, ID, fontes e conteúdo ao consumidor. Não copie credenciais nem transcrições para este template.

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
