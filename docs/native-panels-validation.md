# Validação de spec e plano em painel nativo

Data: 2026-11-05. Escopo: apresentação documental no pacote portátil NEXUS.
Sem adapter, HTML, dependência, serviço, mudança de helper ou instalação global.

## Mudança e critérios

O contrato de chat agora descreve abertura do mesmo Markdown nos recursos nativos
permitidos da sessão. Brainstorming e Plan apontam diretamente para esse contrato.
Os templates agrupam a SPEC por assunto e o PLAN por entregas numeradas,
preservando seus campos anteriores e as relações com a fonte adotada.

Critérios: selecionar capacidade real; respeitar modo/permissões; conservar o
arquivo de plano nativo; manter resumo e links no chat; tratar erro e abertura
enfileirada sem falso sucesso; preservar edição do usuário, revisão e aceites.
Pergunta conceitual e plano curto continuam admitindo resposta direta.

## Método e baseline

Um consumidor somente leitura, em contexto novo, leu invocação, brainstorming,
plan, chat e os dois templates antes das alterações. Aplicou seis cenários
sintéticos. Nenhuma ferramenta fictícia foi executada.

O contrato genérico anterior já levou o consumidor a escolher abertura nativa
no Codex, revisão de plano no Claude Code VS Code e fallback quando o preview
não podia ser acionado. Também criou Markdown quando a revisão de dois artefatos
tornava a persistência útil. Esses casos não demonstraram falha e foram mantidos
como cenários de preservação.

A lacuna observada foi a forma do documento: no cenário de preenchimento, a
SPEC ficou como título seguido de uma lista de campos, sem subtítulos; o PLAN
agrupava campos gerais e decisões, sem uma seção de entregas numeradas. O
incremento acrescenta essa estrutura e explicita a seleção por superfície.

## Avaliação após a edição

Outro consumidor, sem herdar a conversa do implementador, leu os mesmos pontos
de entrada e aplicou os cenários abaixo. São aplicações textuais por um único
consumidor, não amostras estatisticamente independentes nem smoke tests de hosts.

| Caso sintético | Resultado observado |
| --- | --- |
| Codex com SPEC/PLAN existentes e abertura permitida | Escolheu duas aberturas de arquivo por caminho absoluto à direita, com resumo, links e revisão; distinguiu validação proposta de executada. |
| Claude Code VS Code com Plan já ativo e sem comando de preview exposto | Preservou revisão/arquivo nativos de PLAN; ofereceu link da SPEC e instrução manual de preview, sem inventar ferramenta. |
| Terminal, somente exploração conceitual | Respondeu à recomendação de conflitos diretamente, sem arquivo, painel ou execução. |
| Falha da abertura | Conservou documentos, links, estado e aprovação pendente, sem criar UI alternativa ou repetir em ciclo. |
| Revisão de dois artefatos ainda não salvos, workspace gravável | Escolheu Markdown no workspace consumidor e abertura nativa, sem inicializar TASKS ou helpers. |
| Preenchimento BALANCED | SPEC com seis seções temáticas; PLAN com resultado, entregas numeradas, validação/recuperação e referências pertinentes. |
| Edição do usuário com aprovação de revisão anterior e escopo alterado | Releu/reconciliou fontes, preservou edições e reapresentou a parte materialmente alterada. |
| Modo permite salvar apenas PLAN nativo | Manteve PLAN autorizado e SPEC na conversa, explicitando ausência de arquivo/persistência, sem contornar permissões. |
| Abertura retorna `queued` | Informou solicitação pendente e manteve links, sem anunciar abertura nem reenviar a solicitação. |

## Verificações e revisão

- `python3 scripts/validate.py`: aprovado; metadados, links locais e pacote.
- `python3 -m unittest discover -s tests -v`: 239 testes, resultado OK com um
  skip, antes e depois das alterações. Inclui empacotamento Claude e relocação.
- Comparação com os templates anteriores: preservados os 17 campos de SPEC e
  os 15 campos de PLAN; nenhum campo anterior removido.
- `git diff --check`: aprovado.
- Review independente, somente leitura, contra snapshot anterior às edições:
  nenhum achado acionável; conferiu pontos de entrada, identidade/fonte,
  permissões, aceites, campos e resposta de abertura enfileirada.

Não foram adicionados testes que apenas procurem frases nas instruções; a suite
existente verifica estrutura/portabilidade, enquanto os cenários acima avaliam
aplicação textual limitada. Helpers e runtime não foram alterados.

## Observação real e limites

Nesta sessão, duas chamadas reais de `open_in_codex` solicitaram abrir os templates
de SPEC e PLAN do workspace no painel à direita. Ambas retornaram `queued`.
Isso comprova solicitações aceitas para enfileiramento, sem confirmar painel
aberto ou fidelidade de renderização. A inspeção visual automatizada do próprio
Codex não estava permitida pelo runtime; não houve tentativa de contornar o limite.

Claude Code não foi executado. A orientação para revisão nativa e preview manual
foi conferida nas documentações de [Claude Code no VS Code](https://code.claude.com/docs/en/vs-code)
e [Markdown no VS Code](https://code.visualstudio.com/docs/languages/markdown),
consultadas nesta data. Disponibilidade continua condicionada à sessão real.

Não há medição de desempenho nem evidência de sincronização entre hosts. O
contrato evita reabrir documentos a cada atualização e mantém uma única fonte,
sem novo polling ou inferência para renderização. A validação visual no Codex e
o smoke test no Claude Code permanecem pendentes. Essas observações foram feitas
no checkout de desenvolvimento.


## Validação da árvore do PR

O incremento foi aplicado isoladamente sobre `origin/main` em `805bf94`,
conservando as orientações de navegação seletiva já presentes nessa base. Somente
os sete arquivos desta entrega foram incluídos; o checkout compartilhado foi
preservado.

- `python3 scripts/validate.py`: aprovado.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`:
  242 testes, resultado OK com um skip, na execução autorizada fora do sandbox.
- `git diff --check`: aprovado.
- Os templates e o contrato de painel coincidem com os arquivos revisados;
  Brainstorming e Plan receberam somente as adições desta tarefa sobre a base atual.

A primeira execução dessa suite no sandbox apresentou um erro em
`test_crash_requires_reconciliation_not_replay`: `PermissionError` ao consultar
um grupo de subprocessos com `os.killpg(child, 0)`. A repetição completa fora do
sandbox passou, sem mudança em código ou testes. O resultado verde não comprova
renderização visual nem elimina os limites de host registrados acima.
