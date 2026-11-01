# Plano — memória local

Objetivo: entregar persistência local opt-in e recuperação seletiva, conforme ampliação de escopo autorizada nesta frente em 2026-10-31. O pacote continua sem executor de hooks, scheduler, serviços ou adapters de providers.

## Auditoria

Base: `5684e44`. A referência de memória e o template eram Markdown; nenhum registro de consumidor, índice ou integração de persistência foi encontrado no worktree. `context.load` e `memory.capture` são eventos lógicos; workflow exige conferir estado real na retomada e policies exige contexto delimitado. Não há dados a migrar nesta base. Regras de proveniência/revalidação se repetem entre referência e template; manter a referência como contrato e o template como entrada. A declaração de ausência de persistência no README precisará distinguir helper opt-in de runtime automático.

## Decisões

- Python 3.10+, biblioteca padrão, filesystem local POSIX. Um store por escopo explícito (`working:projeto/tarefa`, `project:projeto`, `shared:colecao`); nenhum diretório global implícito.
- JSON UTF-8 por revisão imutável; manifest vincula escopo; índice compacto é derivado. O maior número de revisão publicado é o estado corrente. Dados legados permanecem intactos e são importados individualmente por entrada normalizada com referência à origem.
- Lock cooperativo do sistema operacional, compartilhado na leitura e exclusivo na escrita, sem espera ilimitada; CAS por revisão esperada. Gravação temporária no mesmo diretório, fsync e rename; arquivos temporários não contam como revisões. Recuperar estado antes de repetir resultado incerto.
- Recuperação por metadados, IDs, entidades e tags, sem embeddings; pack JSON portátil com limite de caracteres e contagem medida. Tokens do provider indisponíveis são null. Revalidação semântica cabe ao agente nas fontes atuais.
- Rejeitar formatos reconhecíveis de credenciais antes de persistir. Scanner heurístico não substitui revisão/sanitização e política do host. Sem upload nem cópia entre stores automática.

## Incrementos e aceite

1. [x] Testes de contrato antes do helper: persistência em processos distintos, isolamento, recuperação, obsolescência, deduplicação, conflitos, legado e segredos.
2. [x] Helper em `skills/nexus/scripts/memory.py`: init, put, get, pack, reindex; falhas explícitas e histórico preservado. Testes de falhas de I/O na fronteira de publicação e recuperação após interrupção.
3. [x] Referência e template: lifecycle, working checkpoint, Context Pack, autorização, retenção e integração manual. Manter demais referências sob ownership de suas frentes.
4. [x] Validação estrutural, suíte completa e revisão independente do diff. Registrar comandos, resultados e limites em `docs/memory-validation.md`.

## Foco de revisão

Estado parcial de inicialização/gravação; índice ausente, inválido ou desatualizado; duas escritas da mesma revisão; caminhos/symlinks e escopo divergente; limites que omitem informação essencial; entradas legadas e segredo antes de qualquer arquivo temporário. Arquivos originais e revisões anteriores nunca são removidos pela importação ou expiração lógica.

Sem instalação global ou edição de outros worktrees. A integração final com os módulos de hooks/workflow/policies permanece explícita na referência de memória para evitar escritas concorrentes nessas frentes.
