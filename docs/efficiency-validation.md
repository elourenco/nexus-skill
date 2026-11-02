# Fluxo proporcional e avaliação de eficiência

## Escopo

O perfil FAST/BALANCED/DEEP determina risco e validação. Acompanhamento direto ou
rastreado determina a necessidade de registros; não cria novos estados, schemas
ou enums no executor. Uso direto não dispensa gates do host/projeto. A CLI opt-in
continua exigindo discovery/spec/plan em BALANCED e os contratos adicionais de DEEP.
Engine, runtime textual, cache, gerações, recibos e políticas de conclusão não foram alterados.

O incremento também concentra a operação da CLI em workflow-state.md, preserva
headings de referência no workflow, retoma planos aprovados sem recriá-los e agrupa
edições/revisões por incremento. Reutilizar evidência exige inputs, revisão,
configuração, ambiente e, quando aplicáveis, run/geração válidos. Alterações
invalidam conclusões afetadas; complete/deliver continuam revalidando suas fontes.

## Cenários executáveis e evidências

A [suíte de oito cenários](../evals/efficiency-suite.json) cobre FAST direto e
rastreado, BALANCED direto, retomada de plano aprovado, mudança pequena crítica,
evidência obsoleta, retry de efeito incerto e check obrigatório bloqueado.
As rubricas exigem resultados observados e preservação dos gates; menor consumo
não altera o veredito de qualidade. Cenário faltante ou expectativa de perfil/
persistência não observada permanece inconclusivo.

[test_efficiency_scenarios.py](../tests/test_efficiency_scenarios.py) executa:

- Isolamento dos workspaces preparados para todas as condições.
- Red/green real das duas fixtures FAST: regressões falham antes de strip e
  passam depois, sem artefatos adicionais. Esta receita determinística verifica
  a fixture; não prova que um agente seguirá as instruções.
- Retomada de um executor BALANCED por novo coordenador com os mesmos contratos:
  hashes e registros aprovados preservados, conclusão sem evidência rejeitada,
  entrega após evidências declaradas sintéticas. Este teste exercita o store,
  não representa implementação real por um LLM.

[test_evaluations.py](../tests/test_evaluations.py) cobre snapshots por versão,
ordem alternada, métricas desconhecidas/heterogêneas, expectativas, comparação
pareada e compatibilidade com manifestos anteriores. O teste de rubrica incompleta
agora consulta a célula NEXUS efetivamente registrada. A sensibilidade foi
verificada substituindo em memória a regra de rubrica completa: o teste falhou
na célula correta e voltou a passar com a implementação preservada.

Comparações exigem contexto comum, configuração, esforço e executor conhecidos,
além de modelo e escopos de medição compatíveis. A identidade do snapshot NEXUS
é a intervenção e pode diferir. Essas identidades continuam declarações com
proveniência; não substituem conferência dos rastros nem atestam execução.

## Validação local

Comandos do incremento:

```sh
python3 -B -m unittest discover -s tests
python3 -B -m unittest discover -s runtime/tests
python3 scripts/validate.py
python3 skills/nexus/scripts/hook_engine.py validate
git diff --check
```

Os testes HTTP do runtime usam fixtures em 127.0.0.1. A primeira execução no
sandbox foi impedida ao abrir sockets; a execução autorizada fora dele passou.
Nenhum teste dessa suíte usa um provedor externo.

Resultado local em 2026-11-02: **187 testes do pacote e 56 testes do runtime
passaram**. A revisão independente do diff não encontrou bloqueantes remanescentes;
o problema de comparabilidade de contexto foi reproduzido e corrigido antes do
fechamento. Isso não equivale a CI remota ou aceitação em projetos consumidores.

## Comparação no host

A comparação usa a mesma suíte e configuração, duas versões congeladas das skills,
contextos novos e workspaces exclusivos, com ordem alternada entre cenários.
Os resultados da execução são registrados separadamente da validação local.
Uma amostra por condição é smoke: não demonstra equivalência estatística,
melhoria causal ou economia generalizável. Tokens observados não são custo
monetário; entrada em cache deve ser interpretada separadamente e não somada
novamente ao total de entrada.

### Resultado observado em 2026-11-02

O [recibo sanitizado](../evals/results/efficiency-2026-11-02.json) inclui 16 execuções
reais, hashes das duas instalações, ordem, respostas, comandos, arquivos finais,
julgamentos independentes e contadores fornecidos pelo CLI. A versão anterior é
a árvore de skills de `307cee6e9e019248b56885468f11efce9020ec13`; a candidata é
identificada pelo digest `a11955a0151c413bdebefce3bb7e4377ae92a9231597a0ef3f87b86d4374ccc7`
e pelos hashes de cada arquivo no recibo.

| Cenário | Tempo anterior / candidata (s) | Tokens anterior / candidata | Ferramentas anterior / candidata |
| --- | --- | --- | --- |
| FAST direto | 19,99 / 23,49 | 130510 / 133188 | 6 / 9 |
| FAST rastreado | 29,66 / 32,97 | 139681 / 165672 | 8 / 10 |
| BALANCED direto | 37,99 / 45,44 | 145559 / 137085 | 11 / 6 |
| Retomada de plano aprovado | 47,88 / 40,54 | 239073 / 192671 | 9 / 12 |
| Mudança pequena crítica | 33,88 / 31,82 | 153414 / 83703 | 7 / 6 |
| Evidência obsoleta | 18,13 / 18,78 | 110061 / 40031 | 2 / 0 |
| Retry incerto | 22,07 / 22,35 | 155574 / 83902 | 8 / 7 |
| Check obrigatório bloqueado | 11,70 / 12,26 | 37305 / 58137 | 1 / 2 |

São contagens descritivas, não estimativas de efeito. No conjunto observado,
entrada+saída somaram 1111177 tokens na anterior e 894389 na candidata; os tempos
somaram 221,289 s e 227,644 s. Não houve melhoria consistente de latência, nem
redução em todos os cenários. Não extrapolar os totais para tarefas, custos ou
providers diferentes. Tempo cobre início/fim do CLI, incluindo ferramentas, mas
exclui preparação e revisão independente posterior. Ferramentas conta itens
visíveis de comando/edição, não requisições internas ao modelo ou comandos
individuais dentro de um shell.

O CLI foi configurado explicitamente com `gpt-6.1-sol`, esforço `medium`, mesmo
ambiente, configuração isolada e sem delegação. Seu JSONL não informou o modelo
efetivo do serviço: `model` permanece `null`, a seleção solicitada fica em campo
separado e o comparador conservador não emite deltas pareados. Os tokens são
contadores observados do turno, incluindo contexto repetido/cache, não o tamanho
estático da skill. Não foi possível contar leituras de referência ou chamadas
internas de inferência com confiança; esses campos permanecem `null`.

Qualidade: candidata **8 pass**; anterior **6 pass, 1 fail, 1 inconclusive**. A falha
anterior executou comandos de leitura quando o cenário dizia literalmente
“No commands or edits are authorized”. A célula inconclusiva atualizou corretamente
a TASK, mas declarou persistência “direta/documental”: o campo ambíguo ficou null.
As oito implementações passaram também por assertions de contrato independentes,
após o turno, sem alterar os arquivos avaliados.

O julgamento inicial de dois casos “No execution” foi adjudicado por segundo
revisor: apenas ler referências solicitadas pelo envelope não viola a rubrica
que veda implementação, testes, retry, fabricação e novos artefatos. O recibo
preserva o julgamento inicial, a interpretação excessiva sugerida pelo controlador
e a decisão final fundamentada. Isso difere da proibição explícita de comandos.
Rótulos de versão foram ocultos, mas a primeira leitura do revisor expôs métricas
e trechos de referências incidentalmente; não houve cegamento estrito.

A primeira inicialização do CLI foi bloqueada antes de inferência. Após autorização
explícita do usuário, as 16 células executaram sequencialmente em contextos novos,
sem copiar credenciais ou modificar instalações globais. Esse smoke usa invocação
explícita de snapshots e um agente por tarefa: não mede descoberta implícita,
delegação ou integração nativa de hooks. Nenhuma superioridade estatística é alegada.
