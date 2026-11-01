# Agentes e Review Council — desenho e plano

Escopo ampliado pelo usuário em 2026-10-31: runtime CLI de planejamento/review por API; implementação delegada ao host. Este incremento não instala agentes nem modifica configurações globais.

## Auditoria e decisão

A base contém quatro papéis documentais (Planner, Architect, Implementer, Reviewer), seis pilares e um validador de Markdown. Não há runtime, adapter ou registro executável prévio. Os nove perfis locais de arquitetura, planejamento, implementação, testes, review, diagnóstico, trabalho mecânico, aprofundamento e análise crítica são úteis: os últimos quatro são especializações/níveis de trabalho, não novos processos obrigatórios. Nenhum será removido ou copiado para o pacote portátil.

O host expõe delegação nativa, mas não há bridge Python para ela. Não foram encontrados providers adicionais declarados na configuração local nem chaves OpenAI/Anthropic nas variáveis do processo. A CLI Codex falha ao localizar seu binário; a CLI Claude responde ao help, sem comprovar autenticação. Presença de executável ou assinatura não comprova acesso por API. Estes fatos são uma observação local, não requisitos de instalação.

Decisão: Python 3.10+, biblioteca padrão, configuração JSON explícita e adapters textuais para Responses e Messages. Sem daemon, banco, ferramentas remotas, execução de shell ou escrita em projetos consumidores. A skill continua utilizável sem o runtime. Implementer, Tester e Memory Curator fornecem propostas/handoffs, sem declarar execução ou persistência.

## Contratos e comportamento

- Provider define transporte, destino e disponibilidade local; Model define identificador configurado, capacidades declaradas, contexto e dados opcionais de custo/latência/sucesso; Agent define papel, ferramentas, entradas e saída.
- Router filtra capacidades, privacidade, disponibilidade, contexto e limites antes de ordenar por Economy, Balanced ou Quality. Não depende de nomes comerciais de modelos. Telemetria ausente permanece desconhecida; ranking configurável resolve empates.
- Orchestrator controla chamadas, prazo, reserva de consumo estimado e uma única escalada de capacidade por execução completa. Falhas de credencial, transporte, quota ou ambiente não justificam escalada. Timeout após envio é resultado incerto; não há retry automático.
- Council recebe contexto explícito e artefato identificado por hash; seleciona pilares pelo risco e arquivos, valida saída/evidência, consolida duplicações conservadoramente e decide APPROVED, CHANGES_REQUESTED, BLOCKED ou INCONCLUSIVE. Texto do modelo nunca autoriza execução.
- FAST agrupa verificações em uma revisão; BALANCED separa pilares aplicáveis; DEEP exige chamadas independentes para os pilares selecionados. Independência de contexto não equivale a diversidade de modelos/providers.
- Somente reviews textuais independentes executam em paralelo, com limite global e por provider; `max_parallel=1` oferece fallback sequencial. Um único provider é suficiente. Nenhuma execução paralela de escritores é oferecida.
- Limites de chamadas, concorrência, bytes de contexto e saída solicitada são explícitos. Tokens e custo pré-dispatch são estimativas; não garantem teto financeiro remoto. Reserva concorrente é atômica e consumo incerto não libera saldo como se fosse zero.
- Endpoints oficiais são padrão dos adapters; destinos alternativos exigem configuração explícita. APIs locais/compatíveis precisam passar testes de compatibilidade próprios. Não declarar suporte a providers adicionais somente por aceitarem uma URL.

## Fontes de integração

- [OpenAI Responses](https://developers.openai.com/api/reference/resources/responses/methods/create): request textual, status, output e usage; `store=false` sem prometer ausência de toda retenção pelo serviço.
- [Anthropic Messages](https://platform.claude.com/docs/en/api/messages): request textual, versão explícita, stop reason e usage.

Documentação consultada em 2026-10-31. Testes com transporte controlado validarão serialização e tratamento local; chamadas autenticadas reais permanecem pendentes.

## Plano de implementação

- [x] Contratos/configuração e registry: validar configurações antes de I/O, distinguir papel de modelo e explicitar handoffs ao host.
- [x] Router/orchestrator: testar primeiro providers ausentes, privacidade, budget concorrente, uma escalada global, prazo e timeout incerto; implementar seleção e execução limitadas.
- [x] Adapters: testar requests/responses, erros, truncamento, recusa e métricas ausentes; implementar somente transporte textual verificado na documentação.
- [x] Council/CLI: testar seleção de pilares, saída inválida, referências falsas, duplicações, pilar ausente e fallback sequencial; integrar comandos de inspeção, roteamento, execução e review.
- [x] Documentação e verificação: atualizar esta frente e entrada do repositório proporcionalmente ao escopo ampliado; executar unittest, CLI e `python3 scripts/validate.py`; review independente sobre diff e contratos.

## Aceite e limites

Todos os dez critérios do pedido serão associados a cenários em `runtime/tests/`. Uso com dados sintéticos e testes de contrato não comprova qualidade de inferência, disponibilidade autenticada, throughput ou custos reais. O resultado final deve distinguir código funcional localmente, fallback e integração futura. Sem commit, push, merge, deploy ou instalação global.

Implementação e resultados: [runtime](../runtime/README.md) e [validação](../runtime/validation.md). O teste de integração percorre a CLI e ambos os protocolos em loopback; autenticação externa permanece pendente.
