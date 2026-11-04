# Consistência de versões dos plugins — 2026-11-04

## Falha reproduzida

Os manifestos de desenvolvimento de Claude Code e Codex declaravam `0.3.1`,
enquanto o pacote distribuído declarava `0.3.12`. Registrar o marketplace pela
branch padrão instalava o código-fonte com a versão inicial. As tags-fonte
`vX.Y.Z` também preservam esses metadados, pois apontam para o SHA validado.

Dois testes novos falharam antes da implementação: ausência de uma referência
imutável com manifestos de release e ausência de materialização dos catálogos
remotos como catálogos locais no pacote distribuído.

## Contrato corrigido

- Os catálogos de origem de ambos os hosts encaminham para `plugins`.
- O pacote distribuído tem catálogos locais, versões iguais à release e
  `.nexus-release.json` com a tag-fonte e o SHA validado.
- `plugin-vX.Y.Z` fixa a árvore do pacote. A tag-fonte continua intacta.
- Tags existentes são conferidas pela árvore completa, incluindo proveniência.
  Conflitos interrompem a publicação; tags nunca são movidas.
- A recuperação de uma tag ausente ocorre mesmo quando o canal já avançou,
  sem rollback. Respostas de escrita incertas não são repetidas automaticamente.
- Catálogos locais históricos mantêm seus bytes e hashes originais.
- A validação de um checkout usa uma cópia local explícita preparada por
  `scripts/verify_hosts.py`, sem instalar acidentalmente a release remota.

## Verificação nativa

```sh
NEXUS_HOST_UPDATES=1 python3 -m unittest tests.test_release.NativeHostUpdatesTests -v
```

Claude Code `2.1.308` e Codex CLI `0.166.0-alpha.5.1`, com o executável Codex
distribuído no ChatGPT para macOS, passaram pelos seguintes cenários:

1. Adicionar a origem Git sem escolher `plugins` instala o pacote publicado.
2. Publicar B e atualizar o catálogo/plugin troca `0.3.0` por `0.3.1`, apesar
   de os manifestos de origem continuarem em `0.3.0`.
3. Instalar `plugin-v0.3.0` depois de B retorna `0.3.0`; atualizar o catálogo
   e o plugin mantém essa versão.
4. Voltar ao canal `plugins` instala `0.3.1` nos dois hosts.
5. A versão, proveniência e todos os arquivos das skills do pacote carregado
   correspondem ao snapshot Git da release escolhida, com conteúdo diferente
   entre A e B. As seis skills são descobertas e habilitadas.
6. O sentinela em `.nexus/local/` do consumidor permanece idêntico.

Perfis vazios, repositórios Git e uma regra `insteadOf` temporários permitem
exercitar clone/fetch/ref e instalação reais sem credenciais ou rede. Os testes
não executam inferência nem alteram o perfil habitual do usuário. O wrapper npm
global `codex` deste computador estava com seu binário ausente; o teste usou o
executável do aplicativo, sem modificar a instalação global.

## Falhas e custo operacional

Os testes Git/API cobrem recuperação de tag ausente, resposta perdida após
criação, tag conflitante, reexecução antiga, preservação dos catálogos históricos
e os cenários preexistentes de concorrência e promoção interrompida.

Registrar diretamente `plugins` continua sendo o caminho recomendado. O fallback
de `main` acrescenta a resolução de uma origem Git durante a instalação; não
acrescenta processos ou chamadas à execução das skills. A publicação adiciona
leitura/criação da tag e um commit derivado por versão, mantendo promoção serial
sem force. Não há medição de latência/throughput em produção.

Nenhuma release ou tag remota foi publicada pelos testes. A criação efetiva de
`plugin-v*` pelo `GITHUB_TOKEN` e sua aceitação pelos rulesets dependem do primeiro
workflow após o merge. Workflows históricos executam scripts históricos; não há
backfill em massa das tags de pacote.

## Resultado final

Passaram **236 testes do projeto**, incluindo o lifecycle nativo opt-in, e
**56 testes do runtime**, além de `scripts/validate.py`, validação dos **26 hooks**
e `git diff --check`. A verificação independente do checkout com
`scripts/verify_hosts.py` também retornou `pass` para Claude e Codex.
A revisão independente do diff não encontrou achados bloqueantes.

O runtime exigiu acesso a loopback para seus servidores HTTP de teste. A suíte
em Python 3.14 emitiu os `ResourceWarning` preexistentes de conexões SQLite.
Execuções anteriores tiveram um timeout de 0,5 s em
`test_byte_limit_prevents_unterminated_output_flood` sob execução concorrente e
uma falha de limpeza em
`test_complete_generated_package_passes_validation_and_preserves_skill_bytes`,
com arquivos `.git/info` recriados após as verificações. Ambos passaram
isoladamente e na sequência completa final. As fixtures Git de release agora
desabilitam manutenção automática para reduzir interferência na limpeza.
