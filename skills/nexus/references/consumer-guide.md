# Guia mínimo para um projeto consumidor

NEXUS pode ser usado apenas como instrução textual. Use helpers locais quando precisar de estado verificável entre sessões; eles não substituem as permissões, ferramentas ou mecanismos de execução do host.

| Necessidade | Escolha |
| --- | --- |
| Uma mudança curta, acompanhada pelo Todo nativo | Skill textual e ferramentas do host; sem arquivo de workflow obrigatório |
| DAG, reservas de recursos, revisão CAS e gates recuperáveis | [Workflow JSON](workflow-state.md), criado explicitamente no consumidor |
| Checks locais autorizados, timeout e recibos por evento | [Hooks locais](hooks.md), registry revisado pelo consumidor e journal SQLite explícito |
| Evidência de testes vinculada aos arquivos atuais | Policy `hook_receipts` da task e ação explícita `import_receipt` |
| Conhecimento reutilizável entre sessões | [Memória JSON](memory.md), opt-in e com fonte; memória SQLite dos hooks permanece separada |

O workflow JSON contém estado e histórico das tarefas. O SQLite dos hooks contém eventos, recibos e memória local daquele executor. Não há sincronização automática entre stores. A importação de recibos relê o journal para verificar checks; ela não copia conhecimento entre memórias nem executa comandos.

## Rodar um consumidor sintético isolado

Mantenha `skills/nexus/` completo no local de instalação. Defina o caminho real do pacote e um **novo** diretório de saída; a demonstração recusa qualquer caminho existente, inclusive symlink:

```sh
NEXUS_PACKAGE=/caminho/da/instalacao/skills/nexus
python3 "$NEXUS_PACKAGE/scripts/consumer_demo.py" \
  --output-dir /tmp/nexus-consumer-example
```

Não é preciso instalar dependências. Requer Python 3.10+ e POSIX, conforme os helpers. A demonstração resolve imports no próprio pacote, desativa bytecode e executa comandos com o workspace do consumidor como cwd; não grava no pacote nem no cache de instalação. A saída criada contém `shipping.py`, `test_shipping.py`, `checks.py`, `.nexus/hooks.json`, `.nexus/local/workflow.json`, `.nexus/local/hooks.sqlite`, `.gitignore` e `report.json`. Execute novamente com outro diretório para obter uma execução independente. Não apague saída parcial automaticamente após falha: examine seu estado antes de decidir o descarte.

O domínio sintético concede frete grátis para total maior ou igual a 100. A demonstração observa, em processos reais:

1. Implementação com `> 100`: teste da fronteira falha; evento de hooks bloqueia; importação e conclusão são rejeitadas sem alterar o estado.
2. Correção para `>= 100`: testes, check estrutural mínimo e [mutation check](quality-checks.md) passam; recibo exato é importado, aceite dos três casos é declarado e task conclui.
3. Edição posterior do arquivo: entrega rejeita o snapshot antigo mesmo com task done.
4. `rework`: uma nova geração e tentativa executam checks novamente, importam novo evento e entregam o workflow.

O relatório registra gates e resultados observados, sem logs privados ou estimativas de qualidade de raciocínio. `green.mutation: passed` significa que o comando do consumidor observou seu mutante conhecido ser morto por assertion, após baseline aprovado; não representa cobertura de mutantes de um projeto real. O fixture não invoca providers nem produz revisão independente. O teste automatizado também enfraquece a assertion da fronteira e observa o mutante sobreviver, comprovando que a detecção depende do teste executado.

## Adotar os helpers no projeto real

Comece pelas instruções e pelas ferramentas já usadas no projeto. Defina recursos exclusivos, critérios observáveis e limites de tentativas. Exclua `.nexus/local/` do Git antes de registrar dados privados. A demonstração cria esse ignore somente no novo consumidor sintético; os demais helpers não alteram seu `.gitignore`.

Se decidir usar estado durável, inicialize explicitamente a partir do diretório consumidor:

```sh
cd /caminho/do/consumidor
python3 "$NEXUS_PACKAGE/scripts/workflow.py" init --workspace . --mode FAST
python3 "$NEXUS_PACKAGE/scripts/workflow.py" show --format json
```

Use o [contrato de operações](workflow-state.md) para criar tasks, atribuir autorização e executar `ready`, `start` e `result`. Cada request precisa de operation_id estável e expected_revision atual. O workflow não executa o trabalho em seu lugar. FAST dispensa artefatos formais adicionais, mas preserva testes/aceite e policies explícitas; BALANCED e DEEP acrescentam contratos e gates.

Para hooks, crie um registry do consumidor com os comandos reais de seu projeto. O registry do pacote valida este repositório documental e não demonstra lint, testes ou cobertura do consumidor. Revise `argv`, permissões, timeout, flags, thresholds e inputs. Não há instalação, ativação global ou adapter nativo automático. Você pode validar e listar o registry sem executar comandos:

```sh
python3 "$NEXUS_PACKAGE/scripts/hook_engine.py" validate --registry .nexus/hooks.json
python3 "$NEXUS_PACKAGE/scripts/hook_engine.py" list --registry .nexus/hooks.json
```

No consumidor sintético gerado, um evento equivalente a este executa todos os checks. Ele não deve ser emitido no workflow já entregue para tentar alterar sua conclusão; para uma nova execução coordenada, inicialize outro workflow ou use o ciclo autorizado apropriado antes da entrega:

```sh
cd /tmp/nexus-consumer-example
python3 "$NEXUS_PACKAGE/scripts/hook_engine.py" run \
  --registry .nexus/hooks.json --workspace "$PWD" --state .nexus/local/hooks.sqlite \
  --allow command:tests --allow command:complexity --allow command:mutation <<'JSON'
{"event_id":"manual-check-1","task_id":"DEMO-1","event":"test.completed","profile":"FAST","flags":["quality","mutation"],"files":["shipping.py","test_shipping.py","checks.py",".nexus/hooks.json"],"inputs":{}}
JSON
```

Preserve a lista exata de `task.files` e inclua código, testes, configuração e outros inputs relevantes. Recebimento de evento não implica aprovação: respeite gate/exit code. Durante uma tentativa atual, importe o event_id aprovado pela ação `import_receipt`; aceite por critério permanece explícito. Os exemplos completos de policy e request estão no [contrato do workflow](workflow-state.md).

## Concorrência, latência e recuperação

Use recursos `file:`, `dir:`, `db:` e `port:` para evitar conflitos entre tasks; eles coordenam somente o workflow selecionado, sem sandbox para ferramentas externas. Um journal compartilha deduplicação e um claim ativo por workspace. Para outro consumidor, use outro diretório/estado; não compartilhe bancos de testes ou portas por conveniência.

Os helpers são destinados a workflows locais pequenos. Hashes dos inputs e fsync custam I/O proporcional ao escopo; não há benchmark de throughput nem garantia de latência. Agrupe alterações relacionadas e execute checks compatíveis com o orçamento do perfil. Processos incertos conservam claims; investigue efeitos e use reconciliação explícita antes de repetir. Recibos antigos não validam outra geração. Alterações observáveis após um check exigem novos checks, e o host precisa preservar exclusividade até a entrega.

Esta receita comprova comportamento local do pacote copiado. Trust, instalação e eventos nativos de Codex/Claude e qualquer ambiente produtivo exigem validação própria; o fixture não comprova essas integrações.
