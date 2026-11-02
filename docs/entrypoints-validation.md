# Validação das entradas especializadas

Data: 2026-11-02. Escopo: descoberta no pacote, contratos de invocação, referências
relocáveis e aplicação dos procedimentos por agentes em cenários sintéticos.
Não constitui certificação de instalação ou seleção automática em hosts consumidores.

## Baseline

Snapshot anterior às alterações, avaliado por agente de testes independente:
somente `skills/nexus/SKILL.md` existia. Os nomes `nexus-brainstorming`, `nexus-plan`,
`nexus-build`, `nexus-debug` e `nexus-review` não eram encontráveis como entradas.
O núcleo já oferecia fallback por modo; a inspeção não demonstrou falha geral de
autorização ou roteamento. Essa ausência de entradas é a lacuna tratada.

Os testes do validador foram executados antes da alteração: ele ignorava metadados
de skills irmãs, nomes inválidos e pastas de skill sem entrada. A cópia para o
diretório temporário do macOS também revelou comparação entre raiz não canônica e
destinos resolvidos; a raiz agora é normalizada antes de verificar contenção.

## Aplicação por agente consumidor

O avaliador recebeu a entrada e um pedido sintético, sem resposta esperada. Leu
referências sob demanda e executou a atividade pedida. O agente principal inspecionou
as respostas. Uma amostra por cenário não mede taxa de aderência entre modelos.

| Caso | Pedido / insumos | Resultado observado |
| --- | --- | --- |
| Brainstorming | App de inspeção offline até 48h; dois dispositivos alteram notas e status; snapshots causaram perda de notas; REST/banco relacional, equipe de 2 pessoas, sem métricas. Apenas discutir. | Comparou snapshot versionado, operações incrementais e CRDT; recomendou operações incrementais/versionamento, preservou decisão aberta sobre semântica das notas, explicitou timeout/deduplicação, isolamento e migração de clientes. Não implementou nem alegou medições. |
| Plan | Versão otimista e HTTP 409 já aprovados; rascunho local preservado; API e app separados, banco e porta de testes compartilhados; somente plano. | Preservou a decisão e entregou seis etapas com contratos, dependências, testes de atomicidade, compatibilidade e rollback. Reservou banco/porta para validação serializada; não escreveu arquivos nem implementou. |
| Build | Workspace temporário com plano aprovado, função `normalize_labels` inicialmente retornando a entrada e três testes de normalização/ordem/imutabilidade. Alterações locais e testes já autorizados. | Observou a regressão (1 falha em 3 testes), implementou somente `labels.py` com conjunto local e obteve 3/3 passando. Não pediu nova aprovação, não publicou nem criou estado persistente. O agente principal inspecionou o arquivo e repetiu os 3 testes com sucesso. |
| Debug | `dispatch.py` reenvia em `TimeoutError`; trace mostra `r1` aceito como `j100`, resposta perdida e `r2` aceito como `j101`; fila sem deduplicação contratual. Só diagnosticar. | Relacionou duplicação ao retry de mutação com resultado incerto; distinguiu efeito confirmado no trace de comportamento de produção não verificado. Não executou envio, não corrigiu e não inventou saturação/concorrência. |
| Review | Diff introduz retry em `TimeoutError`; código e trace sintéticos da duplicação, sem permissão para corrigir. | Achado high em `dispatch.py:4–5`, trigger/impacto/evidência/recomendação e decisão CHANGES_REQUESTED. Leu alvo diretamente, calculou hash e não alterou código nem enviou jobs. |

Os cinco casos usaram o mesmo agente consumidor em sequência: ele reutilizou
políticas já lidas. Isso avalia continuidade com referências compartilhadas, não
cinco contextos frios independentes. Um segundo agente executou os casos de borda
abaixo; o review final do pacote foi feito por um terceiro agente, sem a narrativa
do implementador.

Fontes lidas no caso de brainstorming: entrada especializada, contrato de
invocação, procedimento, Policies e Cognitive Principles. Nenhum arquivo do
consumidor foi alterado; nenhum helper, hook ou subagente foi criado pela entrada.

## Instalação isolada e limites de escopo

Foram copiadas pastas para diretórios temporários fora do repositório. O avaliador
recebeu apenas caminhos e pedidos, sem critérios de resposta embutidos.

| Caso | Resultado observado |
| --- | --- |
| Apenas `nexus-review/`, núcleo ausente | Tentativas de leitura de `invocation.md` e `review.md` falharam com arquivo ausente; informou os dois caminhos e interrompeu o fluxo, sem usar outra instalação. |
| Apenas `nexus/`, pedido “Brainstorming do NEXUS” | Leu contrato e procedimento local, comparou snapshots/ operações e entregou recomendação condicionada às informações disponíveis; não exigiu entrada irmã. |
| Status com `TASKS.md` existente e T1 `running` | Informou estado registrado e incerteza do worker real; nenhuma execução, store novo ou alteração de arquivo. |
| Retomada da mesma T1, resposta perdida e worker inacessível | Não reenviou nem criou workflow. Informou impedimento e necessidade de evidência de parada/conclusão; distinguiu bloqueio na resposta de persistência não realizada. |
| `nexus-build` com pedido “apenas planeje; não implemente” | Escolheu Plan pelo limite explícito do usuário, entregou etapas e não escreveu código. |

Essas verificações usaram leitura direta dos arquivos, sem instalação global ou
seleção automática em Codex/Claude Code. A reconciliação foi avaliada por decisão
do agente diante de evidências sintéticas; nenhum worker remoto real foi consultado.

## Insumos sintéticos reproduzíveis

Build: `normalize_labels(values: list[str]) -> list[str]` começou retornando `values`.
Plano: aplicar `strip` e `lower`, ignorar vazias e deduplicar por conjunto local
preservando a primeira ocorrência e a lista de entrada. Três testes verificaram
entrada vazia; `[' Foo ', 'bar', 'FOO', '', '  ', 'BAR', 'baz']` resultando em
`['foo', 'bar', 'baz']`; e preservação de `[' A ', 'a']` após a chamada.

Debug/review usaram este alvo completo; o diff substituía o envio direto pelo `try`:

```python
def dispatch(queue, payload):
    try:
        return queue.submit(payload)
    except TimeoutError:
        return queue.submit(payload)
```

Trace: fila sem deduplicação contratual; `r1` enviado em `10:00:00.000` e aceito
como `j100` em `10:00:00.010`; resposta perdida e timeout em `10:00:05.000`; `r2`
enviado em `10:00:05.001` e aceito como `j101` em `10:00:05.011`. Ambos referiam
`operation=job-42`. A conclusão não dependeu de inferir falha remota a partir de timeout.

Retomada: `TASKS.md` documental com T1 `running`, checkpoint de envio ao `worker-42`
e resposta perdida. Nenhuma ferramenta de consulta ao worker estava disponível.

## Verificações estruturais

`python3 -m unittest discover -s tests -p test_validate.py -v`: 10 testes passaram
após a correção do validador, na etapa com a entrada de brainstorming.
Cobertura: metadados de múltiplas skills, nomes, frontmatter ausente/duplicado,
pasta sem entrada, dependência ausente, escape do pacote, cópia do núcleo isolado
e cópia do pacote completo disponível naquele momento.

A suíte completa `python3 -m unittest discover -s tests -v` passou com 115 testes
em 15,235 s nesta etapa. Foram emitidos `ResourceWarning` de conexões SQLite não
fechadas durante a suíte existente; não houve falha. Não foi alterado código de
hooks/memória para esta entrega.

O `quick_validate.py` da skill de autoria foi tentado, mas o Python padrão não
possui PyYAML (`ModuleNotFoundError: yaml`). Nenhuma dependência foi instalada;
o validador do próprio projeto cobre os dois campos escalares efetivamente usados
no pacote e os links locais. Essa verificação não equivale a um parser YAML geral.

O review independente inspecionou diff, novas entradas/referências, testes e
instalação e não encontrou achados acionáveis. Também executou `validate()` sobre
cópias do núcleo isolado e do pacote completo, ambas sem erros. Isso não demonstra
descoberta nos seletores dos hosts nem aderência estatística de modelos.

## Resultado final

- `python3 scripts/validate.py`: aprovado para as seis entradas e links locais.
- `python3 -m unittest discover -s tests -p test_validate.py -v`: 12 testes de
  pacote aprovados, incluindo núcleo ausente, conjunto exato de seis entradas e
  raiz acessada por symlink.
- `python3 -m unittest discover -s tests -q`: 117 testes aprovados em 13,369 s;
  os mesmos avisos de conexão SQLite não fechada apareceram, sem falhas.
- `git diff --check`: sem erros.
- Cinco cenários de procedimentos e cinco cenários de borda aplicados por agentes;
  implementação sintética validada por 3 testes antes/depois. Sem benchmark de
  latência ou throughput de agentes e sem afirmar taxa de acerto de roteamento.

Na implementação inicial, o runtime textual em `runtime/` não foi alterado nem sua
suíte executada. Essa etapa não realizou instalação global, commit, push ou publicação.

## Integração com empacotamento de plugins para o PR

A base `main` passou a conter o empacotamento de plugins (`ddc84ae`). A integração
preserva `validate()` como verificação completa de manifestos/catálogos e skills;
`validate_skills()` valida as cópias standalone sem exigir manifestos. Os testes
de plugins da base foram preservados. Os dois manifestos passam a `0.2.0` para
distinguir o pacote com seis entradas do cache da versão inicial `0.1.0`.

Após a integração:

- `python3 scripts/validate.py`: aprovado.
- `python3 -m unittest discover -s tests -q`: 124 testes aprovados em 13,348 s,
  incluindo 12 testes das entradas e 7 de plugins; avisos SQLite persistem.
- `python3 -m unittest discover -s runtime/tests -q`: 56 testes aprovados.
- `python3 skills/nexus/scripts/hook_engine.py validate`: registro válido, 26 hooks.
- Review independente da integração: sem achados acionáveis; confirmou os testes
  de plugins intactos e distinção entre descoberta standalone/plugin.

Os testes de runtime precisaram de permissão para HTTP em loopback; um teste de
crash precisou consultar grupos de processos. As execuções inicialmente bloqueadas
pelo sandbox foram repetidas com essas permissões e passaram. Nenhuma mudança de
comportamento de runtime foi feita. Descoberta das novas entradas nos seletores
de hosts e instalação global da versão 0.2.0 continuam não verificadas.
