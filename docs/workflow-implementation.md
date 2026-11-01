# Workflows — auditoria e decisões de implementação

Data: 2026-10-31. A ampliação para executor local, scripts, testes e ajustes mínimos nos pontos de entrada foi autorizada pelo usuário. Este escopo substitui, apenas para esta frente, o limite documental da fase 1. Não inclui dashboard, instalação global, SDK de providers, commits, publicação ou deploy.

## Auditoria da base

| Existente | Constatação | Decisão |
| --- | --- | --- |
| workflow.md | Explore/Plan/Build/Review/Autonomous; seis estados e recuperação descritos | Preservar intenções e acrescentar profundidades FAST/BALANCED/DEEP e validating |
| Cinco templates | SPEC, PLAN, task, ADR e memória já úteis | Preservar arquivos; exportar pela CLI e vincular artefatos ao estado |
| agents.md | Papéis e pilares lógicos; nenhum registry executável | Manter política e acrescentar snapshot local de capacidades atribuídas ao host |
| policies.md | Testes adaptativos, roteamento e consumo com proveniência | Aplicar decisões à task; nenhuma tabela global de modelos/preços |
| hooks.md | Eventos lógicos sem adapters instalados | Não simular hooks nem incorporar executor de eventos nesta entrega |
| memory.md | Proveniência e isolamento; sem índice de memória | Manter política; capturar disposição da memória na entrega |
| scripts/validate.py | Metadados e links; não executa workflow | Preservar e acrescentar testes comportamentais separados |
| Todo | Checklist manual, sem comando, estado transacional ou interface nativa | Implementar CLI de mutação e projeções JSON/Markdown |

A separação entre intenções e profundidade evita duplicar modos: Autonomous não vira uma segunda máquina de estados; FAST não remove gates necessários por risco. A política de testes continua em policies.md, e o workflow apenas registra escolha e razão. Templates continuam com sua própria frente; nenhum foi substituído por outra variante.

## Arquitetura e alternativas

Foram consideradas instruções/checklist sem runtime, store local transacional e plataforma com serviço/banco/provider. Checklist não satisfaz persistência/idempotência solicitadas. Serviço/banco obrigatório ampliaria instalação, operação e fronteiras externas sem necessidade demonstrada. A escolha é Python padrão, um snapshot JSON por workflow e três camadas: store, orchestrator, presentation.

O store possui lock com timeout, revisão otimista, operation_id idempotente e gravação atômica de snapshot+histórico. O orquestrador controla dependências, tentativas, reservas e gates. A CLI não contém regras de transição; outro adapter pode consumir a mesma API. O estado não é um controle de acesso: agentes continuam sujeitos às permissões do host e ao escopo do usuário.

Não existe transação distribuída entre arquivo e provider. Dispatch persiste uma intenção e run.id antes da chamada do host; ack grava handle real depois. Se houver interrupção entre chamada e recibo, mantenha recursos e consulte o host. Nenhum replay automático de chamada externa é considerado seguro por causa do operation_id local.

Evidências são atribuídas à geração da tarefa. Mudanças de critérios/contratos e rework invalidam provas antigas. SPEC usa revisão+hash, PLAN aponta para a SPEC vigente. Achados não podem ser substituídos por colisão de ID. A implementação conserva reservas durante testes e review, inclusive quando a validação fica bloqueada.

## Performance, concorrência e recuperação

Não há chamadas de rede na transação. DAG é validado em O(tasks + arestas); snapshot e histórico completos são reescritos sob lock e fsync. Essa opção simplifica recuperação, mas serializa mutações e cresce com histórico; não foi dimensionada para filas de alto volume. O paralelismo útil está no trabalho independente do host, não em writers simultâneos do JSON.

Reservas cobrem arquivos/diretórios normalizados, symlinks, ancestralidade e nomes de recursos compartilhados. Só coordenam participantes do mesmo estado. O host continua responsável por respeitar ownership, isolar bancos/portas e limitar ferramentas executadas fora do protocolo. Nenhuma garantia de coordenação entre hosts ou stores distintos é declarada.

Falha pré-rename preserva estado anterior; pós-rename exige consultar operation_id. JSON corrompido falha fechado. Cancelamento não significa rollback nem parada de processo remota. Budget usa medição conhecida para admitir nova execução; não limita custo de chamada já em andamento e não garante teto financeiro.

## Entrega e integração

Entradas: [workflow](../skills/nexus/references/workflow.md), [contrato do estado/CLI](../skills/nexus/references/workflow-state.md), [executor](../skills/nexus/scripts/workflow.py). README e SKILL.md recebem apenas roteamento e descrição da capacidade nova. As outras referências e templates permanecem preservadas.

O host atual fornece colaboração por ferramentas; não foi encontrada ferramenta nativa de Todo neste ambiente. Todas as mutações listadas no contrato funcionam por CLI, com leitura atualizada em Markdown/JSON. A CLI não possui botões/TUI, não publica dashboard e não sincroniza automaticamente com checklist ou Todo externo.

Critérios e resultados de aceitação estão em [validação](workflow-validation.md). Documentos da fase 1 são históricos e não representam prova da capacidade nova. Testes locais não comprovam comportamento em providers ou filesystems não exercitados.
