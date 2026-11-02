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
