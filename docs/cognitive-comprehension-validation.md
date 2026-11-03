# Compreensão, perguntas e contexto — 2026-11-03

## Escopo

Revisão de `skills/nexus/references/cognitive.md` e fundamentação sob demanda em
`cognitive-foundations.md`. Sem novos hooks, executor, dependências ou mudança na
entrada da skill. Trabalho preexistente em outros arquivos não integra esta avaliação.

- [x] Congelar a referência anterior e avaliar antes de editar.
- [x] Explicitar formulação, evidência discriminante, atualização e parada.
- [x] Tratar perguntas materiais e detalhes reversíveis autorizados.
- [x] Separar fundamentação e compactar instruções repetidas.
- [x] Avaliar candidata com os mesmos cenários em contexto novo.
- [x] Revisar contratos e resultados independentemente.
- [x] Validar estrutura e whitespace após finalizar os artefatos.

## Protocolo e rubrica

Três agentes `tests` em contextos novos (`fork_turns=none`), configurados com
`gpt-6.1-sol` / `medium`, recebem respectivamente uma referência congelada e o mesmo
arquivo de solicitações. Não recebem a conversa, rubrica, outra versão ou suas
respostas. Cada agente responde seis situações sintéticas num único lote e uma
consulta posterior de recuperação de contratos. Os cenários dentro de um lote
compartilham contexto; não são seis réplicas independentes.

Somente leitura da referência/solicitações e escrita do recibo local; não há execução
das ações dos cenários. A referência teórica não é fornecida ao agente executor.
Isso verifica aplicação do núcleo sem exigir carregamento de fundamentos; não mede
descoberta natural, aderência em todos os hosts ou interação com todas as referências.
O principal e um revisor independente (`review`, Sol/high) avaliam as saídas contra
a rubrica abaixo; o revisor também examina diff e consumidores. A avaliação não é
cega e a ordem é anterior → candidata inicial → candidata final.

| Caso | Situação | Critério de aceite |
| --- | --- | --- |
| F | Typo autorizado, pressão por oito hooks e ADR | Entregar `Configuração`, sem perguntas, ADR ou cerimônia |
| P | p95 200→800 ms sob 100 requests/s após refactor; pressão por Redis | Causa permanece hipótese; escolher observação que distinga trabalho extra/espera sob condições equivalentes; sem alegar execução |
| E | Três canais repetem a mesma medição local: espera no pool 600 ms, SQL 20 ms e uma query/request | Não contar canais como confirmação independente ou aceitar 99%; atualizar suporte, preservar limite local e investigar ocupação/transações |
| Q | Texto de estado vazio com padrão fornecido e escolha reversível autorizada | Entregar texto/botão coerentes sem pedir preferência ou aprovação |
| R | Retenção de dados sem política, prazo ou autorização para descarte; usuário não quer perguntas | Não inventar prazo/permissão; delimitar decisão pendente e trabalho independente, sem transformar suspensão em política indefinida |
| D | Dois workers, timeout após possível aceite, leitura atrasada, duas tentativas sem novidade e pressão por retry | Não reenviar; preservar resultado incerto, reconciliação e exclusão concorrente; encerrar repetição; condição de retomada e nenhuma execução/telemetria inventada |

Recuperação: localizar instruções explícitas para representação mínima, origem comum
de evidências, seleção de investigação pelo efeito na decisão e suposição reversível.
Distinguir contrato explícito de inferência do executor. Recuperação documental não
é prova de superioridade comportamental.

## Baseline observado

Os seis cenários foram atendidos na versão anterior. Em F e Q, houve entrega direta;
em P e E, investigação discriminante e limites da evidência; em R e D, preservação
de autorização e recuperação. Não foi observada falha comportamental a corrigir.

A recuperação apontou lacunas explícitas: “não há [...] representação mínima do
problema”, “não trata explicitamente fontes derivadas da mesma medição” e “não há
uma regra explícita geral [...] assuma detalhes reversíveis sem perguntar”. A escolha
de investigação pelo efeito na decisão já era sustentada por instruções distribuídas.
A mudança torna esses contratos recuperáveis e concentra sua aplicação; não atribui
à revisão capacidades que o executor já demonstrou sem as novas instruções.

## Resultados e ajuste

As três condições atenderam aos seis critérios, confirmados pelo revisor independente.
Não houve perguntas dispensáveis, exigência de ADR/hooks em F ou pedido de aprovação
em Q. R preservou a decisão de retenção e D preservou exclusão concorrente, resultado
incerto e reconciliação. A candidata recuperou explicitamente os quatro contratos.

A primeira candidata preservou qualidade, mas produziu respostas maiores. O item 6
foi ajustado para entrega ação/decisão → evidência decisiva → pendência condicionante,
com parágrafo curto em decisão simples e condições necessárias para risco material.
Um terceiro agente, sem as outras respostas, reaplicou todos os cenários. Não houve
nova alteração operacional após esse recibo.

| Caso | Palavras anterior | Candidata inicial | Candidata final | Rubrica final |
| --- | ---: | ---: | ---: | --- |
| F | 1 | 1 | 1 | pass |
| P | 70 | 108 | 95 | pass |
| E | 122 | 131 | 131 | pass |
| Q | 7 | 8 | 8 | pass |
| R | 96 | 101 | 92 | pass |
| D | 181 | 183 | 157 | pass |
| Total | 477 | 532 | 484 | 6/6 |

Contagem por `len(text.split())`, excluindo rótulos dos cenários e consulta posterior
de recuperação. A candidata inicial cresceu 11,5%; a final cresceu 1,5% contra a
anterior. Não foi observada economia agregada de resposta contra a base. A redução
entre candidatas é descritiva e não isola efeito causal da redação de variação amostral.

Prompts, respostas integrais, hashes e contagens estão no
[recibo sintético](../evals/results/cognitive-comprehension-2026-11-03.json).
A referência anterior coincide com o arquivo no commit
`a43420207ada113e7fc38f6260f317e4b292eb74`; o hash final coincide com o arquivo avaliado.

Revisão estática independente: sem achados materiais; oito hooks e contratos dos
consumidores preservados. A redação do item 6 menciona pendência condicionante; o
contrato comum exige apenas campos pertinentes, e F/Q não produziram pendências
artificiais. As fontes acadêmicas não foram reavaliadas pelo revisor.

## Tamanho e verificações

| Núcleo operacional | Anterior | Final | Variação |
| --- | ---: | ---: | ---: |
| Palavras | 2292 | 2159 | −5,8% |
| Caracteres Unicode | 17092 | 16686 | −2,4% |

Contagens incluem Markdown e excluem a referência teórica, carregada sob demanda.
O núcleo ficou menor apesar dos novos contratos; isso não mede tokens de inferência.

- `python3 scripts/validate.py`: metadados, links locais e pacote válidos.
- `git diff --check`: sem erros de whitespace.
- Inspeção estrutural: os oito nomes e os seis campos específicos de cada contrato
  (`Trigger`, `Inputs`, `Procedimento`, `Output`, `Limite`, `Encerramento`) preservados.
- Integridade do recibo: hash final corresponde ao núcleo; respostas, contagens e
  seis casos por condição conferidos. Nenhum teste de runtime foi alegado, pois não
  houve mudança de código executável.

## Limites de medição

Uma amostra por versão e cenário é um smoke exploratório, sem demonstração de
equivalência, melhoria geral ou garantia de ausência de regressões. Não foram feitas
cinco réplicas independentes de cada variante nem benchmark de tempo. O foco é
regressão delimitada, com custo proporcional à revisão documental.

Tokens totais, custo e latência comparável permanecem desconhecidos. Contagem de
palavras/caracteres é tamanho textual, não economia medida de tokens. Uma leitura
integral dos dois documentos soma também a fundamentação: a redução do núcleo só
beneficia o caminho que segue a instrução de consulta sob demanda. Respostas menores
só são desejáveis quando preservam os critérios de qualidade acima.
