# Avaliação comportamental reproduzível

O empacotamento e a qualidade das respostas têm evidências separadas. `scripts/verify_hosts.py` verifica descoberta nativa das seis entradas em perfis temporários. `scripts/evaluate.py` prepara contextos sintéticos, recebe observações de execuções reais e agrega julgamentos manuais. Nenhum deles transforma palavras-chave em qualidade, executa inferência automaticamente ou afirma melhoria estatística.

## Suíte versionada

`evals/suite.json` define onze cenários e rubricas explícitas: uma chamada de cada entrada (`nexus`, brainstorming, plan, build, debug e review) e pressões de fronteira (análise apenas, intenção do usuário sobrepondo a entrada, timeout com operação remota aceita, evidência obsoleta e núcleo ausente). `evals/fixtures/python-name/` contém o único workspace com alteração solicitada e testes reais. São dados sintéticos, sem projetos consumidores.

Cada cenário tem duas condições: `baseline`, sem NEXUS disponível, e `nexus`, com a mesma tarefa e a invocação da entrada. O campo `baseline_prompt` remove nomes de skills que poderiam disparar a condição experimental. Todos os demais parâmetros do host devem permanecer equivalentes. A comparação mede essa intervenção completa; não isola o efeito das descrições de descoberta. Não use uma sessão que já carregou NEXUS como baseline.

## Preparar e executar

```sh
python3 -B scripts/evaluate.py prepare --output /tmp/nexus-eval-v1 --run-id local-v1 --samples 2
```

O comando recusa sobrescrever o diretório. Congela a suíte, hashes dos arquivos da skill e um snapshot das skills. Cada célula tem `contexts/SCENARIO/VARIANT/SAMPLE/prompt.txt` e `workspace/` próprios. Não compartilhe o workspace entre amostras. Para `missing-core`, exponha somente `missing-core-snapshot/`, que não contém o núcleo. Nas demais células NEXUS, exponha `skill-snapshot/`. Não exponha a rubrica ou o diretório das outras condições ao agente avaliado.

Execute cada prompt em uma sessão realmente nova do host autorizado. Registre host e versão, modelo observado (ou `null`), configuração, contexto disponibilizado e qualquer diferença material entre condições. Não use resume, conversa herdada, memória compartilhada, saídas das outras amostras ou o agente implementador como se fosse uma réplica independente. Alterne a ordem das condições entre repetições. A CLI não cria agentes nem exige provider/modelo específico; autenticação, permissões e instalação continuam responsabilidade do host. Não copie credenciais para perfis temporários.

Observe a resposta final e o rastro de ferramentas. Para cada critério, um revisor identifica evidência concreta e atribui `pass`, `fail` ou `inconclusive`. Preferencialmente, o revisor não conhece a condição antes de julgar a resposta. Uma declaração do modelo de que executou testes não comprova execução: use o resultado observado da ferramenta. Sem acesso ao rastro, chamadas, leituras de referências e comandos permanecem `null`. Uma lista vazia significa zero observado, não desconhecido. Latência é tempo observado da execução completa em milissegundos; não é estimativa de tokens ou custo.

Exemplo do formato de recibo (substitua pelos dados observados, não registre este exemplo como execução):

```json
{
  "host": "host e versão observados",
  "model": null,
  "fresh_context": true,
  "response": "Resposta sintética efetivamente observada",
  "commands": null,
  "calls": null,
  "reference_reads": null,
  "latency_ms": null,
  "reviewer": "identificador do revisor",
  "grades": {
    "scope": {"verdict": "pass", "evidence": "Trecho concreto ou observação do rastro"},
    "evidence": {"verdict": "inconclusive", "evidence": "Rastro indisponível"}
  }
}
```

Os identificadores em `grades` devem ser os da rubrica do cenário; o exemplo corresponde a `core-question`. O arquivo pode incluir campos adicionais de proveniência (versão do host, parâmetros, identificador de sessão, justificativa de isolamento e limitações), sem segredos.

```sh
python3 -B scripts/evaluate.py record --run /tmp/nexus-eval-v1 --scenario core-question --variant baseline --sample 1 --observation /tmp/observation.json
python3 -B scripts/evaluate.py report --run /tmp/nexus-eval-v1
```

Recibos são publicados com criação exclusiva, sem sobrescrita; correções exigem novo run e proveniência explicada. Para recortes explícitos, `prepare --suite /caminho/subset.json` aceita uma suíte no mesmo schema, sem alterar a padrão.

A agregação valida identidade da célula, rubricas, campos observados e integridade do manifesto/snapshot. Esses hashes detectam alterações acidentais, não oferecem atestação contra um autor que reescreve ambos os arquivos. `fresh_context` é declaração verificável pelo revisor, não isolamento imposto pela ferramenta.

Uma célula só passa com todos os critérios aprovados. Critério reprovado mantém `fail` mesmo com amostras faltantes. Ausência, critério não julgado ou observação insuficiente mantém `inconclusive`. O relatório apresenta contagens por condição, quantidade de latências conhecidas e média somente dessas observações; não imputa zero aos desconhecidos. A ausência de diferença em poucas amostras não demonstra equivalência. `quality_improvement` permanece `null`; avaliar efeito exige amostragem e análise apropriadas fora deste harness.

## Comparação de versões previous/candidate

O modo anterior `baseline/nexus` e a API `prepare(output, run_id, samples, suite_path=None)` continuam aceitos. Para comparar duas versões do pacote, use o argumento opcional `previous_skills` na API ou:

```sh
python3 -B scripts/evaluate.py prepare --output /tmp/nexus-efficiency --run-id efficiency-v1 --samples 2 --suite evals/efficiency-suite.json --previous-skills /tmp/previous-version/skills
```

O diretório fornecido deve conter `nexus/SKILL.md`. A candidata vem de `skills/` do checkout que executa o harness. As condições são `previous` e `candidate`; ambas recebem o mesmo prompt, incluindo a mesma invocação da entrada. O manifesto registra `conditions[VARIANT]` com `snapshot`, `missing_core_snapshot`, `files_sha256` e `identity_sha256`. As cópias `previous-skill-snapshot/` e `candidate-skill-snapshot/` são as fontes congeladas para execução. Para o cenário de núcleo ausente, use o `missing_core_snapshot` da condição correspondente. Alterar arquivos ou inventário de qualquer snapshot invalida o run. A imutabilidade é verificada por hashes; a ferramenta não instala permissões de filesystem nem impede reescrita coordenada do manifesto e de seu checksum.

`execution_order` registra a sequência planejada de células `{scenario, variant, sample}`. A primeira condição alterna por cenário/amostra, reduzindo confundimento sistemático de ordem. O operador deve seguir essa sequência e registrar desvios como proveniência; o harness não executa as sessões nem comprova a ordem efetiva. Cada célula tem seu próprio workspace. A preparação valida os snapshots antes de retornar; `record` e `report` validam novamente ambos.

Os campos opcionais `expected_profile` (`FAST`, `BALANCED`, `DEEP`) e `expected_persistence` (`direct`, `tracked`) podem ser declarados por cenário. A observação usa `profile` e `persistence` com esses mesmos enums ou `null`. Divergência explícita produz `fail`; ausência em cenário com expectativa produz `inconclusive`, preservando qualquer falha já observada na rubrica. Sem expectativa, esses campos são apenas descritivos. Classificação observada e rubrica continuam independentes das métricas de eficiência.

Observações antigas continuam válidas. Campos novos são opcionais e dados ausentes permanecem desconhecidos. Exemplo de medições adicionais, somente quando o rastro permite observá-las:

```json
{
  "profile": "FAST",
  "persistence": "direct",
  "tokens": {"total": 1200, "source": "host usage export", "scope": "all-agents", "unit": "tokens"},
  "tool_calls": {"total": 4, "source": "complete tool trace", "scope": "all-agents", "unit": "calls"},
  "llm_calls": null
}
```

`tokens` exige total inteiro não negativo efetivamente medido, origem não vazia, unidade `tokens` e escopo `all-agents`: inclui o principal e todos os agentes da execução. Se o host expõe apenas parte da execução, registre `null`; não derive tokens por texto, latência ou custo. `tool_calls` e `llm_calls` exigem total inteiro não negativo, origem, escopo explícito e unidade `calls`. São categorias separadas; o legado `calls` não identifica categoria/escopo e nunca entra em comparação pareada. `reference_reads` continua uma lista observada ou `null`; sua métrica é a quantidade de itens, sem inferir leituras ausentes. Booleanos, negativos, frações em contagens, NaN e unidades incorretas são rejeitados. Proveniência adicional continua permitida. Não há estimativa de custo.

`metrics_by_scenario_variant[SCENARIO][VARIANT][METRIC]` informa `observed`, `expected`, `mean`, unidade e assinaturas das medições estruturadas. Assinaturas distintas de origem/escopo/unidade não recebem média combinada. `paired_by_scenario[SCENARIO][METRIC]` informa pares comparáveis/esperados e `mean_delta` (segunda condição menos primeira). Um par requer a mesma amostra, host e modelo conhecidos equivalentes e `comparison_context` explícito nas duas observações. Esse objeto contém strings não vazias `executor`, `configuration`, `input_context`, `effort` e `evidence`. Os quatro primeiros identificam o executor/versão efetivos, a configuração controlada, o contexto comum inicial (prompt, fixture e instruções comuns) e o esforço observado; `evidence` aponta para o rastro ou artefato que permite ao revisor verificar essas identidades. Use hashes ou identificadores versionados vinculados à evidência real. Não inclua a identidade do snapshot das skills no contexto comum: essa diferença é a intervenção medida. Ausência de dados exige `comparison_context: null`, inclusive esforço não observável; dois valores desconhecidos não estabelecem equivalência. Os objetos precisam ser iguais, exceto a localização `evidence`, que pode diferir por execução. Divergências adicionais nos campos legados `configuration`, `effort`, `context` ou `executor` também vetam o pareamento. Sem comparabilidade explícita, métricas brutas permanecem disponíveis e o delta fica `null`. Métricas estruturadas também exigem mesma origem/escopo/unidade; ausência de uma medição exclui apenas aquele par. O harness valida a declaração e a igualdade das identidades; não verifica automaticamente a veracidade dos artefatos apontados por `evidence`. O revisor continua responsável por conferir o rastro e registrar diferenças materiais; igualdade dos campos não comprova equivalência física do ambiente. Assinaturas distintas entre pares mantêm a cobertura, mas não recebem delta médio combinado. A cobertura permanece explícita por cenário, sem média global de diferenças.

Os campos legados `latency_ms_mean` e `latency_observations` permanecem para consumidores existentes; `legacy_latency_scope` explicita que misturam todas as células observadas e não representam comparação entre versões. Use as métricas por cenário/condição e os pares para analisar eficiência. Nenhuma métrica aprova qualidade: rubricas e expectativas determinam os vereditos; `quality_improvement` permanece `null`. Testes sintéticos do harness e uma execução real parcial não comprovam ganho geral.

## Descoberta nos hosts

```sh
python3 -B scripts/verify_hosts.py --codex /caminho/do/codex --claude /caminho/do/claude --output /tmp/discovery.json
```

O script instala o catálogo local em `CODEX_HOME` e `CLAUDE_CONFIG_DIR` temporários, consulta `skills/list` do app-server Codex e o inventário nativo `claude plugin details`, preserva os comandos/saídas e remove os perfis ao terminar. Não cria thread de inferência. Falha operacional ou formato de inventário desconhecido fica inconclusivo. A versão do pacote é lida do manifesto.

A leitura do protocolo usa bytes não bloqueantes, deadline e limite de tamanho mesmo quando o host não termina uma linha. O encerramento tem espera limitada e fallback de terminate para kill. Entradas Codex precisam estar habilitadas; no Claude, o inventário é combinado com o registro de instalação habilitada. JSON/schema inválido mantém a descoberta inconclusiva. O arquivo de saída só é criado após a coleta produzir um resultado.

Em 2026-11-02, Codex CLI `0.166.0-alpha.5.1` e Claude Code `2.1.308` descobriram as seis entradas do pacote `0.3.0`, habilitado em consumidores separados. O inventário Claude mostrou zero agents/hooks/MCP/LSP. Recibo: [host-discovery-2026-11-02.json](../evals/results/host-discovery-2026-11-02.json). O wrapper `codex` do PATH estava quebrado (`ENOENT`); foi usado o executável já instalado dentro do aplicativo ChatGPT. Esse resultado comprova instalação/descoberta, não aderência conversacional ou seleção implícita.

## Validação do harness

```sh
python3 -B -m unittest discover -s tests -p test_evaluations.py -v
python3 -B -m unittest discover -s tests -p test_verify_hosts.py -v
python3 scripts/validate.py
```

Os testes exercitam amostras ausentes, dados desconhecidos, duplicação, células inválidas, evidência reprovada, métricas inválidas e manifesto adulterado. Testes do harness não são resultados comportamentais de agentes. A execução da matriz completa exige sessões novas reais e revisão dos respectivos rastros; resultados parciais devem manter essa limitação explícita.

## Smoke registrado

O [recorte analysis-only](../evals/results/analysis-only-2026-11-02.json) registra
cinco amostras por condição e avaliação manual independente do conteúdo. Ambas
passaram; não demonstra melhoria. Consulte os [limites e resultados](quality-improvements-validation.md)
antes de interpretar o recorte como evidência de aderência geral.
