# Design de módulos, sistemas e soluções

Use quando houver decisão sobre interfaces, dependências, fronteiras de dados,
integração ou deploy. Leia a seção pertinente; uma edição mecânica não exige esta
referência. Preserve decisões aprovadas até que evidência material as contradiga.
Este conteúdo complementa [Policies](policies.md#policy-engineering), sem criar
fase, agente, diagrama ou ADR obrigatório. As [fontes](design-sources.md) são
proveniência de manutenção, não leituras necessárias à execução.

<a id="diagnostico"></a>

## Diagnosticar antes de redesenhar

Delimite o fluxo pedido e siga uma chamada real: entrada → regra → estado/I/O →
consumidor. Leia callers, implementação e testes; identifique quem escreve o estado,
quem conhece decisões internas e onde uma mudança precisa ser repetida. Histórico
de alterações ajuda a priorizar investigação quando o escopo ainda é amplo.

Desenhe só as relações necessárias à decisão. Diretórios, nomes de classes e
dependências declaradas não comprovam arquitetura em runtime. Para ciclo, mostre
o caminho de imports/chamadas e a consequência; para acoplamento, mostre uma mudança
que se propaga ou uma falha que atravessa a fronteira. Preferência estética é uma
sugestão, não um defeito. Se só houver hipótese, indique a verificação discriminante.

<a id="modulos"></a>

## Módulos e interfaces

Uma boa interface concentra comportamento coeso e esconde decisões que o consumidor
não precisa conhecer. Seu contrato inclui entradas/saídas, invariantes, ownership,
erros, efeitos, ordem, cancelamento e custos relevantes; poucas assinaturas não
compensam I/O oculto ou pré-condições espalhadas pelos callers.

| Sinal observado | Decisão proporcional |
| --- | --- |
| Vários callers repetem a mesma política ou tradução | Concentre essa decisão junto de seu responsável; mantenha conceitos com semânticas distintas separados. |
| Cadeia de wrappers apenas repassa parâmetros/resultados | Simule a remoção: a complexidade desaparece ou volta para os callers? Consolide quando eliminar só indireção; preserve fronteiras que protegem contrato, autorização, ciclo de vida ou isolamento. |
| Integração volátil espalha tipos, erros ou retries do fornecedor | Defina a menor capacidade exigida pelo domínio e traduza no adapter. Um único fornecedor pode justificar a fronteira; outro fornecedor hipotético não é requisito nem justificativa suficiente. |
| Mudança exige conhecer detalhes de muitos módulos | Reavalie localização da regra e direção das dependências antes de adicionar camadas. Reduzir superfície pública não significa concentrar responsabilidades sem relação. |
| Regra só pode ser testada subindo toda a infraestrutura | Isole decisão determinística ou injete o efeito variável quando útil; preserve testes de contrato/integração das garantias reais. |

Reutilize termos do domínio e idioms da linguagem. Interface é um contrato, não
necessariamente uma classe, um arquivo ou a palavra-chave `interface`. Passe
capacidades externas explicitamente; valores locais puros podem ser construídos
diretamente. Não exija container de DI ou uma interface por classe.

Testes devem alcançar o comportamento pelo contrato pertinente. Fakes ajudam a
exercitar regras, mas não provam isolamento transacional, constraints, leases,
atomicidade ou efeitos exatamente uma vez. Verifique essas garantias no storage e
runtime responsáveis, incluindo concorrência e recuperação quando afetadas.

<a id="sistemas"></a>

## Arquitetura de sistema e de solução

Para uma solução entre sistemas, comece pelo fluxo de negócio: participantes,
responsáveis, fontes de verdade e dados/eventos trocados. Para um módulo existente,
comece pelo diagnóstico local. Explicite as restrições que discriminam alternativas:

- Contratos, consistência, fronteiras de transação e falha; requisitos de auditoria
  e retenção efetivamente fornecidos, sem inventar obrigações.
- Carga e distribuição de acesso, fan-out, latência alvo, saturação, throughput,
  pools/filas e limites das dependências. Valores desconhecidos são hipóteses.
- Ownership operacional, autonomia de deploy, compatibilidade de versões, custo
  de operar, observabilidade e objetivos de recuperação.

Compare as alternativas viáveis com manter/adaptar a solução atual. Número de
registros, QPS, tamanho de equipe e nomes de tecnologias isolados não selecionam
banco ou arquitetura. Examine consultas, índices, contenção, consistência,
distribuição e carga equivalente antes de recomendar troca por desempenho.

Ao distribuir uma operação, explicite round trips e a atomicidade que se perde.
Defina identidade, repetição, ordenação, falha parcial, recuperação e ownership dos
retries conforme [modelagem](domain-design.md). Limite fan-out e recursos. Uma API
idêntica não demonstra equivalência se mudar a janela de falha ou visibilidade.
Migração deve tratar coexistência, cutover e recuperação no [plano](plan.md)
existente; rollback de código não desfaz efeitos persistidos.

<a id="padroes"></a>

## Seleção contextual de padrões

| Abordagem | Sinal que justifica considerar | Custo/condição para escolher |
| --- | --- | --- |
| Clean Architecture / camadas | Regras de negócio acopladas a transporte ou infraestrutura dificultam evolução/verificação | Direção de dependências explícita; introduza só separações que protejam o contrato. Mapeamentos e camadas extras precisam de benefício demonstrável. |
| Hexagonal / ports and adapters | Integração externa volátil, efeitos difíceis de controlar ou tradução duplicada | Porta pelo contrato consumidor; adapter concentra tradução. Preserve semântica de erros, timeout e recursos, não apenas tipos. |
| DDD | Linguagem ambígua, regras complexas e ownership conflitante | Bounded contexts delimitam modelos; aggregates delimitam invariantes/consistência. Value objects precisam de semântica/validação real. Contexto não implica microsserviço. |
| Monólito modular | Coesão transacional e deploy conjunto atendem às restrições | Módulos com contratos claros e operação simples; avalie limites de escala e autonomia reais. |
| Serviços separados | Escala, isolamento ou deploy independente justificam a fronteira e há ownership operacional | Pagar rede, falhas parciais, compatibilidade e coordenação de dados; extração incremental, não divisão por entidade. |
| CQRS | Modelos de leitura e escrita têm necessidades distintas que a solução atual não atende bem | Custos de projeção, sincronização e defasagem; separar código de leitura/escrita não exige bancos separados. |
| Event sourcing | Histórico de eventos como fonte de verdade e reconstrução de estado são requisitos adequados ao domínio | Evolução de eventos, replay, efeitos e projeções precisam de contrato. Auditoria, sozinha, não exige event sourcing. |

## Saída da decisão

No chat, plano ou ADR já usado, registre apenas o necessário: problema/evidência,
restrições, alternativas, decisão, custos aceitos, cenário que a valida e condição
de reconsideração. Em review, vincule achado ao fluxo e impacto demonstráveis.
Para executar uma mudança estrutural, consulte [refatoração](refactoring.md) quando
precisar preservar comportamento; mudança de contrato deve ser explicitada como tal.
