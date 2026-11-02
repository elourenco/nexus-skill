# Receita de checks de qualidade do consumidor

Configure os comandos existentes do projeto como [hooks locais](hooks.md). NEXUS registra execução e valida recibos; não instala ferramentas de cobertura, mutation testing ou análise de complexidade, não escolhe thresholds universais e não infere qualidade sem medição.

## Fixture executável e limites

O [consumidor mínimo](consumer-guide.md) gera `checks.py`, testes e registry fora da instalação. Seus três comandos podem ser inspecionados e executados diretamente no consumidor:

```sh
python3 -B checks.py tests --min-tests 3
python3 -B checks.py complexity --max-branches 0
python3 -B checks.py mutation --min-killed 1
```

| Comando | Medição / requisito | Limite da conclusão |
| --- | --- | --- |
| `tests` | Executa unittest; mínimo de 3 testes; nenhum erro, falha ou skip | Quantidade de testes não mede cobertura nem relevância das assertions |
| `complexity` | Conta nós AST If/For/While/Try/IfExp em shipping.py; threshold 0 | É check estrutural específico do fixture, não complexidade ciclomática, cognitiva ou CRAP |
| `mutation` | Baseline passa; uma cópia temporária troca `>= 100` por `> 100`; pelo menos uma assertion falha, sem erro de importação | Um mutante conhecido não mede mutation score do projeto nem suficiência geral dos testes |

O mutation check copia somente `shipping.py`, `test_shipping.py` e `checks.py` para um diretório temporário exclusivo. Baseline e mutante rodam em processos separados com timeout de 2 s cada, sem bytecode. A fonte original não é alterada; a cópia é removida ao concluir ou lançar exceção tratada. Baseline quebrado, mutante sobrevivente e falha operacional não são contabilizados como mutante morto. O teste da receita enfraquece a assertion da fronteira e exige `killed: 0`/exit 1, além de verificar a fonte preservada. Não existe mecanismo genérico de geração ou seleção de mutantes no pacote.

O registry gerado usa `handler: command`, `execution_mode: ENFORCE`, `config.read_only: true`, sem cache e uma tentativa. `read_only` é declaração revisada do consumidor, não sandbox: o mutation check pode escrever apenas em sua cópia temporária. Cada comando requer permissão própria, concedida explicitamente com `--allow command:ID`.

`tests` sempre participa do evento test.completed. `complexity` exige flag `quality`; `mutation` exige flag `mutation`. O evento da demonstração inclui ambas. A task exige recibos dos três IDs: omitir uma flag não dispensa o check, e a importação rejeita hooks obrigatórios ausentes. Para mudar o conjunto exigido, revise registry e policy com autorização e invalide a geração pelo workflow. Alterar flags ou thresholds para aprovar uma falha é mudança de contrato, não evidência de correção.

## Configurar ferramentas reais

Escolha thresholds por invariantes, criticidade e baseline do consumidor. Faça a ferramenta real retornar exit code não zero quando a condição falhar; um relatório textual sem gate executável não bloqueia a entrega. O hook deve executar argv explícito, sem shell ou comandos oriundos do payload. Inclua scripts, configuração, testes e fontes relevantes no snapshot. Ferramentas/dependências externas também precisam de identidade de versão verificável; atualizar uma ferramenta fora do escopo não é detectado pelo hash de arquivos.

| Sinal | Contrato do comando do consumidor | Cuidado para decisão |
| --- | --- | --- |
| Cobertura | Ferramenta mede linhas/branches definidos; configuração determina arquivos e threshold; exit code aplica o limite | Publicar denominador e exclusões; cobertura alta não prova assertions úteis |
| Mutation testing | Baseline aprovado, seleção determinística, mutantes mortos/sobreviventes e timeout separados | Não tratar crash/timeout como assertion que matou mutante; limitar por escopo/custo |
| Complexidade | Ferramenta identifica métrica e versão; threshold explícito no código alterado | Não comparar métricas diferentes nem usar número como substituto de revisão |
| Duplicação / CRAP | Ferramenta existente, cálculo e exclusões documentados e gates do projeto | NEXUS não fornece cálculo próprio nem threshold global |

É possível substituir argv/flags dos hooks gerados pelos comandos reais de seu projeto; isso requer uma nova revisão do registry. A demonstração não é uma recomendação para usar contagem de nós AST como gate de produção. Seu propósito é comprovar que um threshold configurável gera aprovação/rejeição observáveis e que um mutante real depende de assertions executadas.

## Checks caros, latência e falhas

Cada hook aceita timeout máximo de 60 s por tentativa. FAST admite evento de até 10 s; BALANCED e DEEP, até 120 s. A admissão reserva o pior timeout/backoff antes de iniciar cada hook. Os tempos configurados no fixture são 2 s para tests, 2 s para complexity e 6 s para mutation; são limites, não medições de performance. Caso o ambiente seja lento, ajuste perfil e limites conscientemente. Não aumente retries para esconder falhas determinísticas.

Para mutation suites ou análises que excedam esses limites, execute a ferramenta no runner do próprio projeto e mantenha NEXUS fora da execução longa. **Não há importador nativo de recibos externos**. Se quiser aproveitar esse resultado em uma policy hook_receipts, o consumidor precisa implementar um comando local curto de verificação, também revisado e autorizado, que rejeite artefato ausente, inválido ou obsoleto. Seu contrato deve vincular workspace/task, workflow/run/generation atuais, hashes de todos os inputs, ferramenta/versão, thresholds, instante e resultado medido. O verificador não pode apenas ler um booleano passed. Artefato e verificador entram no snapshot; o journal recebe a execução desse verificador. Esta integração adicional não é implementada pelo fixture e precisa de testes de adulteração, obsolescência e falhas parciais antes de uso.

Separe recursos e artefatos por tentativa. Um timeout ou execução interrompida pode deixar resultado incerto; confira processos/efeitos antes de reconciliar ou repetir. Logs extensos e segredos não pertencem ao workflow: mantenha-os no mecanismo privado já adotado pelo projeto, com recibos locais mínimos. Os hooks descartam stdout/stderr dos comandos; seu report não deve depender de logs para decidir aprovação.

A [policy de recibos](workflow-state.md) relê registry, journal e snapshot em complete/deliver. Essa proteção detecta mudanças observáveis até a leitura final e rejeita checks anteriores ao run atual; não impede outro processo de editar arquivos depois. Preserve exclusividade no host até terminar a entrega.
