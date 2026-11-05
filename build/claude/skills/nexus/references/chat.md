# Chat guiado e apresentação portátil

Use este contrato para acompanhamento, decisões e entregas em todas as entradas
NEXUS. Ele orienta o agente a usar recursos existentes; não instala uma interface,
não controla o layout global do aplicativo e não acrescenta gates ao workflow.
Instruções do host, preferências e autorizações existentes prevalecem.

## Composição da resposta

Comece pelo resultado ou situação atual. Para trabalho com etapas, componha a
resposta nesta ordem, incluindo apenas partes pertinentes:

1. **Situação:** o que mudou, o que está em andamento e o bloqueio relevante.
2. **Acompanhamento:** lista compacta de tarefas com estado e próxima ação;
   responsável quando houver mais de um. Destaque itens ativos/bloqueados; agrupe
   concluídos e deixe o restante acessível sem truncamento silencioso.
3. **Decisão:** quando uma escolha real estiver pendente, apresente a pergunta,
   opções com consequências e recomendação fundamentada. Explicite o que a
   resposta autoriza. Reuse aceites anteriores para o mesmo alvo e escopo.
4. **Evidências:** links verificáveis para arquivos, diffs, testes ou artefatos;
   detalhe técnico expansível quando suportado. Bloqueios e limitações que mudam
   uma decisão ficam visíveis, não escondidos nos detalhes.
5. **Próxima ação:** quem pode avançar e o que falta. No fechamento, preserve o
   [contrato de entrega](invocation.md#entrega-comum), inclusive verificações não
   executadas e arquivos alterados.

Isso é ordem de informação, não cinco títulos obrigatórios. Pergunta simples
recebe resposta direta; uma tarefa pequena dispensa painel, checklist e contagem.
Use linguagem do usuário, rótulos curtos, hierarquia visual discreta e texto junto
dos indicadores de estado. Não dependa apenas de cor, emoji, hover ou largura fixa.

## Spec e plano em painel nativo

Ao entregar uma SPEC ou PLAN para revisão, prefira abrir o documento Markdown no
painel nativo disponível. Reuse o arquivo adotado pelo projeto ou pelo modo de
planejamento do host. Quando um documento salvo for útil à revisão/retomada e a
escrita estiver autorizada, salve-o no workspace consumidor; use os
[templates](../assets/templates/contracts.md) se precisar desse formato. Pergunta
conceitual, plano curto no chat e pedido de não criar arquivos mantêm sua entrega
direta. As permissões do modo atual prevalecem, inclusive para salvar a SPEC.

Componha o documento para leitura: título descritivo, identidade/revisão e estado
quando conhecidos, resumo em uma frase e seções curtas. Na spec, agrupe objetivo,
escopo, contratos, aceites e decisões. No plano, numere entregas verificáveis com
dependências, arquivos/componentes, validação e conclusão. Use bullets para itens
paralelos e tabelas curtas para comparações; preserve os campos e vínculos do
formato adotado. Evidência ainda não coletada permanece identificada como tal.

Depois de salvar ou atualizar a proposta, selecione a abertura pela capacidade
verificada da sessão, usando o schema real:

| Superfície e capacidade disponível | Apresentação |
| --- | --- |
| Codex desktop com ferramenta de abertura de arquivo, como `open_in_codex` | Abra o arquivo existente pelo caminho absoluto no painel à direita, quando essa posição for aceita. Use o alvo de arquivo; não crie uma Page ou cópia para exibi-lo. |
| Claude Code no VS Code com revisão nativa de plano no modo já adotado | Apresente o PLAN pelo mecanismo nativo permitido, conservando o arquivo de plano do host. A SPEC continua documento separado; abra-a em preview Markdown se houver ferramenta para isso. |
| Claude Code desktop ou outro editor com abertura/preview de arquivo exposto | Use a capacidade disponível para o mesmo Markdown. Abrir no editor não comprova preview renderizado. |
| Terminal, capacidade ausente, proibida ou falha | Entregue link/caminho real e resumo no chat. No VS Code, pode indicar a abertura manual por `Markdown: Open Preview to the Side`; isso não é uma chamada de ferramenta. |

Não mude para Plan nem acione saída/aprovação de plano apenas para obter um
preview. A revisão nativa deve preservar o escopo do pedido: somente planejar
encerra na entrega; abrir, ler ou comentar um documento não autoriza execução.
As regras de aceite do fluxo continuam valendo quando execução estiver em escopo.

No chat, mantenha resumo, links reais da spec/plano, revisão conhecida, decisão
pendente e efeito do aceite quando pertinente. Deixe riscos/bloqueios que mudam
a decisão visíveis no resumo; o detalhamento fica no documento. Abra os documentos
pertinentes no checkpoint de revisão e reaproveite abas existentes quando possível;
atualizações de progresso não reabrem ambos os arquivos a cada mensagem.

O painel é uma visualização da mesma fonte. Antes de incorporar edição ou
comentário recebido no painel, releia o documento e reconcilie a revisão; não
sobrescreva alterações do usuário nem mantenha estado de tarefas em outra UI.
Uma abertura confirmada comprova a abertura, não a fidelidade da renderização.
Se a ferramenta retornar abertura enfileirada, informe que está pendente e mantenha
o link, sem anunciar que o painel abriu nem reenviar a mesma solicitação.
Se falhar, preserve arquivo, estado e decisão em texto, sem repetir a operação
em ciclo. A apresentação usa recursos existentes, sem gerar HTML, instalar
dependências, iniciar serviço ou consultar outro modelo para renderizar.

## Escolha de componentes do host

Na primeira necessidade, examine ferramentas e instruções disponíveis na sessão.
Reaproveite essa descoberta enquanto continuar válida; reavalie em mudança de
host/modo ou falha. Disponibilidade inclui permissão de uso no modo atual, schema
e semântica da ferramenta. Marca do provedor, modelo, plugin instalado ou exemplo
na documentação não comprovam que a sessão dispõe da capacidade.

Use o componente nativo pertinente quando estiver verificado e permitido; não
fique apenas descrevendo que poderia usá-lo. Se o formato da ferramenta for
diferente do exemplo abaixo, siga o schema real. Não invente nomes de APIs,
diretivas, botões, componentes ou garantias de renderização.

| Necessidade | Recurso existente, se verificado | Fallback portátil |
| --- | --- | --- |
| Etapas e tarefas | Lista/plano nativo com semântica de estado compatível | Lista curta com estado, responsável e próxima ação |
| Escolha do usuário | Pergunta estruturada, seleção ou formulário nativo | Uma pergunta objetiva; alternativas curtas ou resposta livre |
| Evidências | Referências de arquivos, diff/review ou detalhe expansível | Links reais e resumo; detalhes adicionais sob demanda |
| Comparar alternativas | Tabela ou visualização já disponível | Lista de trade-offs, ou tabela quando legível no terminal |
| Explorar uma interface | Preview/artefato interativo existente, quando útil ao pedido | Descrição e exemplo textual equivalente |

A seleção é por recurso: um host pode ter perguntas estruturadas, mas não listas
ou HTML. Uma ferramenta exclusiva de planejamento não deve ser chamada fora desse
modo; use texto. Recursos de Codex, Claude Code ou outro host só entram na resposta
quando expostos pela sessão. Não instalar SDK, MCP, plugin ou serviço para exibir
um status; não gerar uma aplicação HTML a cada atualização. Novos adapters/runtime
exigem escopo próprio conforme as fronteiras do pacote.

Uma lista nativa só pode receber a projeção da fonte existente se não introduzir
uma autoridade concorrente. Se a ferramenta mantiver seu próprio todo editável
sem integração verificada, use a lista textual. Se o estado nativo já for a fonte
adotada, use-o diretamente. Preserve IDs e estados da fonte; uma UI que só admite
pendente/em andamento/concluído precisa mostrar explicitamente bloqueios e revisão.
Se não conseguir preservá-los, use texto; não converta `validating` em `done`.

## Interação e acompanhamento

- Para decisão pendente, use a pergunta nativa permitida, com poucas opções
  distinguíveis e a recomendação identificada. Permita resposta livre conforme
  o host. Não apresente preferência pré-selecionada como resposta recebida.
- Status é leitura: pode expor uma decisão pendente e oferecer sua resolução,
  mas não inicia execução. Se o usuário pediu somente informar, informe a decisão
  sem abrir pergunta. Quando houver continuidade autorizada, pergunte apenas o
  necessário e avance no trabalho independente. Silêncio não aprova ação; pergunta
  opcional segue as regras de default/espera do host. Uma exigência de autorização
  permanece pendente até resposta válida, pelo mecanismo permitido pelo host.
- Ofereça ações somente quando houver handler/ferramenta real e efeito definido.
  Abrir evidências ou expandir detalhes é apresentação. Aprovar, continuar,
  cancelar ou repetir é ação sobre o trabalho: respeita escopo, gates e permissões.
  Cancelamento solicitado não equivale a processo encerrado.
- Um protótipo deve identificar dados fictícios e interação simulada. Clique em
  demonstração não autoriza operação real. Não afirmar atualização ao vivo, painel
  persistente ou sincronização sem mecanismo efetivo.
- Prefira atualizações por mudança relevante: conclusão de etapa, bloqueio,
  decisão, falha, recuperação e entrega. Respeite cadência exigida pelo host e
  preferência do usuário. Não acrescentar pergunta sobre frequência a toda tarefa,
  nem prometer monitoramento após a sessão sem ferramenta e autorização próprias.

## Estado, concorrência e recuperação

O chat é uma apresentação da [fonte adotada](workflow.md), não um segundo store.
Em trabalho rastreado, identifique a fonte e revisão ou instante de observação
disponível; se não conhecidos, declare isso sem inventar metadados. Sem persistência,
diga que o estado está apenas na conversa quando a continuidade depender dele.
Contagem `2/4 concluídas` é contagem de tarefas, não 50% do esforço nem previsão.
Consumo, latência e duração exigem medições com origem; ausência fica desconhecida.

Antes de aplicar uma ação recebida de cartão/lista/pergunta, reconcilie alvo,
estado atual e efeito autorizado com a proposta apresentada. Use IDs e revisão
disponíveis. Proposta materialmente alterada exige reapresentar a escolha afetada;
mudança irrelevante à escolha não exige novo aceite. Sem revisão disponível,
releia a fonte e não prometa proteção atômica que o host não oferece.

Quando adotada a CLI, preserve seu [contrato de revisão e operação](workflow-state.md):
use a revisão atual e a mesma identidade para retry do mesmo payload. Isso não
torna efeitos externos idempotentes. Em clique duplicado ou timeout, consulte
recibo/handle/estado antes de repetir ou redistribuir. Resultado externo incerto
fica pendente de reconciliação, com próxima ação explícita. Não libere ownership
nem anuncie sucesso por falha da UI. Trabalho independente autorizado pode continuar.

Se a renderização falhar, degrade apenas a apresentação para texto e preserve o
estado e a decisão pendente. Se uma ferramenta de interação retornar resultado
incerto, reconcilie também a interação antes de reenviar uma ação. Uma UI editável
ou bloqueio visual de botão não substitui validação do estado na ferramenta real.

Agrupe eventos do mesmo checkpoint; não recarregue histórico e evidências inteiros
a cada mensagem. Expansão local de detalhes não precisa de nova inferência quando
o host já dispõe dos dados. Mantenha ownership e dependências visíveis quando
afetarem o acompanhamento; mais componentes não justificam aumentar paralelismo,
polling ou chamadas externas. São orientações de custo/latência, não benchmarks.

## Exemplo portátil

Exemplo fictício, sem operação associada. O conteúdo essencial deve permanecer
equivalente ao usar componentes nativos; adapte a formatação às regras do host.

> A estrutura está pronta; a revisão continua. 2 de 4 tarefas concluídas.
>
> - T1/T2 — concluídas; evidências E1/E2 disponíveis na fonte.
> - T3 — em revisão; responsável: agente principal.
> - T4 — aguardando você: escolher a apresentação preferida.
>
> Prefere resumo compacto ou detalhes por tarefa? Recomendo compacto para
> acompanhamento. A escolha altera a apresentação, sem autorizar novas operações.
>
> Próxima ação: concluir a revisão já autorizada de T3.
> Fonte: snapshot fictício rev7. Consumo e previsão de término não medidos.

No uso real, substitua referências de evidência por links existentes quando o host
os suportar. Se só houver um identificador, apresente-o como tal; não fabrique URL.
