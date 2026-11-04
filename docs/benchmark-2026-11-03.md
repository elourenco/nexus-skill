# Benchmark real de quatro condições — 2026-11-03

As **96 execuções reais** foram concluídas e julgadas: 94 aprovadas, duas reprovadas, nenhum inconclusivo. As durações das células somaram 3.078,726 segundos (51,3 minutos); preparação e julgamento ficam fora dessa soma.
A [suíte controlada](../evals/benchmark-suite-v1.json) foi congelada antes das sessões.


## Resultado principal

| Condição | Aceite da rubrica | Mediana: código | Mediana: análise | Tokens totais |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 24/24 | 49,74 s | 7,62 s | 1.267.218 |
| NEXUS | 24/24 | 61,80 s | 14,66 s | 2.659.518 |
| Superpowers | 22/24 | 66,38 s | 14,91 s | 2.779.345 |
| Matt Pocock | 24/24 | 58,85 s | 14,77 s | 2.663.938 |

Cada condição tem 24 execuções (nove de implementação e 15 de análise). Todos os
casos de implementação passaram nos critérios observados. As duas reprovações
foram Superpowers/review-handler/amostras 1 e 2: a resposta tratou rejeição de payload
divergente como requisito/defeito confirmado apesar do contrato não especificado.
Dois revisores em contextos separados concordaram; controles que propuseram essa
política condicionalmente foram aprovados. Os defeitos reais de tenant e concorrência
foram identificados inclusive nos casos reprovados; não se trata de falha de isolamento
em código produzido por essa condição.

A baseline foi mais rápida e consumiu menos neste recorte. NEXUS e Matt tiveram o
mesmo aceite e totais de tokens próximos; a diferença agregada entre ambos foi de
apenas 4.420 tokens (0,17%). NEXUS consumiu 119.827 tokens a menos que Superpowers
(4,31%), sem que estes percentuais demonstrem economia generalizável ou financeira.
Comparado à baseline, NEXUS consumiu 2,10 vezes o total de tokens e não mostrou
ganho de aceite nesta suíte. Os contadores de cache diferem; preço não deriva desses
totais. Não há fundamento aqui para afirmar que NEXUS é universalmente melhor.

O [JSON completo](../evals/results/four-arm-2026-11-03.json) contém todas as células,
proveniência, respostas, comandos, arquivos, verificações e julgamentos.

## Protocolo congelado antes da coleta

- 8 cenários × 4 condições × 3 repetições = 96 execuções, sequenciais.
- CLI Codex 0.166.0-alpha.5.1; modelo solicitado gpt-6.1-sol, esforço medium.
- Modelo efetivo não é informado no JSONL; não será inferido da seleção solicitada.
- Contexto novo por célula, workspace exclusivo, sem delegação nem serviços externos.
- Configuração do usuário ignorada, descoberta de skills/plugins/hooks/memórias
  desabilitada por flags verificadas na CLI instalada. Autenticação existente usada
  sem copiar credenciais. Isso não atesta integralmente instruções internas do host.
- Entrada geral de cada coleção: NEXUS nexus/SKILL.md; Superpowers
  skills/using-superpowers/SKILL.md; Matt skills/engineering/ask-matt/SKILL.md.
- Superpowers22f0b463 e Matt4ae2317d congelados. Arquivos de texto conferidos contra
  hashes Git; no Matt, root AGENTS.md symlink omitido, sem recriar aliases. Imagens
  binárias omitidas. Referências textuais e helpers estão presentes.
- NEXUS é o snapshot da árvore local após a otimização; identidade por inventário
  SHA-256, incluindo mudanças ainda não commitadas.
- Mesma tarefa por cenário em todos os braços; bootstrap autoriza somente leitura
  das instruções selecionadas quando o cenário proíbe comandos operacionais.
- Rubricas congeladas antes da coleta removem preferência por ausência de artefatos
  de workflow e tratam contratos desconhecidos de payload/retry como condicionais.
- API tem verificações adicionais congeladas antes de observar qualquer solução: 
  identidade composta sem colisão, falha concorrente com retry e entradas inválidas.
- Qualidade exige contratos do pedido e evidências; overhead aparece em tempo/tokens,
  sem reprovar um método apenas pelo seu processo interno.

## Escopo das métricas

Latência mede início/fim do processo CLI, incluindo ferramentas, excluindo preparação
e avaliação posterior. Tokens são entrada+saída observadas no turno; cache é parte
da entrada, não uma parcela adicional. Sem subagentes dentro da tarefa, contadores
do executor cobrem os agentes da célula; controlador/revisores externos não entram
no custo da entrega e seu trabalho é declarado separadamente. Não é custo monetário.

Três repetições permitem descrição e inspeção da variabilidade, sem equivalência
estatística, p95 estável ou superioridade geral. Cinco cenários são textuais e três
implementam código; agregados serão acompanhados por essas classes e por cenário.
Este estudo mede instruções em agente único e invocação explícita, não a descoberta
nativa ou o fluxo completo multiagente de cada projeto.

## Proveniência do NEXUS

O [patch do snapshot](../evals/results/four-arm-2026-11-03-nexus.patch), aplicado ao
commit a43420207ada113e7fc38f6260f317e4b292eb74, reconstrói o diretório skills/
avaliado. A reconstrução em árvore temporária foi comparada arquivo por arquivo
com o snapshot congelado; identidade SHA-256
409b0c95cd98b987dffa1cec17c40fea82df19b7806a371ead996f8545c53e3f.
Isso inclui alterações locais anteriores e desta otimização, sem criar commit.

## Revisão dos verificadores

Um teste adicional de falhas concorrentes compartilhadas foi reclassificado como
diagnóstico, sem participar do gate: não garantia que a segunda requisição chegara
à deduplicação antes da liberação da primeira e exigia uma semântica de tentativa
mais forte que o contrato. A revisão foi independente e sem acesso às soluções ou
métricas; nenhum exemplar já executado havia falhado nesse teste. O oracle original,
seu hash e a decisão são preservados. Os testes originais e os oracles de identidade
composta/entrada inválida continuam obrigatórios. Nenhuma tarefa/intervenção mudou.

## Limites de interpretação

A suíte foi criada neste projeto e enfatiza contratos, limites de execução e evidência;
não é um corpus externo independente nem uma amostra de todos os usos das coleções.
O julgamento usa agentes em contextos separados, com rótulos/métricas ocultados,
mas estilo e procedimentos podem revelar o método. Não há cegamento estrito.
Checks determinísticos apoiam os casos de código; Python independente usa os testes
originais, enquanto a cobertura batch adicional foi inspecionada e teve sua execução
observada. O julgamento não equivale a uma prova formal de correção.

As células de inferência foram sequenciais, mas o host e o serviço não tiveram
isolamento físico de carga. Preparação, verificações e julgamento são contabilizados
fora das durações das células e podem ocorrer durante a coleta. Estados de cache
remoto não foram controlados; os contadores observados são preservados separadamente.
Não atribua variação de latência ou preço apenas à quantidade de tokens.

A descoberta externa foi desabilitada por flag experimental aceita pela CLI instalada;
isso não atesta integralmente o prompt interno do host. Modelo solicitado/configurado
é conhecido, mas o serviço não emitiu modelo efetivo; por isso os deltas pareados
estritos do harness ficam null. Totais/medianas permanecem observações descritivas.

## Métricas detalhadas exportadas

96 células completas: 8 cenários × 4 condições × 3 amostras. Protocolo sequencial, contexto novo, agente único e entradas gerais congeladas. Modelo solicitado: `gpt-6.1-sol`, esforço medium; modelo efetivo não observado (`null`).

Qualidade por rubricas manuais independentes, com rótulos e métricas ocultados dos avaliadores; estilo pode revelar o método. Implementação: 3 cenários, 9 entregas por condição. Análise textual: 5 cenários, 15 respostas por condição. A aprovação textual não demonstra correção de código executado.

| Condição | Implementação aprovada | Análise aprovada | Pass/fail/inconclusive | Latência mediana global (ms) | Tokens total | Cache input (subconjunto) | Tokens/aprovado |
|---|---:|---:|---|---:|---:|---:|---:|
| baseline | 9/9 | 15/15 | 24/0/0 | 11,211.5 | 1,267,218 | 867,712 | 52,800.8 |
| nexus | 9/9 | 15/15 | 24/0/0 | 17,247.0 | 2,659,518 | 2,076,160 | 110,813.2 |
| superpowers | 9/9 | 13/15 | 22/2/0 | 20,541.5 | 2,779,345 | 2,140,032 | 126,333.9 |
| matt | 9/9 | 15/15 | 24/0/0 | 22,695.5 | 2,663,938 | 2,112,512 | 110,997.4 |

Tokens totais = input + output; cache não é somado novamente. Tokens/aprovado inclui tentativas falhas e fica desconhecido com cobertura incompleta, resultados inconclusivos ou nenhuma aprovação. Latência global mistura tipos de tarefa e é apenas descritiva.

| Cenário | Condição | Pass/fail/inconclusive | Tokens mediana | Tokens min–max | Latência mediana (ms) | Latência min–max (ms) |
|---|---|---|---:|---|---:|---|
| api-idempotency | baseline | 3/0/0 | 147,794 | 146,880–175,906 | 83,097 | 75,500–101,421 |
| api-idempotency | nexus | 3/0/0 | 239,805 | 234,645–279,762 | 102,070 | 100,197–112,960 |
| api-idempotency | superpowers | 3/0/0 | 174,608 | 172,881–209,264 | 93,255 | 90,959–93,487 |
| api-idempotency | matt | 3/0/0 | 201,280 | 192,819–222,378 | 95,271 | 93,681–106,548 |
| fast-direct | baseline | 3/0/0 | 70,230 | 70,207–70,306 | 13,514 | 12,392–15,007 |
| fast-direct | nexus | 3/0/0 | 98,078 | 98,018–98,217 | 18,011 | 17,030–21,430 |
| fast-direct | superpowers | 3/0/0 | 168,330 | 127,660–171,044 | 25,205 | 23,438–26,337 |
| fast-direct | matt | 3/0/0 | 173,429 | 146,430–173,537 | 29,048 | 29,002–30,471 |
| approved-plan-resume | baseline | 3/0/0 | 101,812 | 100,053–121,786 | 49,740 | 46,412–53,716 |
| approved-plan-resume | nexus | 3/0/0 | 163,298 | 109,562–208,440 | 61,802 | 52,568–68,873 |
| approved-plan-resume | superpowers | 3/0/0 | 223,881 | 206,978–232,901 | 66,384 | 64,463–71,867 |
| approved-plan-resume | matt | 3/0/0 | 166,521 | 163,563–204,448 | 58,854 | 54,309–70,242 |
| uncertain-retry | baseline | 3/0/0 | 17,424 | 17,418–17,436 | 8,823 | 7,840–10,031 |
| uncertain-retry | nexus | 3/0/0 | 81,324 | 62,026–85,829 | 17,008 | 13,804–17,464 |
| uncertain-retry | superpowers | 3/0/0 | 57,953 | 57,873–57,983 | 14,987 | 14,546–16,591 |
| uncertain-retry | matt | 3/0/0 | 60,431 | 60,422–60,436 | 13,910 | 13,359–15,002 |
| stale-validation | baseline | 3/0/0 | 17,332 | 17,289–17,344 | 6,408 | 4,466–7,617 |
| stale-validation | nexus | 3/0/0 | 63,219 | 63,156–63,284 | 14,659 | 14,147–14,694 |
| stale-validation | superpowers | 3/0/0 | 55,898 | 55,865–75,379 | 13,657 | 12,378–17,645 |
| stale-validation | matt | 3/0/0 | 59,856 | 37,853–61,002 | 12,879 | 12,099–14,182 |
| mandatory-check-blocked | baseline | 3/0/0 | 17,320 | 17,320–17,378 | 5,951 | 5,749–7,018 |
| mandatory-check-blocked | nexus | 3/0/0 | 63,163 | 63,157–63,297 | 11,729 | 11,624–12,194 |
| mandatory-check-blocked | superpowers | 3/0/0 | 56,211 | 55,900–75,372 | 13,559 | 12,692–14,090 |
| mandatory-check-blocked | matt | 3/0/0 | 81,780 | 80,694–81,837 | 14,888 | 14,769–16,389 |
| review-handler | baseline | 3/0/0 | 17,978 | 17,903–17,988 | 22,581 | 20,985–22,890 |
| review-handler | nexus | 3/0/0 | 118,426 | 85,884–136,648 | 31,380 | 30,472–35,510 |
| review-handler | superpowers | 1/2/0 | 98,823 | 98,704–119,908 | 31,022 | 29,589–36,204 |
| review-handler | matt | 3/0/0 | 79,054 | 78,900–79,170 | 32,867 | 29,545–35,628 |
| independent-review-unavailable | baseline | 3/0/0 | 17,386 | 17,319–17,409 | 6,505 | 5,033–7,664 |
| independent-review-unavailable | nexus | 3/0/0 | 60,066 | 60,043–60,171 | 13,314 | 11,785–15,772 |
| independent-review-unavailable | superpowers | 3/0/0 | 75,312 | 75,293–75,324 | 14,906 | 14,531–15,651 |
| independent-review-unavailable | matt | 3/0/0 | 59,929 | 59,903–78,266 | 11,354 | 11,083–15,046 |

O JSON público inclui manifesto, fontes/revisões/hashes, política dos oráculos, métricas e cobertura, respostas e rubricas por célula, verificação independente, arquivos antes/depois e comandos/file changes observados. Saída operacional stdout/stderr é preservada, incluindo testes completos do próprio agente; leitura de instruções e configuração privada do host é omitida. Saídas extensas fora de testes podem ser truncadas com hash integral. Stderr diagnóstico do CLI, raciocínio interno e identificadores de threads não são publicados. Cada trace bruto possui hash para vinculação ao original privado.

Não há inferência de superioridade estatística nem custo monetário. Três amostras por célula e o protocolo de agente único limitam a generalização.