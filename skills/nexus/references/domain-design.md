# Modelagem nos pontos de mudança

Use quando a alteração afetar estados do domínio, entrada externa ou ownership de
dados. Se o código já for claro e local, preserve-o. Este checklist complementa
[Policies](policies.md); não cria fase, camada ou documento obrigatório.

| Condição observável | Decisão e evidência suficiente |
| --- | --- |
| Flags/opcionais permitem combinações inválidas | Modele estados e transições válidos por construção quando a linguagem permitir: variante discriminada, enum com dados ou construtor validado. Demonstre a combinação rejeitada e a transição permitida. Não troque validação de runtime por um cast. |
| Dados cruzam uma fronteira externa | Faça parsing e validação naquela fronteira e entregue um valor de domínio confiável ao código interno. Outra fronteira de confiança exige sua própria validação; autorização e invariantes dependentes do estado continuam sendo verificadas no momento da operação. |
| Saída de IA pode produzir efeito ou decisão sobre pessoas | Trate-a como entrada externa. Defina ações permitidas, responsável e validação/autorização no executor; supervisão e contestação conforme o [impacto](ai-safety-ethics.md#ai-products). Não confunda schema válido com ação autorizada ou decisão justa. |
| Regra de negócio mistura cálculo com rede/disco/relógio | Extraia a decisão determinística e deixe I/O na borda quando isso reduzir acoplamento. Teste entradas/saídas reais e a integração da borda; não introduza interfaces/camadas sem consumidor. |
| Dois atores alteram o mesmo estado | Primeiro confirme se precisam compartilhá-lo; particione por ownership quando possível. Caso precisem, escolha atomicidade/transação/serialização no escopo correto. Um lock em memória não coordena processos; locks locais não coordenam servidores distintos. |
| Operação pode repetir ou falhar parcialmente | Defina identidade, escopo de deduplicação, duração e comportamento após crash. Mostre o resultado de repetição concorrente; timeout não confirma que o efeito falhou. |

Comece pela forma dos dados e pelo contrato observável. Glossário só para termos
ambíguos que afetem a implementação; reutilize o existente. Evite generalização
prematura e deduplicação entre conceitos com semânticas diferentes.

Para estado compartilhado, registre o escritor/escopo, o ponto de atomicidade,
a invariante e um cenário de interleaving ou recuperação que possa quebrá-la.
Avalie contenção, latência e throughput com carga equivalente quando desempenho
for critério de aceite. Sem execução, apresente hipótese e teste proposto.

Quando uma aprovação depender de estado mutável, preserve sua validade até o
efeito com atomicidade/isolamento adequados; releitura isolada não elimina corrida.
A [recuperação de IA](ai-safety-ethics.md#failure-recovery) aplica esses contratos
também a ferramentas, controles indisponíveis e limites agregados.

Exemplo: um contador de jobs por tenant precisa de incremento atômico no storage
compartilhado, isolamento por tenant e uma identidade de job se a entrega repetir.
Uma transação pode garantir incremento sem perda e ainda contar o mesmo job duas
vezes; atomicidade e deduplicação têm aceites distintos. Não exigir fila ou lock
global quando a operação atômica do storage já atende ao contrato.

Saída: decisão curta no plano, diff ou review existente, com o cenário que a
verifica. Sem mudança nessas dimensões, não percorra o checklist.
