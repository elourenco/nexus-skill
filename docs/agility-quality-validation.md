# Agilidade e qualidade — validação de 2026-11-08

## Escopo e base

Implementação da proposta aprovada nesta conversa. Base versionada local:
`4d272744bcb7a063a81ceee7ea4c0e8904ea77b4` (`origin/main` observado), branch
`elourenco/nexus-agility-quality`, em worktree própria. Durante a implementação e avaliação, anteriores à
publicação do PR, não houve fetch, commit, push ou publicação. O checkout original foi preservado: 177 arquivos rastreados
ou não ignorados conferidos por SHA-256 antes/depois. Arquivos ignorados não entram
nessa cobertura. Nenhum arquivo desse checkout foi editado por esta implementação.

A base já possui navegação seletiva e Plan com Workflow condicional. Preservamos
essas regras e reduzimos o gatilho ainda amplo no Build/invocação/rotas. O estado
local sujo analisado anteriormente não foi copiado para a nova branch.

## Alteração implementada

- Build/invocação/rotas: Workflow para dependências, ownership, estado ou recuperação
  ainda indefinidos; uma sequência de passos suficiente não dispara outro procedimento.
- Build/Agents: o destinatário resolve o contrato nas fontes e segue a próxima ação
  autorizada; lacuna material bloqueia apenas sua dependência, sem nova fase de readiness.
- Review: reconstrução seletiva do comportamento/invariante e contraexemplo; interpretação
  divergente deve ser conferida antes de atribuir defeito à SPEC.
- Review: divergência normativa avaliada na fronteira afetada, distinguindo requisito
  vigente, mudança aprovada e proposta ainda não implementada.
- Agents: qualificação de independência reutilizável enquanto válida, mantendo evidência
  da execução individual, instruções do host e limites de isolamento explícitos.
- Build: checks/review podem compartilhar versão identificada com recursos isolados;
  edição posterior invalida cobertura afetada; review de design não cobre código final.

FAST/BALANCED/DEEP, review independente obrigatório em DEEP, autoridade, orçamento,
limites de tentativas, evidência válida e gates de conclusão permanecem vigentes.
Não foram alterados runtime, helpers, políticas de testes ou gates do CI.

## Protocolo e reprodução

A [suíte](../evals/agility-quality-suite.json) contém pedidos, rubricas e arquivos
iniciais sintéticos em `fixture_files`. Materialize esses arquivos em um diretório
privado novo por cenário/condição, mantendo o mesmo conteúdo em ambas. Use a entrada
indicada da distribuição congelada; permita somente os efeitos do pedido e um
`response.md` de avaliação. Não exponha rubricas nem outras células ao executor.

Rodamos seis agentes nativos `tests`, com `fork_turns=none`: uma amostra por cenário
e condição, até dois consumidores independentes em paralelo, cada qual com seu
próprio diretório. Sol/medium foi solicitado pela política do host; modelo/esforço
efetivos não foram atestados. Todos os previous rodaram antes da edição; depois os
candidate. Snapshots das skills foram identificados por inventário SHA-256 e
reconferidos sem mudanças. Não é uma avaliação cega, randomizada ou estatística.

Desvios: previous/drift recebeu um lembrete adicional do coordenador para encerrar
quando a evidência da fronteira fosse suficiente. O harness existente foi preparado
após as execuções para identificar snapshots; seus diretórios/ordem planejada não
são os consumidores/ordem efetivamente usados. Não se atribui execução ao harness.

Os [resultados observados](../evals/results/agility-quality-2026-11-08.json) incluem
respostas dos agentes e rechecagens do coordenador. São dados sintéticos, sem
transcrições privadas de consumidores. Snapshots e artefatos brutos ficam no diretório
temporário local da execução; a suíte permite reconstruir as fixtures iniciais.
O commit base permite reconstruir previous; a candidata avaliada está no commit
`1908f4516e17edee289f11f268cdb42d6905e5f7`, anterior à atualização de base descrita abaixo.

## Resultados funcionais

| Cenário | Previous | Candidate | Evidência reproduzida pelo coordenador |
| --- | --- | --- | --- |
| Texto trivial | pass | pass | README final tem somente a substituição solicitada, comparação exata de bytes. |
| Contrato omitido no handoff | pass | pass | Teste real cobre applied/absent/unknown: consulta antes de envio, identidade estável, reenvio único somente em absent; documentos e testes preservados. |
| Drift normativo | pass | pass | Revisores identificam R1=2000 ms versus implementação/teste=10000 ms; suíte existente passa, asserção normativa independente falha; ausência de future_queue proposed não é defeito. |

As duas implementações de handoff foram reexecutadas com
`python3 -B -m unittest discover -v`: exit 0. Os agentes relataram teste inicial
vermelho por NotImplementedError e posterior verde; sem export nativo completo dos
rastros dos filhos, a sequência pré/pós e a lista de referências lidas são relatos
autorais. O resultado final e preservação foram conferidos diretamente. Os casos
de retry usam callbacks locais e não comprovam semântica de um provider real,
concorrência multiprocesso ou durabilidade após crash.

Os dois consumidores drift permaneceram idênticos à fixture (exceto response.md).
A suíte verde foi observada novamente; `assert timeout_ms() == 2000` falhou com
10000. Esse é um contraexemplo esperado do objeto avaliado, não uma falha da skill.

## Gates locais

- Baseline: `python3 scripts/validate.py` aprovado; 242 testes de `tests/`, um skip;
  56 testes de `runtime/tests/` aprovados após permitir bind HTTP em localhost.
- Candidata: `python3 scripts/package_claude.py` aprovado; validação estrutural/links
  aprovada; 242 testes de `tests/`, um skip; 56 testes de `runtime/tests/` aprovados;
  `hook_engine.py validate` com 26 hooks válidos; schema da nova suíte válido;
  `git diff --check` sem erros.
- O primeiro runtime no sandbox falhou com PermissionError ao abrir 127.0.0.1;
  nova execução autorizada fora desse bloqueio passou. Nenhum gate foi retirado.
- ResourceWarnings de conexões SQLite não fechadas ocorreram em baseline e candidata
  com Python 3.14. O skip opt-in `NEXUS_HOST_UPDATES=1` não foi convertido em sucesso executado.
- Review independente `final_quality_review` (Sol/high solicitado, contexto novo):
  APPROVED no escopo, sem achado acionável. Revisor leu diff/fontes e executou
  probes próprios sem gravação: seis resultados funcionais confirmados; os 177
  arquivos originais e os snapshots também foram reconferidos. A comprovação
  completa do processo permanece inconclusiva por ausência de traces integrais.

## Limites

Esta triagem encontrou os mesmos resultados funcionais nas duas condições. Não
houve falha comportamental da skill anterior nestes três casos; o vermelho do
handoff era da fixture incompleta, não uma reprovação do protocolo anterior.
A alteração é uma explicitação e ajuste de gatilhos, sem ganho causal demonstrado.

Sem rastros completos dos filhos, leituras/chamadas e ausência de toda cerimônia
ficam limitadas aos relatos e artefatos disponíveis. Contexto novo foi solicitado
na ferramenta; exclusão de instruções/memória do host não foi testada. Tokens,
latência comparável e throughput não foram medidos e permanecem desconhecidos.
Os resultados não comprovam equivalência geral, maior qualidade ou economia.
CI remoto, instalação e aceite em outros hosts não foram executados nesta tarefa.

A triagem não exercita gate DEEP indisponível, contrato realmente ausente, retomada
incerta ou invalidação concorrente de review. Esses contratos foram inspecionados
no diff; não se declara cobertura comportamental nova para tais caminhos.

## Atualização da base para publicação do PR

Após publicar o primeiro commit, o PR #33 apresentou conflito com a política Git
integrada em `main` no commit `1b28b5939c0b3784e8724b35d7f35ce733778cb6` (#32).
A branch foi atualizada por rebase, combinando em Build as regras de validade do
review com integração Git, e em Routes o gatilho restrito de Workflow com a rota
Git. As demais adições da política Git foram preservadas.

Os seis resultados comportamentais acima pertencem ao snapshot anterior à atualização
de base, identificado por `1908f451`. Não houve nova inferência dos três cenários
sobre o pacote integrado. A validação estrutural, os testes locais e a revisão da
resolução são registrados separadamente; não transferem automaticamente a cobertura
comportamental para o novo snapshot. O merge do PR permanece pendente.

No pacote integrado, passaram novamente: 242 testes (um skip opt-in), 56 testes
do runtime com fixtures HTTP locais, empacotamento Claude, validação estrutural,
26 hooks e diff --check. Review independente da resolução em `dd27ce0`: APPROVED,
sem achados acionáveis; preservação das duas mudanças conferida pelo diff.
