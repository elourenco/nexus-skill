# Runtime textual de agentes e review

CLI opcional em Python 3.10+, sem dependências externas. Executa planejamento, análise e review por API; não edita projetos, executa comandos/testes, grava memória ou chama agentes nativos do host. `skills/nexus/` continua sendo uma skill portátil independente deste diretório.

## Uso

Na raiz do repositório:

```sh
python3 -m runtime.nexus_runtime --config runtime/config.example.json inspect
python3 -m runtime.nexus_runtime --config runtime/config.example.json route --task runtime/task.example.json
python3 -m runtime.nexus_runtime --config runtime/config.example.json run --task runtime/task.example.json
python3 -m runtime.nexus_runtime --config runtime/config.example.json review --request runtime/review.example.json
```

O exemplo tem providers desabilitados e identificadores de modelo a substituir; `inspect` funciona sem rede, e os demais retornam impedimento até haver configuração elegível. Copie a configuração para um local privado fora do Git, informe modelos/capacidades/limites verificados, habilite somente os destinos autorizados e disponibilize a credencial pela variável indicada em `api_key_env`. Nenhuma chave aparece no JSON. Não copie transcrições ou dados privados para os exemplos versionados.

`inspect` verifica configuração local/presença de credencial, sem autenticar. `route` ordena candidatos sem chamar modelos. `run` despacha um papel; `review` executa o Council sobre snapshots explícitos. A saída é JSON em stdout, sem logs persistentes automáticos. Proteja-a ao salvar: resultados podem conter código fornecido e texto do modelo.

Exit codes: `0` conclusão/APPROVED; `2` entrada/configuração inválida; `3` BLOCKED; `4` INCONCLUSIVE; `5` CHANGES_REQUESTED; `130` interrupção. `APPROVED` não autoriza merge/deploy.

## Configuração e contratos

| Objeto | Campos e significado |
| --- | --- |
| Provider | `id`, `kind`, `enabled`, `max_parallel`, `data_classes`; opcionais `endpoint`, `api_key_env`, `api_version` |
| Model | `id` local, `provider`, `model` remoto, `capabilities`, `level` (1–3), `context_tokens`, `max_output_tokens` |
| Métricas opcionais | `input_usd_per_million`, `output_usd_per_million`, `success_rate` (0–1), `observed_latency_ms`; as duas últimas exigem `metrics_source` |
| Routing | `policy`: `economy`, `balanced` ou `quality`; `order` contém cada ID local de modelo uma vez para desempate |
| Limits obrigatórios | `max_calls`, `max_parallel`, `timeout_seconds`, `deadline_seconds`, `max_prompt_bytes`, `max_output_tokens` |
| Limits opcionais | `max_estimated_tokens`, `max_estimated_cost_usd`; ausência não é orçamento zero |

Modelos e preços não são embutidos. Níveis são classificação explícita do operador, não benchmark universal. Capacidades suportadas neste executor: `text`, `reasoning`, `code_review`. Pedidos de `shell`, edição ou outras ferramentas são bloqueados mesmo se o modelo tiver essa capacidade em outro ambiente.

Providers adicionais não são exigidos: basta um provider e um modelo suficientes. Provider desabilitado/sem credencial é excluído; referência de modelo a provider não declarado é erro de configuração. Não há descoberta remota automática de quotas, disponibilidade ou catálogo. Limites do serviço são respeitados por falha explícita, não por supor capacidade infinita.

Routing aplica disponibilidade local, capacidades, classe de dados, allowlist de providers, complexidade, contexto e saldo antes da preferência. `economy` prioriza custo conhecido, latência e histórico; `balanced` prioriza o menor nível suficiente, histórico, latência e custo; `quality` prioriza nível, histórico, latência e custo. Dados desconhecidos não viram zero. Desempate final usa `order`. A execução atual atualiza histórico/latência em memória; não existe armazenamento global de telemetria.

As classes `public`, `private` e `restricted` são rótulos definidos pelo operador. O runtime exige correspondência exata com `data_classes` do provider e, se presente, `allowed_providers` da tarefa. Não classifica automaticamente conteúdo nem detecta segredos. Preço, privacidade e capacidades configuradas precisam de proveniência e verificação pelo operador.

## Papéis e tarefas

`planner`, `architect` e `reviewer` produzem análise textual. `implementer`, `tester` e `memory_curator` produzem propostas/handoffs com `host_handoff=true`; aplicação, execução e persistência não ocorreram. Todos possuem lista de ferramentas vazia neste runtime. A [referência portátil](../skills/nexus/references/agents.md) define responsabilidades e uso no host.

Uma tarefa JSON exige `task_id`, `agent` e `prompt`. Opcionais: `complexity` (1–3; padrão 1), `data_class` (padrão `private`), `required_capabilities` e `allowed_providers`. O chamador fornece somente o contexto necessário. O planner descreve dependências; não há executor de DAG nem retomada automática entre processos.

## Review Council

O [exemplo de review](review.example.json) contém um bug sintético. Uma solicitação exige `task_id`, `mode`, `requirements`, `diff`, `changed_files`, `sources`, `risks`, `complexity` e `data_class`; pode restringir `allowed_providers`. Cada arquivo alterado precisa de snapshot em `sources`; para remoções, forneça a versão anterior e identifique-a nos requisitos. Os caminhos são relativos, e o conteúdo é fornecido explicitamente: não há leitura implícita do repositório. O chamador deve garantir que diff, lista de arquivos e snapshots pertencem à revisão correta.

`quality` sempre participa. Riscos explícitos selecionam pilares adicionais: `contract`, `authorization`, `untrusted_input`, `secrets`, `performance`, `concurrency`, `persistence`, `external_io`, `product`, `critical`. Nomes de arquivos também fornecem sinais. Essas heurísticas não substituem avaliar o comportamento; declare riscos que o nome não evidencia.

- `fast`: uma chamada com todos os pilares selecionados.
- `balanced`: uma chamada independente por pilar aplicável.
- `deep`: mesma separação de contextos, com gate completo; `critical` força este modo mesmo se solicitado `fast`.

O mesmo modelo/provider pode realizar todas as revisões. A independência é de chamadas/contextos em relação à execução, sem diversidade de provider garantida. `max_parallel=1` mantém o fluxo sequencial; valores maiores usam threads para I/O independente com limite global e por provider. Há no máximo seis grupos de review e uma escalada compartilhada, sem fila persistente.

Cada resposta deve trazer `task_id`, `artifact_id`, `reviewer_id`, `coverage`, `findings` e `gaps`. O hash cobre requisitos, diff, fontes, arquivos e riscos. O contrato enviado ao modelo exige os campos dos achados definidos na skill. A validação rejeita JSON inválido, IDs divergentes, cobertura omitida, linhas inexistentes, citações que não aparecem no snapshot e achados que se autodeclaram resolvidos. Nenhum texto de resposta é executado.

A consolidação une apenas achados com mesma descrição normalizada, fonte, localização e evidência; mantém todos os relatos/pilares e a maior severidade. Paráfrases possivelmente equivalentes permanecem separadas para avaliação humana. `evidence_reference_verified=true` comprova localização/citação; `semantic_truth_verified=false` deixa explícito que a existência do trecho não prova o bug.

Todos os pilares válidos e sem achados/lacunas: `APPROVED`. Com achados: `CHANGES_REQUESTED`. Todos impedidos antes de concluir: `BLOCKED`. Falha parcial, JSON inválido, timeout ou lacuna: `INCONCLUSIVE`, preservando achados já obtidos. Não existe votação majoritária nem aprovação por ausência de resposta. O resultado é uma avaliação do snapshot, não demonstração de correção nem autorização externa.

## Orçamento, concorrência e recuperação

Um `Engine` corresponde a uma execução completa. Chamadas, reservas e a única escalada são compartilhadas entre seus participantes sob lock. Seleção reavalia saldo antes do dispatch; reservas incompatíveis não são admitidas. O custo dos contextos repetidos entre pilares conta em cada chamada.

Tokens de entrada são estimados pelos bytes UTF-8 do prompt e instruções; não há tokenizer nem garantia formal de janela. A API ainda pode rejeitar contexto. A reserva inclui a saída máxima solicitada e permanece contabilizada após cada dispatch, inclusive falhas/incerteza; uso observado acima da estimativa aumenta a reserva e impede novas chamadas sem saldo. Essa política conservadora pode bloquear antes do saldo real se esgotar.

Chamadas/concorrência/bytes têm controle local; limite de saída é enviado ao serviço. Custos são estimativas pelas tarifas configuradas, sem cobrança medida, descontos, taxas de ferramentas ou garantia de teto financeiro. `usage_priced_cost_usd` multiplica uso informado por tarifa configurada; não é fatura. Sem tarifas e com budget financeiro estimado exigido, não há dispatch. `usage` ausente permanece nulo. Para teto financeiro estrito, use controle verificável no serviço; este runtime não oferece esse recurso. Os limites valem por processo/workflow, não entre CLIs simultâneas ou reinícios.

Escalada só ocorre por truncamento comprovado ou saída estruturada inválida, para um modelo de nível superior, uma vez no workflow e com as mesmas restrições. Não há retry de transporte ou fallback após envio incerto. Credencial/quota/recusa/erro operacional são resultados explícitos. O contexto original é mantido sem incluir a resposta inválida como instrução.

O deadline impede novos dispatches e rejeita conclusões tardias. Timeout de socket e verificações monotônicas por bloco interrompem inatividade e slow-drip; DNS, conexão ou leitura individual podem ultrapassar o prazo. Não é um deadline rígido de processo. Interrupção/fechamento local não garante cancelamento ou ausência de cobrança remota. Não repita automaticamente uma chamada incerta.

## Integrações e evidências

| Integração | Estado |
| --- | --- |
| OpenAI Responses API | Adapter textual implementado a partir da [referência oficial](https://developers.openai.com/api/reference/resources/responses/methods/create); `store=false`; protocolo e falhas testados em loopback |
| Anthropic Messages API | Adapter textual implementado a partir da [referência oficial](https://platform.claude.com/docs/en/api/messages); versão explícita configurável, padrão `2026-10-21`; protocolo e falhas testados em loopback |
| Outros providers/modelos locais | Sem adapter homologado; endpoint alternativo é configuração experimental e exige teste de compatibilidade, autenticação e política de dados |
| CLI Codex/Claude, ferramentas nativas e assinaturas | Nenhuma integração executável nesta CLI; contratos de handoff ao host, sem reutilização automática de login |

HTTPS é exigido fora de loopback; endpoints não aceitam credenciais na URL, query ou fragmento. Redirecionamentos e descoberta automática de proxies são desabilitados. HTTP loopback permite testes e serviços locais explicitamente configurados; isso não garante que um serviço local não encaminhe dados. `store=false` não é promessa sobre toda a retenção do provider.

Nenhum teste autenticado externo foi realizado. Portanto, há dois adapters implementados e testes locais de ambos os protocolos; não há evidência de operação multi-provider em produção, de qualidade de inferência, preços atuais ou latência/throughput real.

## Verificação

```sh
python3 -m unittest discover -s runtime/tests -v
python3 scripts/validate.py
git diff --check
```

A suíte inclui testes HTTP em loopback; ambientes que bloqueiam bind precisam permitir sockets locais. Não há teste ignorado silenciosamente. Veja [cenários e resultados](validation.md).
