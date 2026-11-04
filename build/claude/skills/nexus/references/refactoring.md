# Refatoração com preservação de comportamento

Use para planejar, executar ou revisar reestruturação que afete responsabilidades,
interfaces, dependências ou efeitos. Alteração mecânica local com equivalência clara
usa o fluxo curto de Build e checks pertinentes, sem carregar todo este guia.
Preserve a arquitetura/plano aprovado; consulte [design](architecture-design.md)
somente quando houver decisão estrutural ainda não resolvida. [Fontes](design-sources.md)
são registro de manutenção e não dependências externas.

<a id="contrato"></a>

## Fixar o que deve permanecer

Refatoração preserva o comportamento observável acordado: resultados, erros,
efeitos, ordem, mutação de entradas, identidade e compatibilidade. Inclua os
contratos operacionais afetados: transações, retries, cancelamento e limites de
latência/recursos. Ganho de desempenho precisa de medição; extração de função não
prova melhoria nem equivalência por si só.

Separar uma correção, mudança de API ou paralelização da transformação estrutural
torna seus aceites verificáveis. Se a mudança de comportamento já estiver
autorizada, execute-a com critérios próprios; caso contrário, preserve o contrato
e delimite a decisão pendente. Caracterização descreve o legado, não legitima
vulnerabilidade ou transforma comportamento desconhecido em requisito desejável.

## Sequência de aplicação

1. Localize o problema e os consumidores reais. Defina a menor região afetada e o
   contrato a preservar; reutilize testes, ADRs e decisões válidas.
2. Se o comportamento for incerto ou não houver cobertura relevante, caracterize
   saídas, fronteiras, erros e efeitos antes de mover código. Expectativas vêm do
   contrato e da observação, não de uma cópia do novo algoritmo. Registre checks
   propostos separadamente dos executados.
3. Escolha a transformação pelo problema, idioma da linguagem e custo de mudança.
   Ferramentas semânticas de rename/move ajudam quando disponíveis; confira callers,
   exports, uso dinâmico, serialização e configurações que elas não alcançam.
4. Aplique incrementos revisáveis e verificáveis, mantendo o sistema utilizável.
   Preserve pontos de caracterização/regressão exigidos; não espalhe limpeza
   estilística por arquivos alheios. Para mudanças entre versões, detalhe a
   compatibilidade no [plano](plan.md), sem chamar migração incompatível de refatoração.
5. Execute checks sobre a versão final conforme [Policies](policies.md#policy-testing).
   Confira contrato e efeitos, não só compilação. Evidência anterior invalidada
   pela mudança permanece histórica. Teste bloqueado não conta como aprovado.

<a id="padroes"></a>

## Padrões pelo problema

| Problema | Transformação candidata | Preservação a conferir |
| --- | --- | --- |
| Conceito sem nome ou função mistura etapas distintas | Extract Function / Split Phase | Ordem e quantidade de avaliações, efeitos, escopo de erro e dados necessários em cada fase. |
| Fragmentação, wrappers ou classe sem responsabilidade própria | Inline Function / Inline Class / Remove Middle Man | Contratos públicos, isolamento, autorização e ciclo de vida que a fronteira possa proteger. |
| Regra distante do estado/invariante que governa | Move Function / Move Field | Ownership, callers, visibilidade, serialização e propagação do mesmo contexto transacional. |
| Condicionais dificultam entender casos | Decompose Conditional / Guard Clauses | Precedência, short-circuit, efeitos, defaults válidos e distinção entre ausência, zero, false e vazio. |
| Parâmetros recorrentes têm significado conjunto | Introduce Parameter Object | Coesão real, compatibilidade de chamadas, identidade e mutabilidade; evitar saco de parâmetros genérico. |
| Herança impede variação independente | Replace Superclass with Delegate | Contrato público, despacho, inicialização, identidade e comportamento esperado pelos consumidores. |
| Consulta mistura cálculo com mutação | Separate Query from Modifier | Não quebrar operação que precisa ser atômica nem duplicar I/O; uma separação aparente pode introduzir TOCTOU. |
| Nome oculta intenção ou código parece sem uso | Rename / Remove Dead Code | Callers reais, reflexão, plugins, rotas, exports públicos e flags antes de remover. |

Padrões são candidatos, não sequência obrigatória. Extração e inline são decisões
opostas válidas; escolha a que concentra conhecimento e reduz custo para callers.
Tamanho de arquivo ou método isoladamente não demonstra necessidade de mudança.

<a id="efeitos"></a>

## Concorrência, efeitos e performance

Ao mover código com I/O ou estado, confira nas versões anterior e proposta:

- Escopo/isolamento da transação, duração dos locks e compartilhamento do mesmo
  contexto entre operações. Mover uma chamada pode liberar ou prolongar um lock.
- Ordem de início/conclusão, visibilidade dos efeitos e condição de parada em erro.
  Trocar awaits sequenciais por `Promise.all` inicia trabalho adicional e não cancela
  irmãos automaticamente quando uma promessa rejeita. Ordem do array de resultados
  não é ordem dos efeitos; isso pode ser mudança de comportamento.
- Propagação de cancelamento, operações já iniciadas e liberação de recursos.
  Cancelar não desfaz um efeito concluído; timeout pode deixar resultado incerto.
- Ownership dos retries, identidade/deduplicação e recuperação após crash. Mover
  retry para outra camada pode multiplicar tentativas ou repetir parte já concluída.
- Chamadas de rede/queries, N+1, cópias/alocações, caches e paralelismo. Limite
  recursos e backpressure conforme a dependência; compare carga e ambiente
  equivalentes quando houver critério de desempenho.

Exemplo: em um envio sequencial que para no primeiro erro, o contrato impede iniciar
itens posteriores. Iniciar todos em paralelo e devolver resultados na ordem original
viola esse contrato. Um cenário discriminante registra quais envios começaram antes
e depois da falha, incluindo sinal já cancelado e cancelamento durante um envio.

Testes de regra com fake continuam úteis. Se a mudança afetar atomicidade, leases,
constraints ou efeitos distribuídos, teste os interleavings e recuperação no runtime
responsável; testes sequenciais em memória não comprovam essas garantias.

## Entrega

Informe a transformação, contrato preservado ou mudança explicitamente autorizada,
verificações observadas e lacunas. No review, relacione o risco a uma execução
concreta; na implementação, siga [Build](build.md) até o aceite do escopo autorizado.
Não exija novo brainstorming, artefato ou aprovação só por usar uma refatoração.
