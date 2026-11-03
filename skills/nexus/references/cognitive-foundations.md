# Fundamentos da compreensão e decisão

Referência de estudo e manutenção do [protocolo cognitivo](cognitive.md).
Não é pré-requisito de execução, checklist adicional ou sequência de autores a
consultar. Os métodos abaixo inspiram intervenções observáveis; não descrevem a
arquitetura mental de um modelo nem comprovam ganhos de qualidade ou velocidade.

## Filosofia e lógica da investigação

| Fundamento | Aplicação no NEXUS | Limite |
| --- | --- | --- |
| Questionamento socrático | Esclarecer termos, premissas e contradições que mudam a decisão | Afinidade conceitual, não implementação histórica do elenchus; perguntar mais não implica compreender melhor |
| Primeiros princípios | Distinguir requisito, restrição verificada, suposição e convenção; reconstruir a parte inadequada | Convenção útil não precisa ser redescoberta; preservar requisitos válidos |
| Abdução, dedução e indução — Peirce | Gerar explicação plausível, derivar previsão, confrontar resultado e revisar suporte | Plausibilidade não prova causa; hipóteses iniciais podem estar todas erradas |
| Falsificacionismo — Popper | Definir observação que contraria a hipótese antes de testar | Um teste depende de medição e condições auxiliares; resultado inesperado exige verificar também o teste |
| Parcimônia | Preferir explicação/solução suficiente sem suposições/mecanismos gratuitos | Explicação simples e implementação simples são critérios distintos; nenhuma pode violar invariantes |
| Afinidade com o estoicismo | Separar ação controlável de dependência externa e condição de retomada | Organiza ação, não diagnostica causalidade nem aceita falhas evitáveis |

Peirce distingue a criação de hipóteses da derivação de consequências e de sua
avaliação pela experiência. Usamos essa distinção em
`hypothesis.falsify`, sem exigir exposição do raciocínio privado.
[Texto de Peirce sobre os tipos de raciocínio](https://www.textlog.de/7660.html).
Para a discussão dos limites da refutação, consulte
[Karl Popper — Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/popper/).
As outras correspondências da tabela são analogias operacionais, não alegações de
fidelidade a uma escola filosófica ou validação científica do protocolo.

## Psicologia e decisão sob restrições

- **Racionalidade limitada — Herbert Simon:** decidir sob informação e recursos
  limitados sustenta buscar uma ação suficiente, com critério de parada. No NEXUS,
  suficiência depende de risco e reversibilidade, preservando gates obrigatórios.
  [A Behavioral Model of Rational Choice, 1955](https://academic.oup.com/qje/article-abstract/69/1/99/1919737?login=false).
- **Considerar o contrário — Lord, Lepper e Preston:** procurar uma razão concreta
  para a favorita estar errada inspira `bias.challenge`. Não exige oposição ritual
  nem garante eliminação de vieses; o estudo original trata julgamento humano.
  [Considering the Opposite, 1984](https://www.researchgate.net/profile/Mark-Lepper-2/publication/16669522_Considering_the_Opposite_A_Corrective_Strategy_for_Social_Judgment/links/56107d7508ae48337519fedb/Considering-the-Opposite-A-Corrective-Strategy-for-Social-Judgment.pdf).
- **Metacognição — John Flavell:** monitorar compreensão e lacunas inspira
  `reasoning.reflect`. A adaptação exige evidência externa e atualização concisa;
  introspecção do modelo não valida sua conclusão.
  [Metacognition and Cognitive Monitoring, 1979](https://jwilson.coe.uga.edu/EMAT7050/Students/Wilson/Flavell%20%281979%29.pdf).
- **Expertise — Kahneman e Klein:** regularidade do ambiente e oportunidade de
  aprendizado são condições importantes para intuições habilidosas em pessoas.
  No protocolo, familiaridade sugere uma hipótese; não substitui evidência.
  FAST/BALANCED/DEEP regulam esforço e não equivalem aos Sistemas 1/2.
  [Conditions for Intuitive Expertise, 2009](https://gwern.net/doc/psychology/cognitive-bias/illusion-of-depth/2009-kahneman.pdf).

## Valor da investigação e atualização

**Metarraciocínio racional — Russell e Wefald:** escolher computações pelo valor
esperado para a próxima decisão inspira a seleção de leituras, perguntas e testes.
A adaptação é qualitativa: resultado capaz de mudar a ação, consequência do erro,
custo, latência e risco da verificação. Não implementa cálculo de utilidade ótima.
[Descrição do programa de pesquisa por Russell](https://aima.cs.berkeley.edu/~russell/research-bo.html).

**Atualização inspirada em Bayes:** histórico comparável informa plausibilidade;
evidência discriminante muda suporte relativo. O protocolo não calcula posterior
sem probabilidades justificadas. Réplicas da mesma medição têm origem comum;
não devem ser multiplicadas como evidências independentes. Confiança numérica
requer calibração, não fluência da resposta.

**Causalidade:** observação conjunta não basta para atribuir causa. Considere
fatores de confusão e condições equivalentes; intervenções de teste exigem
autorização e controle do risco. O NEXUS não implementa inferência causal formal.
[Pearl, An Introduction to Causal Inference](https://escholarship.org/uc/item/9qf971fw).

## Exemplo e avaliação

“Adicionar cache” vira “reduzir p95 sob carga conhecida preservando consistência”.
Queries extras e espera no pool geram previsões diferentes: quantidade de queries
por request e tempo de aquisição da conexão. Se a espera dominar a amostra local,
investigue ocupação/transações antes de escolher mecanismo. Isso não confirma
comportamento em produção nem autoriza alterar limites do pool.

Avalie formulação, evidência, perguntas dispensáveis, preservação de invariantes e
condição de parada em cenários equivalentes. Meça chamadas e tokens totais somente
com telemetria do host; caracteres/palavras medem tamanho textual, não consumo.
Compare qualidade antes de atribuir valor à redução de latência ou texto. Estudos
humanos fundamentam as analogias; avaliações de agentes precisam testar sua eficácia.
