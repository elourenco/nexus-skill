# Memória — evidências de 2026-10-31

## Escopo e auditoria

Base local `5684e44`, branch `nexus/memory`. A base possuía apenas a referência e o template Markdown de memória; não havia registros de consumidor nem índice. O usuário autorizou expandir esta frente para helper executável, template e testes. Originais de consumidores não foram consultados nem migrados; todos os ensaios usam dados sintéticos em diretórios temporários. Os ensaios não fazem instalação global nem chamadas a providers.

Antes da implementação, revisão independente aplicou quatro cenários: retomada com decisão obsoleta, concorrência/interrupção, legado/duplicação/credencial e handoff entre providers. Encontrou lacunas contratuais de seleção, versão/CAS, recuperação parcial e envelope portátil. A ausência dessas capacidades era um limite declarado da fase documental, não uma implementação defeituosa.

## Execução real

Comandos a partir deste worktree:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
git diff --check
```

- Verificação final para PR: 29 testes passaram em 4,099 s; `python3 scripts/validate.py` aprovou metadados/links locais; `git diff --check` não apontou erros.
- Suíte inicial: 11 testes falharam pela ausência do helper, antes de implementá-lo; os 11 passaram após a implementação.
- Suíte ampliada: 28 testes passaram, executando CLI em processos distintos, filesystem real e testes de falhas na fronteira de I/O. Revisão independente também executou os 28 testes (4,322 s naquela amostra).
- Regressões observadas durante review: limite final de pack excedido por crescimento das métricas; índice inconsistente ocultando fato active ou causando TypeError; scanner com custo quadrático; credencial fictícia embutida em JSON. As reproduções falharam antes das correções e passaram depois.
- Atualização idêntica conserva a revisão e os bytes do store; mudança de proveniência cria revisão. JSON com chaves duplicadas é rejeitado para não perder campos silenciosamente.
- Revisão final para PR: corrigida rejeição de data UTC sem horário, que antes causava AttributeError. A regressão cobre expires_at e observed_at sem persistência parcial. O workflow de CI passou a executar a suíte de memória.
- Validador adicional `skill-creator/scripts/quick_validate.py`: a primeira tentativa foi bloqueada por ausência de PyYAML. Na revisão final, PyYAML foi instalado somente em um venv temporário e a verificação retornou `Skill is valid!`; o helper e sua suíte continuam sem dependências externas.

## Cobertura

| Invariante | Evidência |
| --- | --- |
| Persistência entre sessões | `put` e `get` executados por subprocessos distintos; valores/autoria/timestamps e revisão preservados. |
| Isolamento | Scope CLI divergente e entrada de outro projeto rejeitados sem mutação. Raízes temporárias isoladas por teste. |
| Recuperação por tarefa | Query de metadados, IDs, entidades e tags; termo exclusivo do corpo não entra na busca; detalhes são opt-in. |
| Orçamento | Limite aplicado ao JSON completo, incluindo métricas e omissões; registros inteiros, sem truncar decisões. |
| Obsolescência | stale, superseded, expired e prazo vencido excluídos do pack; histórico continua consultável. |
| Deduplicação | Novo ID com mesmo fato rejeitado; no-op do mesmo ID não acumula revisões. Não é deduplicação semântica. |
| Concorrência | Dois processos com mesma revisão esperada: um vence; outro recebe busy/conflito; revisão anterior intacta. |
| Falha de publicação | `os.replace` falha antes da publicação: revisão anterior continua; temporário removido. |
| Resultado incerto | Falha injetada em fsync após publicação: nova revisão encontrada por get; reconciliação evita retry duplicado. |
| Índice derivado | Ausente, inválido ou desatualizado: reconstrução em memória; leitura não escreve; falha do índice após publicação não desfaz o registro. Digest/enums rejeitam metadados corrompidos. |
| Interrupção | Processo real segura flock, escreve `.pending-` e recebe SIGKILL; próximo processo progride e ignora temporário. |
| Corrupção da fonte | Última revisão inválida falha explicitamente; não retorna silenciosamente estado antigo. |
| Legado | Markdown permanece byte a byte; não há importação implícita; registro convertido referencia a origem. |
| Segredos | Conteúdo, resumo, proveniência, autor e JSON embutido com padrões reconhecíveis rejeitados antes de gravar, sem eco nos erros. |
| Caminhos | Symlink de registro/lock rejeitado; symlink de índice não é aberto nem sobrescreve alvo externo. |

Falhas de write/replace/fsync são injetadas por mocks no limite do SO; não são testes de queda real de energia. O teste de interrupção e os testes de escritores usam processos reais.

## Amostra de contexto e latência

macOS (Darwin), Python 3.14.6, filesystem temporário local. Corpus sintético com 100 registros, uma revisão por ID, summary `Fixture decision number N`, entidade `src/module-N.py` e conteúdo `Synthetic context. ` repetido 50 vezes; 138.760 caracteres nos JSONs, incluindo terminadores. Vinte consultas sequenciais por variante, índice válido, orçamento padrão de 6000 caracteres. Não inclui latência de provider, inicialização de subprocesso ou rede.

| Consulta | Metadados / corpos lidos / fornecidos | Caracteres fornecidos | p50 / máximo observado |
| --- | --- | --- | --- |
| Tarefa `Verify current choice`, entidade `src/module-42.py` | 100 / 1 / 1 | 786 | 4,740 / 5,092 ms |
| Tarefa ampla `Inspect module`, mesma entidade | 100 / 100 / 11 | 5.816; 89 registros omitidos | 19,832 / 20,099 ms |

Busca combina termos da tarefa/query com seletores por OR; a palavra `module` torna a segunda consulta ampla. O experimento evidencia o custo de consultas amplas, não uma economia universal. Contagem de tokens/custo de provider indisponível (`null`). Scanner de 32.768 caracteres simples concluiu em aproximadamente 0,001 s depois da correção, contra timeout de 3 s no teste anterior; medição pontual.

## Revisão comportamental final e limites

Os quatro cenários iniciais agora têm ações concretas: pack e revalidação antes da retomada; CAS/lock e leitura do ID após interrupção; conversão seletiva com origem preservada; envelope JSON portátil sem copiar conversa. Revisão independente não encontrou novos achados materiais após os fixes.

- Autoridade, atualidade semântica, suficiência do pack, autorização de persistência e envio para outro provider continuam verificações do agente/host.
- Scanner é heurístico; não garante detectar segredos desconhecidos, codificados ou ofuscados. Não gravação não equivale a remediação de segredos já presentes na entrada/histórico/Git.
- POSIX local e escritores cooperativos; sem Windows, NFS, sincronização distribuída, autenticação ou proteção contra proprietário malicioso do store. Compatibilidade Python 3.10+ é o contrato; a execução observada foi em 3.14.6.
- Substituição entre registros é composta por duas escritas. Git merges entre worktrees e duplicatas semânticas exigem reconciliação explícita.
- Expiração é lógica; sem purge automático, compactação física ou exclusão de backups. Summary incremental é produzido pelo agente.
- Índice verifica arquivos de revisão em O(n); escrita recompõe metadados. Consultas amplas podem ler todos os corpos candidatos antes de omitir os que não cabem.
- Integrações com hooks/workflows/agents/reviews/policies estão contratadas em memory.md; não há executor, adapter ou instalação automática. Outras referências não foram editadas por esta frente.
- Testes executados localmente; execução remota em CI e teste em projetos reais não foram realizados.
