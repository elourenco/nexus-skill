# Validação de atualizações dos plugins — 2026-11-03

O contrato abaixo registra a entrega original. A correção posterior de instalação
por `main` e de versões fixadas está em
[consistência de versões](plugin-version-consistency-validation.md).

## Contrato entregue

Uma release estável é publicada no SHA de origem validado. A branch derivada
`plugins` recebe a mesma árvore, alterando somente as versões dos dois manifestos
e adicionando `.nexus-release.json` com tag/SHA. O marketplace clonado dessa
branch distribui versões detectáveis sem depender de um checkout pessoal.

## Cenários automatizados

`tests/test_release.py` usa repositórios Git temporários reais e uma API GitHub
simulada. As árvores, commits e refs de distribuição são materializados no Git;
um cenário separa tags remotas das tags presentes no checkout local.
Os testes verificam igualdade da árvore distribuída, versões dos dois hosts,
proveniência, falha após publicação da release, resposta perdida após promoção,
reexecução antiga após versão nova, branch sem proveniência, conteúdo divergente,
avanço concorrente, predecessora com distribuição incompleta e drift de versões
nos manifestos de origem. Mantêm os cenários anteriores de ordem e recuperação.

Sete testes novos falharam contra a implementação anterior antes da correção:
distribuição ausente, falta de recuperação/isolamento e drift não rejeitado.
As verificações de concorrência e conteúdo divergente foram acrescentadas em
seguida, sem sobrescrever a branch alterada por outro writer.

O snapshot completo gerado é extraído em outra pasta, passa pela validação do
pacote e mantém todos os bytes das skills. O teste não exige a tag nova no
checkout: a criação de tag pela API não a baixa para o runner. Esse cenário
reproduziu um achado da revisão independente e passou após a verificação da tag
ser movida para a API remota. Tags anotadas também são resolvidas até o commit.

## Hosts nativos

Teste opt-in reproduzível:

```sh
NEXUS_HOST_UPDATES=1 python3 -m unittest discover -s tests -p test_release.py -k remote_branch -v
```

O executável Codex pode ser escolhido por `NEXUS_CODEX`. O teste usa o binário
do ChatGPT no macOS por padrão; CI normal não exige instalação dos hosts.

Resultado observado: Claude Code e Codex instalaram `0.3.0` de uma origem Git na
branch `plugins` e receberam `0.3.1` após uma nova promoção. O teste usa os
comandos documentados, consulta a versão instalada no Claude e lê os manifestos
do pacote efetivamente descoberto pelo app-server Codex. As seis entradas do
Codex apontam para `0.3.1` e estão habilitadas. Um arquivo sentinela em
`.nexus/local/` do consumidor permaneceu idêntico.

Versões observadas: Claude Code `2.1.308` e Codex CLI
`0.166.0-alpha.5.1`, em macOS/Python `3.14.6`.

Cada host usa um perfil temporário vazio. Uma regra Git `insteadOf` isolada
redireciona uma URL HTTPS sintética para um repositório local: os hosts exercitam
parse da origem/ref, clone, fetch e substituição do pacote sem rede. Nenhuma
credencial foi copiada, nenhuma inferência foi executada e nenhuma configuração
global foi alterada.

O teste também expôs que `claude plugin update` sozinho, imediatamente após uma
release, preservou `0.3.0` com catálogo ainda antigo. A sequência explícita
`plugin marketplace update nexus-local` seguida de `plugin update` recebeu
`0.3.1`; o guia foi corrigido. O agendamento de auto-update em segundo plano não
é validado por esse teste.

A fixture nativa fixa os manifestos em `0.3.0` antes da primeira instalação,
independentemente da versão de desenvolvimento. A integração sobre a base que já
declara `0.3.1` reproduziu a dependência incorreta e confirmou a correção sem
alterar os manifestos reais do pacote.

## Limites e ativação

Validação final na árvore isolada do PR, baseada em `bb99463`: **217 testes
do projeto** (com o lifecycle nativo opt-in) e **56 testes do runtime** passaram. `python3 scripts/validate.py`, validação dos
26 hooks e `git diff --check` também passaram. O runtime precisou de autorização
para abrir seus servidores HTTP de teste em loopback. A suíte em Python 3.14
emitiu `ResourceWarning` de conexões SQLite, sem falhas.

- O wrapper `codex` global deste computador falhou com `ENOENT` no binário npm.
  O teste usou `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`.
  A instalação npm global não foi modificada.
- Nenhuma tag, release ou branch remota foi publicada por estes testes. O primeiro
  run real precisa confirmar permissões do `GITHUB_TOKEN`, rulesets e descoberta
  da branch remota. Essas permissões não são demonstradas pela API simulada.
- O Claude exige opt-in por marketplace para auto-update. No Codex, o teste cobre
  refresh explícito; não afirma polling automático.
- Instalações locais existentes precisam migrar a origem uma vez. Mudanças no
  README não reconfiguram os perfis já instalados.
- Estado e migrações de dados do consumidor não fazem parte da atualização do
  pacote. O teste preserva um sentinela; não demonstra migração de esquemas.
- Não há medições de latência/throughput em produção. A publicação é serial e a
  visibilidade do pacote depende de uma única promoção de ref sem force.
- `actionlint` não está instalado neste ambiente; não foi registrada validação
  por esse linter. A estrutura preexistente do workflow é mantida, com alteração
  do nome da etapa e exclusão da branch gerada no CI de desenvolvimento.
