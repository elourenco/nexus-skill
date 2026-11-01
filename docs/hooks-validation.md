# Evidências — executor local de Hooks

Escopo autorizado em 2026-10-31: executor Python local e testes, mantendo integrações nativas desativadas. Nenhuma instalação global, commit, push ou deploy nesta entrega.

## Auditoria

- Base: eventos documentados, sem runtime NEXUS anterior; nove IDs preservados.
- Validador existente preservado em `scripts/validate.py`.
- Host: oito registros, sem duplicatas exatas, referências locais existentes. Isso não comprova execução; nenhum handler global foi disparado na auditoria.
- Dependências externas novas: nenhuma. Usa Python padrão, SQLite local e processos POSIX.

## Cenários executados

A suíte usa subprocessos, arquivos e bancos temporários reais; não acessa bancos de projetos consumidores.

| Cenário | Resultado exigido |
| --- | --- |
| Comando autorizado / saída sensível sintética | Execução real; stdout/stderr fora de resposta/journal |
| Permissão ausente ou concedida via payload | Comando não executado |
| Evento duplicado / ID conflitante | Sem efeito repetido / rejeição explícita |
| Dois processos no mesmo workspace | Um claim; IN_PROGRESS ou WORKSPACE_BUSY para o outro |
| Mesmo ID em workspaces diferentes | Estado e resultados isolados |
| Timeout / erro de validação | Tentativas limitadas / sem retry indevido |
| SIGTERM / SIGKILL | Limpeza quando possível / claim preservado |
| Filho vivo após crash | Recuperação recusada até reconciliação |
| Mutação seguida de falha | Efeito incerto bloqueia próximos eventos |
| Cache / conclusão após edição | Evidência obsoleta rejeitada |
| Versão de memória desatualizada | Conflito preserva registro; atualização explícita substitui |
| FAST / recomendação profunda | Seleção proporcional e orçamento limitado |
| OBSERVE/ADVISE configurado como comando | Registro rejeitado |
| JSON malformado / caminho externo ou NUL | Erro estruturado |
| Circuito / recursão | Suspensão e chamada recursiva rejeitada |

## Resultados

Validação em 2026-10-31, Python 3.14.6 no host macOS:

- `python3 -m unittest discover -s tests -v`: **33 testes aprovados**, 6,533 s na execução final completa. Esse tempo é de suíte local, não benchmark de latência/throughput do produto.
- `python3 skills/nexus/scripts/hook_engine.py validate`: **26 hooks / 19 eventos**, registro válido.
- `python3 scripts/validate.py`: metadados da skill e destinos Markdown locais válidos.
- `git diff --check`: sem erros nos arquivos rastreados.
- Smoke com banco temporário, registro padrão e 24 arquivos do próprio repositório: `code.post_edit` executou o validador real; replay retornou resultado armazenado; `task.completed` aprovou `completion.verify` usando esse recibo. Todos exit 0, sem instalação de hooks.
- Revisão independente Sol/high identificou quatro problemas: replay de memória com schema diferente, negação de permissão zerando circuito, caminho NUL com traceback e cache obsoleto após mutação no mesmo evento. As regressões falharam antes das correções e passaram depois; o reviewer confirmou o encerramento do último achado com a regressão específica.
- Também foram testados e corrigidos descarte de conteúdo de memória em timeout e alterações esperadas de arquivos por comandos EXECUTE.

Uma rodada intermediária recebeu `PermissionError` em `killpg(pid, 0)` no teste de filho órfão. A causa no host não foi determinada; a repetição isolada e a suíte final completa passaram. Os testes de processo dependem das permissões POSIX; esse resultado não valida outros hosts, Windows ou todas as versões Python desde 3.10.

Não há evidência de integração nativa ou benchmark de produção. ADVISE produz orientação, não revisão por modelo. Completion verifica comandos obrigatórios e escopo declarado; `read_only` é contrato do operador, não isolamento de código. Coordenação requer o mesmo banco local, sem garantia de exactly-once externo ou retenção automática.

## Correções de review — PR #7

Dois defeitos foram reproduzidos antes da correção, com processos e SQLite reais:

- Remover execução de um script declarado (`0700 → 0600`), sem alterar conteúdo, reutilizava cache aprovado e permitia conclusão com recibo antigo. As duas regressões retornaram exit 0 quando deveriam bloquear. O snapshot agora inclui os três bits executáveis, obtidos com `fstat` do mesmo descritor usado para ler o conteúdo; cache e evidência passam a invalidar a alteração. Recibos e cache com o formato anterior também deixam de corresponder ao novo snapshot: é necessário validar novamente o escopo, sem migração de resultados antigos.
- JSON com surrogate isolado (`\ud800` ou `\udfff`) em `memory.content` ou `memory.source` chegava ao SQLite: retornava `OPERATIONAL_FAILURE`, deixava claim `running` e o próximo evento válido recebia `WORKSPACE_BUSY`. Strings de memória e listas de strings agora exigem UTF-8 válido na validação anterior à abertura do estado e ao claim. As regressões cobrem ambos os campos, surrogates alto/baixo, caminho inválido e execução do próximo evento válido, preservando Unicode válido, inclusive caracteres fora do BMP.

A mudança acrescenta uma leitura de metadados por arquivo declarado e codificação UTF-8 dos campos limitados pelo contrato. Não altera coordenação de claims, número de subprocessos nem retries; não foi realizado benchmark. Continua sem isolamento contra alterações externas concorrentes ou garantia de detectar uma alteração transitória revertida entre snapshots.

Validação final das correções em 2026-10-31:

- `python3 -m unittest discover -s tests -v`: **37 testes aprovados**, 7,847 s. Os quatro testes adicionados falharam antes das correções e passaram depois; o cenário de memória inclui quatro combinações de campo/surrogate.
- `python3 skills/nexus/scripts/hook_engine.py validate`: **26 hooks / 19 eventos**, registro válido.
- `python3 scripts/validate.py`: metadados e links locais válidos.
- `git diff --check`: sem erros.

Resultados limitados ao executor local no host POSIX atual; não validam integração nativa nem benchmarks de produção.

## Integração com main

README preserva memória JSON, runtime textual e workflow. Os contratos de memória e hooks explicitam stores isolados, ausência de sincronização e a rota JSON para memória reutilizável. Avaliação documental: um registro JSON não aparece em `memory.retrieve` SQLite; resposta vazia não apaga nem invalida a fonte JSON; o workflow não dispara hooks automaticamente. A CI valida o registro de hooks e descobre toda a suíte local.

Validação da integração: `python3 -m unittest discover -s tests -v` passou com 105 testes em macOS/POSIX. A primeira execução no sandbox falhou na inspeção de grupo de processos (`os.killpg`, EPERM); a execução com permissão para essa inspeção passou. Não foi mascarado o erro nem removido o teste. Validador estrutural e registro de 26 hooks/19 eventos também passaram.
