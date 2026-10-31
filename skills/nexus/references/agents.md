# Papéis e review por pilar

Use o agente principal para trabalho contínuo. Delegue quando houver ganho concreto de isolamento, revisão independente ou paralelismo, conforme suporte e regras do host. Os papéis abaixo são contratos de responsabilidade, não agentes instalados.

| Papel | Responsabilidade |
| --- | --- |
| Architect | Contratos, alternativas e trade-offs |
| Planner | Dependências, ownership e critérios de aceite |
| Implementer | Incremento e validação dentro dos arquivos atribuídos |
| Reviewer | Avaliação independente das fontes e do diff |

Cada delegação informa objetivo, fontes de verdade, arquivos permitidos, recursos isolados, contratos e aceite. Avise que há outros participantes e que alterações alheias devem ser preservadas. O controlador integra os resultados e resolve conflitos; não paralelize escritas sobre o mesmo recurso.

## Conselho de revisão

| Pilar | Quando selecionar | Foco |
| --- | --- | --- |
| Arquitetura | Mudança de fronteira ou contrato | Acoplamento, evolução e compatibilidade |
| Segurança | Alteração de superfície de ataque | Autorização, entradas, segredos e isolamento |
| Qualidade | Lógica ou manutenção relevante | Correção e testes observáveis |
| Performance | Caminho quente, volume ou recursos | Latência, throughput e contenção |
| Resiliência | Integrações ou estado concorrente | Falhas parciais, idempotência e recuperação |
| Produto | Fluxo ou comportamento perceptível | Aceite, estados de erro e usabilidade |

Ative apenas pilares pertinentes. Um revisor pode cobrir vários pilares em mudanças pequenas. Para risco material, use independência real quando disponível; se não houver, declare a limitação.

Entregue ao revisor o diff, fontes/contratos e critérios, sem induzir conclusões pela narrativa do implementador. Cada achado inclui severidade, arquivo/linha, condição de reprodução, impacto e correção sugerida. Consolide duplicações e verifique achados antes de alterar código. Ausência de achados não demonstra ausência de defeitos.
