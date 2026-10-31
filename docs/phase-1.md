# Fase 1 — Fundação

## Objetivo

Criar o repositório e a base editável do NEXUS, preservando espaço para ajustar o comportamento na fase 2. A unidade entregue é uma skill documental portátil, não uma plataforma de execução.

## Decisões iniciais de implementação

- Markdown para instruções e templates; nenhuma dependência de provider para ler o pacote.
- Uma entrada curta com referências carregadas conforme o modo e o risco.
- Testes adaptativos: TDD preferencial para invariantes críticas, regressão para bugs, validação proporcional para mudanças simples.
- Papéis separados de provider e modelo; a política do usuário e as capacidades reais do host determinam o roteamento.
- Artefatos de trabalho em `docs/nexus/` no projeto consumidor; informação privada e temporária em `.nexus/local/`, excluída do Git antes do uso.
- Paralelismo apenas com ownership e recursos independentes; fallback sequencial declarado.
- Repositório privado inicialmente; licença e distribuição pública pendentes.

## Critérios de aceite desta base

- [x] Entrada da skill, referências e templates navegáveis.
- [x] Limites explícitos entre instrução e automação implementada.
- [x] Validação estrutural local e workflow de CI configurado.
- [ ] Instalação e avaliação em projetos reais, por host (fase posterior).

## Fase 2 — Refinar com uso real

1. Calibrar modos, perguntas necessárias e limites de autonomia.
2. Aplicar cenários de edição simples, bug reproduzível e alteração de contrato; registrar tempo, retrabalho e consumo quando disponíveis.
3. Refinar seleção dos pilares de review e critérios de escalada.
4. Decidir o formato futuro: skill portátil, skill com runtime local, ou plataforma independente.
5. Escolher providers e contratos de adapters somente após verificar ferramentas e autenticação suportadas.
6. Definir licença antes de distribuição pública.

## Fases futuras — Dependem de decisão

Hooks executáveis, persistência transacional, filas, cancelamento, checkpoints, roteamento automático, medição de custos e todo/dashboard interativo. Um checklist Markdown organiza o trabalho nesta fase; não implementa o painel solicitado na visão do produto.
