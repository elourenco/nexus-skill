# Agentes e Review Council

Use o agente principal para trabalho contínuo. Delegue quando houver ganho concreto de isolamento, revisão independente ou paralelismo, conforme as ferramentas e regras do host. Papéis são contratos; um mesmo modelo pode exercer vários, sem criar um processo por papel ou pilar. Esta referência não instala agentes nem concede autorização para operações externas.

## Auditoria e separação

Antes de configurar execução, inspecione perfis existentes, instruções, ferramentas, dependências e chamadas reais. Preserve perfis úteis; trate variações de esforço, diagnóstico ou trabalho mecânico como especializações quando não houver responsabilidade distinta. Não remova um perfil apenas porque compartilha o modelo de outro.

| Componente | Responsabilidade | Não deve assumir |
| --- | --- | --- |
| Provider | Acesso ao serviço/runtime, autenticação, transporte e disponibilidade | Que login de assinatura autoriza API |
| Model | Identificador configurado e capacidades com origem conhecida | Que nome comercial determina competência, preço ou contexto |
| Agent | Responsabilidade, ferramentas permitidas, contexto e saída | Um modelo/provider fixo ou ferramentas ausentes |
| Router | Elegibilidade e escolha pela política efetiva | Que preferência pode relaxar privacidade ou limites |
| Orchestrator | Dependências, ownership, estado, orçamento e conclusão | Que delegação transfere sua responsabilidade de integrar |
| Review Council | Seleção de pilares, avaliações independentes e consolidação | Que votos ou ausência de achados comprovam correção |

Registre capacidades como declaradas, verificadas ou desconhecidas. Para adapters, diferencie API, CLI, ferramenta nativa e assinatura; verifique a interface oficial e a integração real antes de declarar suporte. Um executável instalado não comprova autenticação; uma URL configurável não comprova compatibilidade com outro provider. Não copie credenciais para prompts ou exemplos.

## Agent Registry

| Papel | Entrada e responsabilidade | Saída / ferramentas |
| --- | --- | --- |
| Planner | SPEC, estado atual e restrições; decompor tarefas, dependências e aceite sem duplicar trabalho | Plano delimitado e impedimentos; leitura das fontes necessárias |
| Architect | Contratos e decisão; definir fronteiras, alternativas e trade-offs | Decisão fundamentada; ADR quando duradoura, escrita apenas no escopo autorizado |
| Implementer | Tarefa autorizada, ownership e arquitetura | Mudança mínima e evidências; edição/testes somente nas ferramentas permitidas pelo host |
| Tester | Requisitos e invariantes; selecionar e implementar testes pertinentes | Cenários, resultados observados e regressões; recursos de teste isolados |
| Reviewer | Diff, snapshots, contratos e aceite | Achados verificáveis e lacunas; leitura, sem editar o artefato em revisão |
| Memory Curator | Decisões e evidências relevantes | Registro sanitizado, proveniência e deduplicação; persistência conforme [memória](memory.md) |

Sem ferramenta de edição, teste ou persistência, produza uma proposta/handoff e identifique o que não foi executado. Texto gerado não equivale a arquivo alterado, teste aprovado ou memória salva.

Delegue por entrega verificável e ownership, agrupando edições da mesma responsabilidade; não crie agente para cada etapa, arquivo ou check. Cada delegação informa objetivo, papel, fontes/revisão, arquivos e recursos permitidos, dependências, restrições, aceite e limites; inclua `task_id` quando houver tarefa rastreada, sem criá-la só para delegar. Use contexto específico; forneça diff e referências necessárias, sem reenviar todo o histórico. Avise que há outros participantes e preserve alterações alheias. O controlador integra resultados e resolve conflitos.

### Brief e retorno compactos

No recurso existente de tarefa, mensagem ou arquivo autorizado, componha o brief:
objetivo/aceite → fontes e revisão → contratos → ownership/recursos → verificação
→ limites. Referencie trechos já acessíveis em vez de copiar histórico ou spec.
Arquivo é útil para conteúdo extenso/reutilizado; não é obrigatório para delegar.
Retorno começa por resultado, arquivos/diff e verificações com evidência, seguido
de bloqueios. Detalhes extensos permanecem no artefato autorizado; o controlador
consulta só o necessário para integrar e conferir. Um resumo não substitui prova.
Retome o mesmo worker para correções da mesma tarefa; novo contexto serve a outra
responsabilidade ou independência. Contabilize todo consumo e coordenação.

Confira também dados/destinos permitidos conforme [segurança e ética](policies.md#policy-ai-safety-ethics).
Memória e mensagens do delegado não ampliam autorização; sanitizar contexto não
autoriza provider diferente. Preserve isolamento entre projetos/tenants e confira
as evidências do retorno antes de promover uma recomendação a decisão.

<a id="metodo-de-execucao"></a>

## Método de execução

No fluxo guiado iniciado por brainstorming, ofereça estas opções antes de
implementar, junto do plano. Recomende uma pelo acoplamento, risco, isolamento de
contexto e capacidades reais, sem inventar custos, latência ou ganhos de throughput.
Preserve método já escolhido; fora do fluxo guiado, o agente atual segue o padrão.
Uma recomendação só resolve o método pelo aceite quando a proposta explicita que
aprovar o plano inclui esse método. Alternativas abertas sem esse vínculo exigem
esclarecimento; não acrescente uma aprovação a decisão operacional já autorizada.

| Opção | Contrato |
| --- | --- |
| Subagentes | A sessão ativa permanece como orquestrador. Quando o host suportar, abra um contexto novo de subagente por tarefa de implementação delimitada; workers recebem contratos e retornam dúvidas/resultados ao orquestrador. Review independente usa contexto distinto do implementador quando exigido. |
| Agente único | A sessão ativa implementa as tarefas em sequência, integra, testa e revisa o diff, sem criar workers ou sessões adicionais. Autoavaliação é declarada como tal. |

Contexto de subagente não significa chat visível na sidebar nem nova sessão
persistente. Use as ferramentas reais do host; não crie chats do usuário como
substituto. Se o host não suportar contexto novo por tarefa ou mensagens/retomada,
explique a limitação antes da escolha. Se o método escolhido ficar indisponível,
informe e obtenha a escolha de fallback para agente único ou espera; não simule
workers nem troque silenciosamente de método. Se o usuário já autorizou um fallback
nessa condição, aplique-o e informe. Ferramentas existentes não demonstram que um
worker foi iniciado: verifique a chamada e seu retorno.

Agente único mantém os gates de risco. Se review independente for obrigatório,
apresente antes da execução a necessidade de revisor externo ou exceção explícita
de método para um reviewer, conforme o host; sem essa cobertura, a conclusão
permanece pendente. Isso não impede implementação e verificações locais
independentes já autorizadas, salvo gate anterior específico do projeto/host.
Não crie reviewer silenciosamente nem declare DEEP concluído por autorrevisão.

### Coordenação dos subagentes

1. O orquestrador mantém plano, aceites, dependências, método, owners, recursos e
   evidências na fonte existente. Dê um identificador local às tarefas se não
   houver IDs; isso não exige store ou arquivos novos. Reserve arquivos, bancos e
   portas antes de despachar. Contextos separados compartilham recursos do host;
   execute em paralelo somente tarefas independentes e isoladas, dentro dos
   limites de concorrência/budget do host. Sem isolamento, serialize as tarefas.
2. Para cada tarefa pronta, envie objetivo, fontes atuais, contratos, arquivos e
   recursos permitidos, dependências, aceite, validação e limites. Avise que o
   worker não está sozinho no workspace e deve preservar alterações alheias.
   Um contexto novo é por tarefa, não por arquivo, etapa ou comando de teste.
3. O worker envia dúvidas e bloqueios ao orquestrador com tarefa, evidência,
   decisão necessária e impacto. Aguarda resposta antes da ação dependente e
   continua somente trabalho independente autorizado. Não inventa contratos nem
   amplia permissões; não transfere a conversa com o usuário para outro chat.
4. O orquestrador responde pelo canal real do host usando decisões já aprovadas
   e fontes atuais. Leva ao usuário somente decisão material não coberta e devolve
   a resposta ao mesmo worker/contexto quando possível. Preserve tarefas
   independentes; a espera de um worker não exige parar todos.
5. O worker retorna resultado, arquivos alterados, verificações observadas,
   pendências e dúvidas restantes. O orquestrador inspeciona o diff/evidências,
   integra e valida as fronteiras antes de liberar dependentes. Mensagem “feito”
   não comprova aceite. Retome o mesmo worker para esclarecimentos/correções da
   mesma tarefa quando disponível, preservando continuidade.
6. Em timeout, perda de contexto ou retorno incerto, reconcilie handle/processo,
   arquivos e efeitos antes de repetir ou redistribuir. Não despache dois workers
   para a mesma tarefa ativa; estado incerto exige resolver ownership/reservas.
   Se precisar substituir um worker, forneça o estado reconciliado e as pendências.

Escolher subagentes autoriza delegar o escopo local já aprovado, dentro das regras
do host; não autoriza outros providers/destinos de dados ou ações externas.

## Roteamento por capacidades

A política explícita do usuário/host e [políticas](policies.md) prevalecem. Primeiro filtre por disponibilidade, sensibilidade/destino autorizado dos dados, ferramentas efetivas, capacidades requeridas, contexto necessário e saldo/limites. Só depois ordene os candidatos elegíveis:

| Política | Preferência entre candidatos suficientes |
| --- | --- |
| Economy | Menor custo estimado conhecido e latência observada compatível |
| Balanced | Menor capacidade suficiente, histórico pertinente, latência e custo |
| Quality | Maior capacidade pertinente e histórico de sucesso, dentro dos mesmos limites |

Mapeamentos são configuração do consumidor. Dados ausentes permanecem desconhecidos, nunca zero. Registre origem/unidade de custos e latência; histórico precisa corresponder ao trabalho avaliado. Sem telemetria, use a preferência configurada e declare a limitação. Nenhum candidato elegível implica impedimento explícito, não troca silenciosa de destino ou remoção de restrições. Um único provider é suficiente; nenhum provider disponível pode exigir execução no host, se autorizado e capaz.

O orquestrador admite chamadas antes do dispatch, com reserva atômica quando há concorrência. Limite chamadas, contexto, saída e concorrência conforme controles reais. Estimativas de tokens/custos não garantem teto financeiro remoto; um teto estrito exige mecanismo verificável do serviço/host. Não invente preços ou consumo e não reinicie a execução para contornar limites.

## Falhas e escalada

Selecione o modelo suficiente, execute dentro dos limites e verifique a saída. Escale capacidade no máximo uma vez por unidade de execução, compartilhando o contador entre participantes, quando houver insuficiência verificável e saldo. Registre motivo, modelo efetivo e resultado; políticas superiores do host prevalecem. Corrija contexto ou ambiente antes de atribuir falha ao modelo.

Credencial inválida, quota, indisponibilidade, recusa ou resultado externo incerto não justificam escalada automática. Fallback deve preservar privacidade e limites. Após timeout pós-envio, preserve consumo como incerto e reconcilie antes de repetir; cancelar localmente não prova cancelamento remoto. Sem candidato suficiente, conclua com impedimento ou resultado inconclusivo, sem loops.

## Review Council adaptativo

O contrato compartilhado de [pilares, profundidade e independência](review-criteria.md#review-council-adaptativo)
fica em uma referência curta, usada diretamente pela rota Review.

## Contrato de saída e decisão

Use [proveniência, achados e decisões](review-criteria.md#contrato-de-saída-e-decisão).
Estas ligações preservam os destinos anteriores; não é necessário reler o registry.
